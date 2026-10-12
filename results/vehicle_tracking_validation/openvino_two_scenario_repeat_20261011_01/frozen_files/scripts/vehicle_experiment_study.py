#!/usr/bin/env python3
"""Freeze, execute and summarize independent vehicle-following SITL trials."""

import argparse
import ast
from collections import Counter
import csv
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shutil
import signal
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
CORE_PACKAGES = ('uav_learning', 'uav_interfaces', 'px4_msgs')
METRICS = {
    'visibility': 'min', 'unplanned_losses': 'max', 'planned_recovery_s': 'max',
    'unplanned_recovery_mean_s': 'max', 'mean_pixel_error': 'max', 'p95_pixel_error': 'max',
    'processing_mean_s': 'max', 'processing_p95_s': 'max', 'processing_max_s': 'max',
    'frame_interval_p95_s': 'max', 'follow_wall_s': 'max', 'home_error_m': 'max',
    'blind_window_max_s': 'max', 'blind_command_distance_max_m': 'max',
    'gmc_mean_s': 'max', 'full_frame_yolo_mean_s': 'max', 'bytetrack_mean_s': 'max',
    'appearance_mean_s': 'max', 'identity_association_mean_s': 'max',
    'roi_mean_when_run_s': 'max',
    'frame_age_p95_s': 'max', 'queue_wait_p95_s': 'max',
    'vertical_error_std': 'max', 'vertical_bottom_p95': 'max',
    'vertical_edge_fraction': 'max',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def declared_parameters(root):
    result = {}
    for node, module in [('perception_node', 'perception_node'),
                         ('px4_offboard_controller', 'px4_offboard_controller'),
                         ('vehicle_scene', 'vehicle_scene')]:
        tree = ast.parse((root / f'ros2_ws/src/uav_learning/uav_learning/{module}.py').read_text())
        values = {}
        for item in ast.walk(tree):
            if isinstance(item, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'defaults'
                                                   for t in item.targets):
                values.update(ast.literal_eval(item.value))
            if isinstance(item, ast.Call) and isinstance(item.func, ast.Attribute) and item.func.attr == 'declare_parameter':
                if len(item.args) >= 2 and isinstance(item.args[0], ast.Constant):
                    values[item.args[0].value] = ast.literal_eval(item.args[1])
        result[node] = values
    tree = ast.parse((root / 'ros2_ws/src/uav_learning/launch/vehicle_tracking.launch.py').read_text())
    for item in ast.walk(tree):
        if not isinstance(item, ast.Call) or not isinstance(item.func, ast.Name) or item.func.id != 'Node':
            continue
        keywords = {key.arg: key.value for key in item.keywords}
        executable = keywords.get('executable')
        if not isinstance(executable, ast.Constant) or executable.value not in result:
            continue
        parameters = keywords.get('parameters')
        if isinstance(parameters, ast.List):
            for mapping in parameters.elts:
                if not isinstance(mapping, ast.Dict):
                    continue
                for key, value in zip(mapping.keys, mapping.values):
                    try:
                        result[executable.value][ast.literal_eval(key)] = ast.literal_eval(value)
                    except (ValueError, TypeError):
                        pass
    return result


def freeze(root, directory, model, backend_artifacts=None):
    files = set()
    for package in CORE_PACKAGES:
        for path in (root / 'ros2_ws/src' / package).rglob('*'):
            if path.is_file() and not any(part in ('__pycache__', 'test', '.git', '.pytest_cache',
                                                 '.mypy_cache', '.ruff_cache') for part in path.parts):
                if path.suffix != '.pyc':
                    files.add(path)
    for name in ('x500_perception', 'x500', 'x500_base', 'uav_rgb_camera'):
        files.update(path for path in (root / f'PX4-Autopilot/Tools/simulation/gz/models/{name}').rglob('*') if path.is_file())
    files.update(path for path in (root / 'PX4-Autopilot/Tools/simulation/gz/worlds').rglob('*') if path.is_file())
    for name in ('run_vehicle_tracking_validation.py', 'validate_vehicle_tracking.py',
                 'vehicle_experiment_study.py', 'px4_env.sh', 'analyze_vehicle_association.py',
                 'vehicle_crossing_validation.py', 'vehicle_lane_change.py'):
        files.add(root / 'scripts' / name)
    files.add(root / 'PX4-Autopilot/build/px4_sitl_default/bin/px4')
    files.update(path for path in (root / 'PX4-Autopilot/build/px4_sitl_default/etc').rglob('*') if path.is_file())
    files.add(model)
    if backend_artifacts:
        files.update(path for path in Path(backend_artifacts).resolve().iterdir() if path.suffix in ('.xml', '.bin', '.json'))
    hashes = {}
    snapshot = directory / 'frozen_files'
    for path in sorted(files):
        relative = str(path.relative_to(root))
        hashes[relative] = digest(path)
        destination = snapshot / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
    manifest = {'source_sha256': hashes, 'model_path': str(model),
                'declared_parameters': declared_parameters(root),
                'package_versions': {name: importlib.metadata.version(name)
                                     for name in ('ultralytics', 'torch', 'torchvision', 'numpy', 'opencv-python')},
                'safety': {'recovery_timeout': 10.0, 'recovery_max_distance': 4.0},
                'enforcement': 'Live runtime files are checked before/after each trial; drift stops the study. '
                               'Startup ROS parameters are checked. Snapshot copies preserve evidence, '
                               'but this does not make the running filesystem immutable.'}
    write_json(directory / 'freeze_manifest.json', manifest)
    return manifest


def verify_freeze(root, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text())
    changed = [name for name, checksum in manifest['source_sha256'].items()
               if not (root / name).is_file() or digest(root / name) != checksum]
    versions = {name: importlib.metadata.version(name) for name in manifest['package_versions']}
    if changed or versions != manifest['package_versions']:
        raise RuntimeError('Frozen implementation changed: ' + ', '.join(changed or ['package_versions']))


def verify_parameters(captured, scenario, expected=None):
    expected = expected or declared_parameters(ROOT)
    overrides = {'vehicle_scene': {'vehicle_speed': scenario['vehicle_speed'],
                                   'occlusion_start': scenario['occlusion_start'],
                                   'occlusion_duration': scenario['occlusion_duration'],
                                   'occlusion_enabled': True}}
    for key in ('traffic_scenario', 'distractor_color', 'parked_vehicle_y'):
        if key in scenario:
            overrides['vehicle_scene'][key] = scenario[key]
    if 'recovery_competition_enabled' in scenario:
        overrides['perception_node'] = {
            'recovery_competition_enabled': scenario['recovery_competition_enabled']}
    for key in ('predict_box_scale_velocity', 'cpu_inference_threads', 'detector_backend', 'backend_artifacts'):
        if key in scenario:
            overrides.setdefault('perception_node', {})[key] = scenario[key]
    errors = []
    for node, defaults in expected.items():
        for key, value in {**defaults, **overrides.get(node, {})}.items():
            if node == 'perception_node' and key == 'model_path':
                continue
            if captured.get(node, {}).get(key) != value:
                errors.append(f'{node}.{key}')
    if captured.get('px4_offboard_controller', {}).get('recovery_timeout') != 10.0:
        errors.append('blind_motion_budget')
    if errors:
        raise RuntimeError('Runtime parameters differ from the frozen experiment: ' + ', '.join(errors))


def load_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def load_lines(path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        try:
            rows.append(json.loads(line))
        except ValueError:
            pass
    return rows


def percentile(values, fraction):
    values = sorted(values)
    return values[int((len(values) - 1) * fraction)] if values else None


def loss_counts(events, occlusions):
    losses = [event for event in events if event['event'] == 'TRACK_TARGET_LOST']
    planned = set()
    for panel in occlusions:
        if not panel.get('entry_locked') or panel.get('end_wall_s') is None:
            continue
        index = next((index for index, event in enumerate(losses) if index not in planned and
                      panel['start_wall_s'] <= event['time_s'] <= panel['end_wall_s']), None)
        if index is not None:
            planned.add(index)
    unplanned_recoveries = []
    for index, loss in enumerate(losses):
        if index in planned:
            continue
        recovery = next((event for event in events if event['time_s'] > loss['time_s'] and
                         event['event'] in ('TARGET_RECOVERED', 'TRACK_REACQUIRED', 'TRACK_COMPLETE', 'MISSION_DONE')), None)
        if recovery and recovery['event'] in ('TARGET_RECOVERED', 'TRACK_REACQUIRED'):
            unplanned_recoveries.append(recovery['time_s'] - loss['time_s'])
    return len(losses), len(planned), len(losses) - len(planned), unplanned_recoveries


def blind_audit(samples, events):
    windows, start = [], None
    for event in events:
        if event['event'] in ('TRACK_OBSERVATION_GAP', 'APPROACH_OBSERVATION_GAP'):
            start = event['time_s']
        elif start is not None and event['event'] in ('OBSERVATION_GAP_CLEARED', 'TARGET_RECOVERED', 'RECOVERY_TIMEOUT'):
            windows.append((start, event['time_s']))
            start = None
    distances = []
    for begin, end in windows:
        origin = next((row['position_ned'] for row in samples if row['wall_s'] >= begin and row.get('position_ned')), None)
        if origin is None:
            continue
        for row in samples:
            if begin <= row['wall_s'] < end and row['state'] in ('TRACK', 'APPROACH', 'RECOVER') and row.get('setpoint'):
                position = row['setpoint']['position_ned']
                if all(math.isfinite(value) for value in position[:2]):
                    distances.append(math.hypot(position[0] - origin[0], position[1] - origin[1]))
    return (max((end - start for start, end in windows), default=None), max(distances, default=None))


def trial_row(directory, trial):
    report = load_json(directory / 'report.json')
    supervisor = load_json(directory / 'supervisor.json') or {}
    samples = load_lines(directory / 'samples.jsonl')
    associations = load_lines(directory / 'association.jsonl')
    if report:
        events, occlusions = report.get('events', []), report.get('occlusions', [])
    else:
        events, occlusions = [], []
    begin = next((row['wall_s'] for row in samples if row['state'] == 'APPROACH'), None)
    end = next((row['wall_s'] for row in samples if begin is not None and row['wall_s'] > begin
                and row['state'] in ('RETURN', 'LAND', 'DONE')), None)
    follow = [row for row in associations if begin is not None and row['wall_s'] >= begin
              and (end is None or row['wall_s'] < end)]
    times = [row['processing_s'] for row in follow if isinstance(row.get('processing_s'), (int, float))]
    intervals = [b['wall_s'] - a['wall_s'] for a, b in zip(follow, follow[1:])]
    total, planned, unplanned, recoveries = loss_counts(events, occlusions)
    blind_time, blind_distance = blind_audit(samples, events)
    drift = supervisor.get('freeze_verified') is not True
    params_missing = not (directory / 'runtime_parameters.json').exists()
    unsafe = bool(supervisor.get('interventions') or (report or {}).get('failsafe_observed')
                  or not supervisor.get('landed_disarmed_before_shutdown')
                  or (blind_time is not None and blind_time > 10.25)
                  or (blind_distance is not None and blind_distance > 4.3))
    reasons = []
    if not report:
        reasons.append('missing_or_invalid_report')
    if supervisor.get('error'):
        reasons.append(supervisor['error'])
    if report and not report.get('passed'):
        reasons.append('mission_criteria_failed')
    if drift:
        reasons.append('freeze_not_verified')
    if params_missing:
        reasons.append('parameters_not_captured')
    row = {**trial, 'directory': str(directory),
           'success': bool(report and supervisor.get('autonomous_passed') and not drift and not params_missing),
           'report_available': bool(report), 'failure_reasons': reasons,
           'visibility': (report or {}).get('follow_time_visible_fraction'),
           'total_losses': total if report else None, 'planned_losses': planned if report else None,
           'unplanned_losses': unplanned if report else None,
           'planned_recovery_s': max((item['confirmed_recovery_s'] for item in occlusions
                                     if item.get('confirmed_recovery_s') is not None), default=None),
           'unplanned_recovery_mean_s': statistics.mean(recoveries) if recoveries else None,
           'unplanned_recoveries_observed': len(recoveries),
           'mean_pixel_error': (report or {}).get('track_mean_abs_pixel_error'),
           'p95_pixel_error': (report or {}).get('track_p95_abs_pixel_error'),
           'processing_mean_s': statistics.mean(times) if times else None,
           'processing_p95_s': percentile(times, 0.95), 'processing_max_s': max(times, default=None),
           'frame_interval_p95_s': percentile(intervals, 0.95),
           'follow_wall_s': (report or {}).get('follow_wall_time_s'),
           'home_error_m': (report or {}).get('final_home_horizontal_error_m'),
           'blind_window_max_s': blind_time, 'blind_command_distance_max_m': blind_distance,
           'safety_event': unsafe, 'interventions': len(supervisor.get('interventions', [])),
           'failsafe': (report or {}).get('failsafe_observed'),
           'landed_disarmed': supervisor.get('landed_disarmed_before_shutdown', False),
           'scene_occlusion_passed': (report or {}).get('occlusion_recovery_passed'),
           'identity_independently_verified': False,
           'frame_reason_counts': dict(Counter(item.get('reason', 'unknown') for item in follow))}
    for key in ('gmc_s', 'full_frame_yolo_s', 'bytetrack_s', 'appearance_s', 'identity_association_s'):
        values = [(item if key in ('appearance_s', 'identity_association_s') else item.get('detector', {})).get(key)
                  for item in follow]
        values = [value for value in values if isinstance(value, (int, float)) and math.isfinite(value)]
        row[key[:-2] + '_mean_s'] = statistics.mean(values) if values else None
    roi_times = [item.get('detector', {}).get('roi_s') for item in follow]
    roi_times = [value for value in roi_times if isinstance(value, (int, float)) and math.isfinite(value)]
    row['roi_mean_when_run_s'] = statistics.mean(roi_times) if roi_times else None
    row['roi_pass_count'] = len(roi_times)
    for key in ('frame_age_s', 'queue_wait_s'):
        values = [item[key] for item in follow if isinstance(item.get(key), (int, float))]
        row[key[:-2] + '_p95_s'] = percentile(values, 0.95)
    row['stale_frame_count'] = sum(item.get('reason') in ('stale_inference_result', 'stale_queued_frame')
                                   for item in follow)
    row['gmc_quality_reason_counts'] = dict(Counter(
        item.get('camera_motion', {}).get('quality', {}).get('reason', 'not_recorded') for item in follow))
    vertical, bottoms, edges = [], [], []
    for item in follow:
        shape = item.get('image_shape')
        if not shape:
            continue
        height = shape[0]
        for candidate in item.get('candidates', []):
            if candidate.get('accepted'):
                _, top, _, bottom = candidate['bbox']
                vertical.append((top + bottom) / height - 1)
                bottoms.append(bottom / height)
                edges.append(top <= height * 0.05 or bottom >= height * 0.95)
    row['vertical_error_std'] = statistics.pstdev(vertical) if vertical else None
    row['vertical_bottom_p95'] = percentile(bottoms, 0.95)
    row['vertical_edge_fraction'] = statistics.mean(edges) if edges else None
    return row


def metric_summary(rows, key, worst):
    observed = [(row[key], row['name']) for row in rows
                if isinstance(row.get(key), (int, float)) and math.isfinite(row[key])]
    values = [value for value, _ in observed]
    extreme = (min(values) if worst == 'min' else max(values)) if values else None
    return {'n': len(values), 'missing': len(rows) - len(values),
            'mean': statistics.mean(values) if values else None,
            'std_sample': statistics.stdev(values) if len(values) >= 2 else None,
            'min': min(values) if values else None, 'max': max(values) if values else None,
            'worst': extreme, 'worst_trials': [name for value, name in observed if value == extreme]}


def summarize(rows, planned_count):
    count, successes = len(rows), sum(row['success'] for row in rows)
    probability = successes / count if count else None
    interval = None
    if count:
        z = 1.959963984540054
        center = (probability + z*z/(2*count))/(1 + z*z/count)
        radius = z*math.sqrt(probability*(1-probability)/count + z*z/(4*count*count))/(1 + z*z/count)
        interval = [max(0, center-radius), min(1, center+radius)]
    return {'planned': planned_count, 'attempted': count, 'not_attempted': planned_count-count,
            'successes': successes, 'failures': count-successes, 'success_rate': probability,
            'success_rate_wilson_95': interval,
            'safety_event_trials': sum(row['safety_event'] for row in rows),
            'interventions': sum(row['interventions'] for row in rows),
            'metrics': {key: metric_summary(rows, key, worst) for key, worst in METRICS.items()}}


def publish_summary(directory, plan, rows):
    groups = {}
    for group in dict.fromkeys(trial['group'] for trial in plan):
        groups[group] = summarize([row for row in rows if row['group'] == group],
                                  sum(trial['group'] == group for trial in plan))
    report = {'groups': groups, 'trials': rows,
              'limitations': ['No failures are retried or removed. Missing metrics have explicit counts; '
                              'means include available failed-trial observations, not successes only.',
                              'Std is sample standard deviation; one observation has undefined std.',
                              'Repeated deterministic scenes measure restart/runtime variability, not '
                              'independent environmental diversity or a general reliability rate.',
                              'TRACK pixel errors are conditional on confirmed observations, not YOLO mAP.',
                              'Blind audits approximate receipt timestamps and sampled setpoints; '
                              'they supplement, not replace, controller invariant tests.',
                              'Baseline and stress groups are reported separately. Crossing identity '
                              'needs its own ground-truth evaluation; task pass alone cannot prove ReID.']}
    write_json(directory / 'study_summary.json', report)
    if rows:
        fields = [key for key in rows[0] if key not in ('frame_reason_counts', 'failure_reasons')]
        with (directory / 'trials.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fields + ['failure_reasons'], extrasaction='ignore')
            writer.writeheader()
            for row in rows:
                writer.writerow({**row, 'failure_reasons': '; '.join(row['failure_reasons'])})
    lines = ['# Frozen Vehicle Tracking Study', '', 'Failed and interrupted attempts are retained. '
             'Missing observations are not replaced with successful-run values.', '',
             '| Group | Attempted / Planned | Success | Safety Event Trials |', '| --- | --- | --- | --- |']
    for group, summary in groups.items():
        rate = f"{summary['success_rate']:.1%}" if summary['success_rate'] is not None else 'N/A'
        lines.append(f"| {group} | {summary['attempted']} / {summary['planned']} | {summary['successes']} ({rate}) | {summary['safety_event_trials']} |")
    for group, summary in groups.items():
        lines.extend(['', f'## {group}', '', '| Metric | N / Missing | Mean | Sample Std | Worst |',
                      '| --- | --- | --- | --- | --- |'])
        for key, metric in summary['metrics'].items():
            def show(value):
                return f'{value:.4f}' if value is not None else 'N/A'
            lines.append(f"| {key} | {metric['n']} / {metric['missing']} | {show(metric['mean'])} | {show(metric['std_sample'])} | {show(metric['worst'])} |")
    lines.extend(['', '## Limitations', '', *['- '+item for item in report['limitations']]])
    (directory / 'STUDY_REPORT.md').write_text('\n'.join(lines)+'\n')


def make_plan(groups):
    scenarios = [('baseline', 10, 0.8, 4.0, False)]
    if groups:
        scenarios += [('speed_1_2', 5, 1.2, 4.0, False), ('speed_1_6', 5, 1.6, 4.0, False),
                      ('occlusion_2s', 5, 0.8, 2.0, False), ('occlusion_6s', 5, 0.8, 6.0, False)]
    return [{'name': f'{group}_{index:02d}', 'group': group, 'vehicle_speed': speed,
             'occlusion_start': 15.0, 'occlusion_duration': duration, 'crossing': crossing}
            for group, count, speed, duration, crossing in scenarios for index in range(1, count+1)]


def make_pilot_plan():
    return [{'name': name + '_01', 'group': name, 'vehicle_speed': speed,
             'occlusion_start': 15.0, 'occlusion_duration': 4.0, 'crossing': crossing}
            for name, speed, crossing in [('baseline_pilot', 0.8, False),
                                          ('speed_1_6_pilot', 1.6, False),
                                          ('crossing_pilot', 0.8, True)]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--groups', action='store_true')
    mode.add_argument('--pilot', action='store_true', help='Three development checks, not a repeated reliability study.')
    parser.add_argument('--model-path', type=Path, default=ROOT / 'yolo11s.pt')
    args = parser.parse_args()
    directory = args.output.resolve()
    if directory.exists():
        raise RuntimeError('Use a fresh study directory; completed evidence is never overwritten.')
    directory.mkdir(parents=True)
    model = args.model_path.resolve()
    freeze(ROOT, directory, model)
    plan, rows = make_pilot_plan() if args.pilot else make_plan(args.groups), []
    write_json(directory / 'experiment_plan.json', plan)
    stopped = False
    active = None

    def interrupt(signum, frame):
        nonlocal stopped
        stopped = True
        if active is not None and active.poll() is None:
            active.send_signal(signal.SIGINT)

    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    publish_summary(directory, plan, rows)
    for trial in plan:
        if stopped:
            break
        verify_freeze(ROOT, directory / 'freeze_manifest.json')
        for name in ('px4', 'MicroXRCEAgent', 'gz sim server'):
            if subprocess.run(['pgrep', '-x', name], capture_output=True).returncode == 0:
                raise RuntimeError(f'Existing {name}; study stopped, no process was killed.')
        trial_dir = directory / trial['name']
        command = [sys.executable, str(ROOT / 'scripts/run_vehicle_tracking_validation.py'),
                   '--output', str(trial_dir), '--model-path', str(model),
                   '--vehicle-speed', str(trial['vehicle_speed']),
                   '--occlusion-start', str(trial['occlusion_start']),
                   '--occlusion-duration', str(trial['occlusion_duration']),
                   '--freeze-manifest', str(directory / 'freeze_manifest.json')]
        if trial['crossing']:
            command.append('--crossing')
        with (directory / (trial['name'] + '_supervisor.log')).open('w') as log:
            print(json.dumps({'started': trial['name'], 'completed': len(rows), 'planned': len(plan)}), flush=True)
            active = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            last_update = 0
            while active.poll() is None:
                if time.monotonic() - last_update >= 30:
                    samples = load_lines(trial_dir / 'samples.jsonl')
                    last = samples[-1] if samples else {}
                    print(json.dumps({'active': trial['name'], 'completed': len(rows),
                                      'wall_s': last.get('wall_s'), 'state': last.get('state')}), flush=True)
                    last_update = time.monotonic()
                time.sleep(1)
            returncode = active.returncode
            active = None
        row = trial_row(trial_dir, trial)
        row['returncode'] = returncode
        if returncode != 0:
            row['success'] = False
            row['failure_reasons'].append(f'supervisor_exit_{returncode}')
        if args.pilot:
            row['flight_success'] = row['success']
            identity = load_json(trial_dir / 'identity_report.json') or {}
            row['identity_independently_verified'] = bool(identity.get('identity_independently_verified'))
            row['wrong_identity_observations'] = identity.get('wrong_identity_observations')
            row['identity_pass'] = bool(row['flight_success'] and row['identity_independently_verified']) if trial['crossing'] else None
            if trial['crossing'] and not row['identity_independently_verified']:
                row['success'] = False
                row['failure_reasons'].append('independent_identity_not_verified')
        rows.append(row)
        publish_summary(directory, plan, rows)
        print(json.dumps({'finished': trial['name'], 'success': row['success'],
                          'visibility': row['visibility'], 'unplanned_losses': row['unplanned_losses'],
                          'completed': len(rows), 'failures': sum(not row['success'] for row in rows)}), flush=True)
        if stopped:
            break
        verify_freeze(ROOT, directory / 'freeze_manifest.json')
        time.sleep(3)
    write_json(directory / 'study_status.json', {'planned': len(plan), 'attempted': len(rows),
                                               'completed': len(rows) == len(plan), 'interrupted': stopped})
    return 0 if len(rows) == len(plan) else 2


if __name__ == '__main__':
    raise SystemExit(main())
