#!/usr/bin/env python3
"""Supplement frozen reports with censored recoveries, inference and safety statistics."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import statistics

from vehicle_experiment_study import (METRICS, ROOT, digest, load_json, load_lines,
                                      loss_counts, metric_summary, verify_freeze, write_json)


def enrich(row):
    directory = Path(row['directory'])
    report = load_json(directory / 'report.json') or {}
    samples = load_lines(directory / 'samples.jsonl')
    begin = next((item['wall_s'] for item in samples if item['state'] == 'APPROACH'), None)
    end = next((item['wall_s'] for item in samples if begin is not None and item['wall_s'] > begin
                and item['state'] in ('RETURN', 'LAND', 'DONE')), None)
    associations = [item for item in load_lines(directory / 'association.jsonl')
                    if begin is not None and item['wall_s'] >= begin and (end is None or item['wall_s'] < end)]
    detector_times = [item['detector']['full_frame_s']+item['detector'].get('roi_s', 0.)
                      for item in associations if isinstance(item.get('detector', {}).get('full_frame_s'), (int, float))]
    confirmed_boxes = [candidate['bbox'] for item in associations for candidate in item.get('candidates', [])
                       if candidate.get('accepted')]
    border_boxes = [box for box in confirmed_boxes
                    if box[0] <= .5 or box[1] <= .5 or box[2] >= 959.5 or box[3] >= 539.5]
    events = report.get('events', [])
    schedule_panels = [{**panel, 'entry_locked': True} for panel in report.get('occlusions', [])]
    _, scheduled, outside, outside_recoveries = loss_counts(events, schedule_panels)
    unresolved = 0
    recovery_durations = []
    for index, event in enumerate(events):
        if event['event'] != 'TRACK_TARGET_LOST':
            continue
        terminal = next((item for item in events[index+1:] if item['event'] in (
            'TARGET_RECOVERED', 'TRACK_REACQUIRED', 'TRACK_TARGET_LOST', 'TRACK_COMPLETE', 'MISSION_DONE')), None)
        if terminal and terminal['event'] in ('TARGET_RECOVERED', 'TRACK_REACQUIRED'):
            recovery_durations.append(terminal['time_s']-event['time_s'])
        else:
            unresolved += 1
    # No-follow runs remain failures but have no defined follow visibility or loss rate.
    started = (row.get('follow_wall_s') or 0.) > 0.
    planned_verified = all(item.get('entry_locked') for item in report.get('occlusions', []))
    failure_components = []
    if not row['success']:
        if 'freeze_not_verified' in row.get('failure_reasons', []):
            failure_components.append('freeze_artifact_drift')
        if (load_json(directory / 'supervisor.json') or {}).get('error'):
            failure_components.append('supervisor_error')
        if not planned_verified:
            failure_components.append('occlusion_entry_not_verified')
        if started and (row.get('visibility') or 0.) < .8:
            failure_components.append('follow_coverage_below_0_8')
        if not report.get('track_complete_event'):
            failure_components.append('track_objective_incomplete')
        if not report.get('landed') or not report.get('disarmed'):
            failure_components.append('landing_disarm_not_confirmed')
    entry_audits = []
    for panel in report.get('occlusions', []):
        preceding = [item for item in associations if item['wall_s'] < panel['start_wall_s']][-3:]
        entry_audits.append({'reported_entry_locked': panel.get('entry_locked'),
            'preceding_association_confirmed': [item.get('identity_confirmed') for item in preceding],
            'preceding_association_wall_s': [item['wall_s'] for item in preceding],
            'largest_preceding_interval_s': max((b['wall_s']-a['wall_s'] for a, b in zip(preceding, preceding[1:])), default=None),
            'limitation': 'Association and target are separate ROS topics; these receipt times are a diagnostic proxy, not a replacement for recorded entry verdict.'})
    follow_samples = [item for item in samples if begin is not None and item['wall_s'] >= begin
                      and (end is None or item['wall_s'] < end) and item.get('vehicle_ground_truth')
                      and item.get('position_ned')]
    ranges = [math.hypot(item['vehicle_ground_truth']['x']-item['position_ned'][1],
                        item['vehicle_ground_truth']['y']-item['position_ned'][0]) for item in follow_samples]
    return {**row, 'success_indicator': int(row['success']),
            'mission_report_pass_indicator': int(bool(report.get('passed'))),
            'flight_closed_loop_indicator': int(bool(report.get('completed') and report.get('track_complete_event')
                and report.get('landed') and report.get('disarmed') and not report.get('failsafe_observed'))),
            'safety_indicator': int(row['safety_event']),
            'follow_started': started,
            'failure_components': failure_components,
            'occlusion_entry_audits': entry_audits,
            'visibility_when_follow_started': row.get('visibility') if started else None,
            'unplanned_losses_when_follow_started': row.get('unplanned_losses') if started else None,
            'panel_window_losses': scheduled if report else None,
            'unplanned_losses_by_panel_schedule': outside if report else None,
            'schedule_unplanned_recovery_mean_s': statistics.mean(outside_recoveries) if outside_recoveries else None,
            'inference_mean_s': statistics.mean(detector_times) if detector_times else None,
            'inference_max_s': max(detector_times, default=None),
            'confirmed_box_border_fraction': len(border_boxes)/len(confirmed_boxes) if confirmed_boxes else None,
            'recovery_max_s': max(recovery_durations, default=None),
            'follow_range_mean_m': statistics.mean(ranges) if ranges else None,
            'follow_range_max_m': max(ranges, default=None),
            'road_exit_observed': any(item['vehicle_ground_truth']['x'] > 150 for item in follow_samples),
            'unrecovered_loss_episodes': unresolved,
            'safety_events_count': row.get('interventions', 0) + int(bool(row.get('failsafe')))
                + int(not row.get('landed_disarmed'))
                + int((row.get('blind_window_max_s') or 0.) > 10.25)
                + int((row.get('blind_command_distance_max_m') or 0.) > 4.3),
            'failure_category': 'passed' if row['success'] else
                'freeze_artifact_drift' if 'freeze_not_verified' in row.get('failure_reasons', []) else
                'startup_or_supervisor' if (load_json(directory / 'supervisor.json') or {}).get('error') else
                'occlusion_entry_not_verified' if not planned_verified else 'mission_criteria',
            'unscorable_occlusion_entries': sum(not item.get('entry_locked') for item in report.get('occlusions', []))}


def audit_runtime(root):
    mismatches, mapping = [], {}
    source = root / 'ros2_ws/src/uav_learning/uav_learning'
    for path in source.glob('*.py'):
        runtime = root / 'ros2_ws/build/uav_learning/uav_learning' / path.name
        checksum = digest(runtime) if runtime.exists() else None
        mapping[str(runtime.relative_to(root))] = checksum
        if checksum != digest(path):
            mismatches.append(str(path.relative_to(root)))
    return {'build_python_matches_source_now': not mismatches, 'mismatches': mismatches,
            'runtime_sha256': mapping,
            'limitation': 'This supplemental final audit is not a historical hash of installed artifacts at every start.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--crossing', type=Path)
    args = parser.parse_args()
    directory = args.study.resolve()
    verify_freeze(ROOT, directory / 'freeze_manifest.json')
    original = load_json(directory / 'study_summary.json')
    rows = [enrich(row) for row in original['trials']]
    groups = {}
    metrics = {**METRICS, 'success_indicator': 'min', 'safety_indicator': 'max',
               'mission_report_pass_indicator': 'min', 'flight_closed_loop_indicator': 'min',
               'safety_events_count': 'max', 'visibility_when_follow_started': 'min',
               'unplanned_losses_when_follow_started': 'max', 'inference_mean_s': 'max',
               'inference_max_s': 'max', 'recovery_max_s': 'max', 'unrecovered_loss_episodes': 'max'}
    metrics.update(follow_range_mean_m='max', follow_range_max_m='max')
    metrics.update(unplanned_losses_by_panel_schedule='max', schedule_unplanned_recovery_mean_s='max')
    metrics.update(confirmed_box_border_fraction='max')
    for group, summary in original['groups'].items():
        selected = [row for row in rows if row['group'] == group]
        groups[group] = {**summary, 'metrics': {key: metric_summary(selected, key, worst)
                                               for key, worst in metrics.items()},
                         'failure_categories': dict(Counter(row['failure_category'] for row in selected)),
                         'failure_component_counts': dict(Counter(component for row in selected
                                                                   for component in row['failure_components'])),
                         'follow_started_trials': sum(row['follow_started'] for row in selected),
                         'unscorable_occlusion_entries': sum(row['unscorable_occlusion_entries'] for row in selected)}
    crossing = load_json(args.crossing / 'identity_summary.json') if args.crossing else None
    crossing_statistics = None
    if crossing:
        identity_rows = []
        for item in crossing['trials']:
            identity = load_json(Path(item['directory']) / 'identity_report.json') or {}
            scorable = (identity.get('scorable_observations') or 0) > 0
            identity_rows.append({'name': item['name'], 'identity_pass_indicator': int(item['identity_pass']),
                'wrong_identity_observations': identity.get('wrong_identity_observations') if scorable else None,
                'scorable_identity_switches': identity.get('scorable_identity_switches') if scorable else None,
                'after_last_overlap_confirmation_wall_s': identity.get('after_last_overlap_confirmation_wall_s'),
                'matched_truth_fraction': identity.get('matched_truth_fraction') if identity.get('observations_total') else None})
        crossing_statistics = {key: metric_summary(identity_rows, key, worst) for key, worst in {
            'identity_pass_indicator': 'min', 'wrong_identity_observations': 'max',
            'scorable_identity_switches': 'max', 'after_last_overlap_confirmation_wall_s': 'max',
            'matched_truth_fraction': 'min'}.items()}
    result = {'groups': groups, 'trials': rows, 'crossing': crossing,
              'crossing_statistics': crossing_statistics,
              'px4_parameter_audit': load_json(directory / 'px4_parameter_audit.json'),
              'freeze_verified_now': True, 'runtime_audit': audit_runtime(ROOT),
              'definitions': {
                  'success': 'Strict original autonomous mission and occlusion-entry criteria; all attempted starts are denominator.',
                  'visibility': 'Wall-time weighted confirmed-target observation coverage, including planned occlusion; not independent pixel visibility or YOLO recall.',
                  'visibility_when_follow_started': 'Supplemental conditional estimate excluding zero follow time; does not change task success denominator.',
                  'unplanned_losses': 'Original conservative classification excludes one panel loss only when panel entry was verified locked.',
                  'unplanned_losses_by_panel_schedule': 'Supplemental temporal classification excludes the first formal loss during each recorded panel window even if entry evidence is insufficient; not a causal guarantee and does not change strict task success.',
                  'recovery': 'Wall seconds; occlusion recovery starts at panel removal; loss recovery starts at formal TRACK loss. Unrecovered episodes counted separately, not imputed.',
                  'inference': 'Recorded detector-stage latency proxy: GMC plus YOLO full-frame prediction and optional ROI. The frozen logger did not isolate network-only inference; processing also includes tracking, association and annotations.',
                  'tracking_error': 'Absolute horizontal pixel-center error conditional on confirmed TRACK observations; not ground-truth identity accuracy.',
                  'std': 'Sample standard deviation across trials, not across frames. Worst recovery is maximum observed episode, censored episodes separate.',
                  'safety': 'Interventions, PX4 failsafe, shutdown before landed/disarmed, approximate blind duration >10.25s or sampled command distance >4.3m.',
                  'blind_limit': 'Controller retains exact 10s / 4m configuration; audit tolerances account for receipt timestamps and sampling.'}}
    write_json(directory / 'detailed_summary.json', result)
    report_path = directory / 'STUDY_REPORT.md'
    marker = '\n## Supplemental Metrics\n'
    original_text = report_path.read_text().split(marker)[0]
    lines = [marker, 'All metrics below retain failed attempts. N and missing counts are explicit.',
             'Conditional visibility excludes only attempts with no follow interval, not failed flights.',
             'Original strict success verdicts and loss classifications are never replaced.', '']
    supplemental = [key for key in metrics if key not in METRICS]
    for name, group in groups.items():
        lines.extend([f'### {name}', '', '| Metric | N / Missing | Mean | Sample Std | Worst |',
                      '| --- | --- | --- | --- | --- |'])
        for key in supplemental:
            item = group['metrics'][key]
            def show(value):
                return f'{value:.5f}' if value is not None else 'N/A'
            lines.append(f"| {key} | {item['n']} / {item['missing']} | {show(item['mean'])} | {show(item['std_sample'])} | {show(item['worst'])} |")
        lines.extend(['', 'Failure categories: '+json.dumps(group['failure_categories'])+'.', ''])
    lines.extend(['### Definitions', '', *[f'- **{key}**: {value}' for key, value in result['definitions'].items()],
                  '', 'Safety observations are limited to recorded telemetry and sampled commands; '
                  'collision/contact and perception ground-truth recall are not comprehensively instrumented.',
                  '', '![Trial statistics](study_metrics.png)', ''])
    if crossing:
        lines.extend(['### Separate Crossing Identity Study', '',
            f"Attempts: {crossing['attempted']} / {crossing['planned']}; strict identity passes: {crossing['identity_passes']}; "
            f"independently verified identity sequences: {crossing['identity_verified']}; missing identity reports: {crossing['reports_missing']}.", '',
            '| Metric | N / Missing | Mean | Sample Std | Worst |', '| --- | --- | --- | --- | --- |'])
        for key, item in crossing_statistics.items():
            lines.append(f"| {key} | {item['n']} / {item['missing']} | {show(item['mean'])} | {show(item['std_sample'])} | {show(item['worst'])} |")
        lines.extend(['', 'Identity uses timestamp-matched Gazebo model poses and projected mesh bounding volumes. '
                      'Overlapping or poorly matched frames are unscorable, not assumed correct. '
                      'Zero observed switches is not proof of identity during unscorable frames.', ''])
    px4 = result['px4_parameter_audit']
    if px4:
        lines.extend(['### PX4 Runtime Parameter Audit', '',
            f"Archived ULogs: {px4['available_logs']} / {px4['attempted_logs']}.",
            'Algorithm/ROS parameters are fixed, but restart bookkeeping and automatically obtained '
            'sensor calibration state are not bitwise-identical. See `px4_parameter_audit.json` '
            'for every initial and runtime difference. This study must not be described as '
            'freezing every PX4 runtime parameter value.', ''])
    report_path.write_text(original_text+'\n'.join(lines))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    names = list(groups)
    figure, axes = plt.subplots(4, 2, figsize=(14, 15))
    panels = [('success_indicator', 'Strict task success (%)', 100),
              ('visibility_when_follow_started', 'Confirmed coverage, follow-started trials (%)', 100),
              ('unplanned_losses', 'Conservatively classified unplanned losses / attempt', 1),
              ('planned_recovery_s', 'After-panel confirmed recovery (wall s)', 1),
              ('mean_pixel_error', 'Confirmed TRACK horizontal error (px)', 1),
              ('inference_mean_s', 'GMC + YOLO full-frame/ROI mean latency (ms)', 1000),
              ('processing_mean_s', 'Perception pipeline mean latency (ms)', 1000),
              ('safety_events_count', 'Safety events / attempt', 1)]
    for axis, (key, title, scale) in zip(axes.flat, panels):
        for index, name in enumerate(names):
            metric = groups[name]['metrics'][key]
            if metric['mean'] is None:
                continue
            error = (metric['std_sample'] or 0)*scale
            label = 'Mean +/- sample std'
            if key == 'success_indicator':
                low, high = groups[name]['success_rate_wilson_95']
                error = [[(metric['mean']-low)*scale], [(high-metric['mean'])*scale]]
                label = 'Success rate + Wilson 95% CI'
            axis.errorbar(index, metric['mean']*scale, yerr=error,
                          fmt='o', capsize=5, color='#067a72', label=label if index == 0 else None)
            axis.scatter(index, metric['worst']*scale, marker='x', color='#c23e50',
                         label='Worst observed' if index == 0 else None)
        axis.set_title(title, fontsize=11)
        axis.set_xticks(range(len(names)), names, rotation=20)
        axis.grid(axis='y', alpha=.25)
    axes[0, 0].legend(fontsize=9)
    figure.suptitle('Frozen independent restart study: failures retained', fontsize=16)
    figure.tight_layout()
    figure.savefig(directory / 'study_metrics.png', dpi=150)
    plt.close(figure)
    print(json.dumps({'groups': {name: {'successes': item['successes'], 'attempted': item['attempted'],
                           'failure_categories': item['failure_categories']} for name, item in groups.items()},
                      'runtime_matches': result['runtime_audit']['build_python_matches_source_now']}, indent=2))


if __name__ == '__main__':
    main()
