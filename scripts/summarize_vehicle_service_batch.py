#!/usr/bin/env python3
"""Summarize scene requests and plot a batch without changing flight evidence."""

import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import shutil

import numpy as np

from vehicle_experiment_study import digest, load_json, load_lines, metric_summary, write_json


def request_summary(rows):
    durations = [row['duration_s'] * 1000 for row in rows
                 if isinstance(row.get('duration_s'), (int, float))]
    failed = [row for row in rows if not row.get('success')]
    return {'requests': len(rows), 'failed': len(failed),
            'failed_reasons': dict(Counter(row.get('reason', 'unknown') for row in failed)),
            'mean_ms': float(np.mean(durations)) if durations else None,
            'p95_ms': float(np.percentile(durations, 95)) if durations else None,
            'max_ms': max(durations, default=None)}


def analyze(study):
    summary = load_json(study / 'study_summary.json')
    status = load_json(study / 'study_status.json')
    if (status.get('active_trial') or not status.get('completed')
            and not status.get('interrupted') and not status.get('error')):
        raise RuntimeError('Wait for the batch to finish before final analysis.')
    trials, inputs, errors = [], {}, []
    for trial in summary['trials']:
        directory = Path(trial['directory'])
        report = load_json(directory / 'report.json') or {}
        logs, all_rows = {}, []
        for name in ('scene_service.jsonl', 'traffic_service.jsonl'):
            path = directory / name
            present = path.is_file()
            rows = load_lines(path) if present else []
            all_rows.extend(rows)
            complete = bool(rows) and [row.get('sequence') for row in rows] == list(range(1, len(rows)+1))
            inconsistent = sum(bool(row.get('success')) != bool(
                row.get('binding_result') and row.get('response_data')) for row in rows)
            logs[name] = {**request_summary(rows), 'present': present,
                          'sequence_complete': complete, 'inconsistent_success_records': inconsistent,
                          'worker_pids': sorted({row['worker_pid'] for row in rows if 'worker_pid' in row}),
                          'services': {service: request_summary([row for row in rows if row['service'] == service])
                                       for service in sorted({row['service'] for row in rows})}}
            if present:
                inputs[str(path)] = digest(path)
            if not present or not complete or inconsistent:
                errors.append({'trial': trial['name'], 'log': name, 'present': present,
                               'sequence_complete': complete, 'inconsistent_success_records': inconsistent})
        requests = request_summary(all_rows)
        trials.append({'name': trial['name'], 'strict_pass': trial['success'],
                       'task_pass': trial['flight_success'],
                       'identity_pass': trial['identity_independently_verified'],
                       'coverage': trial['visibility'], 'recovery_s': trial['planned_recovery_s'],
                       'outside_panel_losses': trial['outside_panel_losses'],
                       'scene_report_errors': trial['scene_update_errors'],
                       'vehicle_travel_m': report.get('vehicle_travel_m'),
                       'drone_follow_travel_m': report.get('drone_follow_travel_m'),
                       'safety_event': trial['safety_event'],
                       'criteria_failure_causes': trial['criteria_failure_causes'],
                       **requests, 'logs': logs})
    protocol = load_json(study / 'batch_protocol.json')
    for name in ('study_summary.json', 'study_status.json', 'batch_protocol.json', 'freeze_manifest.json'):
        inputs[str(study / name)] = digest(study / name)
    return {'study': str(study), 'planned': status['planned'], 'attempted': status['attempted'],
            'completed': status['completed'], 'stop_reason': status['error'],
            'task_passes': sum(row['task_pass'] for row in trials),
            'identity_passes': sum(row['identity_pass'] for row in trials),
            'strict_passes': sum(row['strict_pass'] for row in trials),
            'reference': protocol['reference'],
            'total_requests': sum(row['requests'] for row in trials),
            'failed_requests': sum(row['failed'] for row in trials),
            'failed_reasons': dict(sum((Counter(log['failed_reasons']) for row in trials
                                        for log in row['logs'].values()), Counter())),
            'request_metrics': {key: metric_summary(trials, key, 'max')
                                for key in ('requests', 'failed', 'mean_ms', 'p95_ms', 'max_ms')},
            'motion_metrics': {key: metric_summary(trials, key, 'min')
                               for key in ('vehicle_travel_m', 'drone_follow_travel_m')},
            'log_integrity_errors': errors, 'trials': trials, 'input_sha256': inputs,
            'limitations': ['Existing task and identity verdicts are not reclassified.',
                            'Request mean/P95/max describe recorded service calls, not image-to-control latency.',
                            'Missing or incomplete logs are explicit errors, not zero-failure evidence.',
                            'Creation retries remain visible; no failed call is dropped.',
                            'Deterministic different-color overtaking is not same-appearance crossing.']}


def plot(summary, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    trials = summary['trials']
    x = np.arange(1, len(trials)+1)
    colors = ['#278267' if row['success'] else '#c24b48' for row in trials]
    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True, constrained_layout=True)
    metrics = [('visibility', 100, 'Confirmed Coverage (%)'),
               ('planned_recovery_s', 1, 'Panel Recovery (wall s)'),
               ('processing_mean_s', 1000, 'Mean Perception Processing (ms)')]
    for ax, (key, scale, label) in zip(axes, metrics):
        values = [row.get(key) * scale if row.get(key) is not None else np.nan for row in trials]
        ax.bar(x, values, color=colors, width=.65)
        ax.set_ylabel(label)
        ax.grid(axis='y', alpha=.2)
        ax.set_axisbelow(True)
        for index, value in zip(x, values):
            if np.isfinite(value):
                ax.annotate(f'{value:.2f}', (index, value), xytext=(0, 4), textcoords='offset points',
                            ha='center', fontsize=9)
            else:
                ax.text(index, .02, 'N/A', transform=ax.get_xaxis_transform(), ha='center')
        ax.margins(y=.2)
    axes[0].axhline(80, color='#555555', linestyle='--', linewidth=1)
    axes[0].set_ylim(0, 110)
    axes[-1].set_xticks(x, [row['name'].rsplit('_', 1)[-1] for row in trials])
    axes[-1].set_xlabel('Independent Simulation Restart (green: strict pass; red: failure)')
    fig.suptitle('Frozen Different-Color Overtaking Batch')
    fig.savefig(output / 'batch_metrics.png', dpi=160)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    study, output = args.study.resolve(), args.output.resolve()
    if output == study or output.is_relative_to(study):
        parser.error('Use an external output directory; flight evidence is read-only.')
    if (output / 'scene_service_summary.json').exists():
        parser.error('Refuse to overwrite an existing analysis.')
    result = analyze(study)
    output.mkdir(parents=True, exist_ok=True)
    result['analysis_script_sha256'] = digest(Path(__file__))
    write_json(output / 'scene_service_summary.json', result)
    fields = ['name', 'strict_pass', 'task_pass', 'identity_pass', 'coverage', 'recovery_s',
              'outside_panel_losses', 'requests', 'failed', 'mean_ms', 'p95_ms', 'max_ms', 'safety_event']
    with (output / 'scene_service_trials.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(result['trials'])
    plot(load_json(study / 'study_summary.json'), output)
    shutil.copy2(Path(__file__), output / Path(__file__).name)
    print(json.dumps({key: value for key, value in result.items() if key not in (
        'trials', 'input_sha256', 'request_metrics')}, indent=2))
    return 0 if not result['log_integrity_errors'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
