#!/usr/bin/env python3
"""Read-only integrity and final report for a selected overtaking repeat batch."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shutil

from analyze_vehicle_framing import analyze as framing
from analyze_vehicle_latency import analyze as latency
from vehicle_experiment_study import digest, load_json, load_lines, write_json


def inspect(study):
    summary = load_json(study / 'study_summary.json')
    protocol = load_json(study / 'batch_protocol.json')
    manifest = load_json(study / 'freeze_manifest.json')
    plan = load_json(study / 'plan.json')
    status = load_json(study / 'study_status.json')
    audit = load_json(study / 'px4_parameter_audit.json') or {}
    errors, pids, trials = [], [], []
    rows = summary['trials']
    if ([row['name'] for row in rows] != [row['name'] for row in plan]
            or not status['completed'] or status['error'] or status['interrupted'] or status['active_trial']):
        errors.append('batch_incomplete')
    if len(rows) != status['attempted'] or len(plan) != status['planned']:
        errors.append('batch_count_mismatch')
    for name, checksum in manifest['source_sha256'].items():
        path = study / 'frozen_files' / name
        if not path.is_file() or digest(path) != checksum:
            errors.append('frozen_file_mismatch:' + name)
    source = study / 'frozen_files/ros2_ws/src/uav_learning/uav_learning'
    for path in source.glob('*.py'):
        other = study / 'installed_snapshot' / path.name
        if not other.is_file() or digest(other) != digest(path):
            errors.append('installed_module_mismatch:' + path.name)
    logs = {item['directory']: item for item in audit.get('trials', [])}
    reference_hashes = load_json(study / 'reference_evidence/implementation_snapshot.json')['source_sha256']
    for name, checksum in reference_hashes.items():
        if manifest['source_sha256'].get(name) != checksum:
            errors.append('selected_reference_mismatch:' + name)
    for row in rows:
        directory = Path(row['directory'])
        implementation = load_json(directory / 'implementation_snapshot.json') or {}
        supervisor = load_json(directory / 'supervisor.json') or {}
        report = load_json(directory / 'report.json') or {}
        identity = load_json(directory / 'identity_report.json') or {}
        parameters = load_json(directory / 'runtime_parameters.json') or {}
        for name, checksum in implementation.get('source_sha256', {}).items():
            if checksum != manifest['source_sha256'].get(name):
                errors.append('trial_source_mismatch:' + row['name'] + ':' + name)
        if not implementation.get('source_sha256'):
            errors.append('missing_trial_snapshot:' + row['name'])
        if implementation.get('model_sha256') != manifest['source_sha256'].get('yolo11s.pt'):
            errors.append('trial_model_mismatch:' + row['name'])
        for node, expected in manifest['declared_parameters'].items():
            for name, value in expected.items():
                if parameters.get(node, {}).get(name) != value:
                    errors.append('trial_parameter_mismatch:' + row['name'] + ':' + node + '.' + name)
        for key in ('overtaking', 'crossing', 'gui', 'vehicle_speed', 'occlusion_start', 'occlusion_duration',
                    'smooth_recovery_setpoints', 'recovery_competition_enabled',
                    'predict_box_scale_velocity', 'detector_backend', 'cpu_inference_threads'):
            if implementation.get('scenario', {}).get(key) != row[key]:
                errors.append('trial_scenario_mismatch:' + row['name'] + ':' + key)
        if not supervisor.get('freeze_verified') or not supervisor.get('parameters_verified'):
            errors.append('runtime_not_verified:' + row['name'])
        if not report or not identity:
            errors.append('missing_trial_report:' + row['name'])
        path = directory / 'flight.ulg'
        entry = logs.get(str(directory), {})
        if not path.is_file() or digest(path) != entry.get('ulog_sha256'):
            errors.append('ulog_hash_mismatch:' + row['name'])
        text = (study / (row['name'] + '_supervisor.log')).read_text()
        match = re.search(r'Started px4: PID (\d+)', text)
        if match:
            pids.append(int(match.group(1)))
        else:
            errors.append('missing_px4_start:' + row['name'])
        flight_pass = bool(report.get('passed') and supervisor.get('autonomous_passed')
                           and not supervisor.get('error') and row['returncode'] == 0)
        strict = flight_pass and bool(identity.get('identity_independently_verified')) and not row['safety_event']
        if row['success'] != strict:
            errors.append('summary_success_mismatch:' + row['name'])
        partials = [candidate for association in load_lines(directory / 'association.jsonl')
                    for candidate in association.get('candidates', [])
                    if candidate.get('accepted') and candidate.get('vertical_truncated')]
        trials.append({'name': row['name'], 'flight_pass': flight_pass,
                       'identity_verified': bool(identity.get('identity_independently_verified')),
                       'strict_pass': strict, 'accepted_truncated_frames': len(partials),
                       'protected_truncated_frames': sum(item.get('geometry_update') == 'horizontal_only' for item in partials),
                       'failure_causes': row['criteria_failure_causes'],
                       'input_sha256': {name: digest(directory / name) for name in (
                           'report.json', 'identity_report.json', 'supervisor.json',
                           'association.jsonl', 'samples.jsonl', 'implementation_snapshot.json',
                           'runtime_parameters.json', 'flight.ulg') if (directory / name).is_file()}})
    if len(pids) != len(set(pids)):
        errors.append('duplicate_px4_start')
    return {'planned': len(plan), 'attempted': len(rows), 'all_attempts_finished': status['completed'],
            'evidence_complete': not errors, 'integrity_errors': errors,
            'unique_px4_starts': len(set(pids)),
            'task_passes': sum(item['flight_pass'] for item in trials),
            'identity_passes': sum(item['identity_verified'] for item in trials),
            'strict_passes': sum(item['strict_pass'] for item in trials),
            'autonomous_landed_trials': sum(bool(row['landed_disarmed'] and not row['interventions']) for row in rows),
            'wrong_identity_observations': sum(row.get('wrong_identity_observations') or 0 for row in rows),
            'failure_counts': dict(Counter(cause for item in trials for cause in item['failure_causes'])),
            'reference_coverage': protocol['reference_coverage'], 'trials': trials,
            'limitations': protocol['limitations']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    study, output = args.study.resolve(), args.output.resolve()
    if output.exists() or output.is_relative_to(study):
        parser.error('Use a new external directory; flight evidence remains read-only.')
    output.mkdir(parents=True)
    integrity = inspect(study)
    integrity['analysis_script_sha256'] = digest(Path(__file__))
    write_json(output / 'completion_check.json', integrity)
    shutil.copy2(Path(__file__), output / Path(__file__).name)
    if not integrity['all_attempts_finished']:
        print(json.dumps({key: value for key, value in integrity.items() if key != 'trials'}, indent=2))
        return 1
    summary = load_json(study / 'study_summary.json')
    stage_audit = latency(study)
    write_json(output / 'latency_safety_audit.json', stage_audit)
    framing_summaries = []
    for row in summary['trials']:
        metrics, frames = framing(Path(row['directory']))
        framing_summaries.append(metrics)
        (output / (row['name'] + '_framing.jsonl')).write_text(
            ''.join(json.dumps(frame, allow_nan=False) + '\n' for frame in frames))
    write_json(output / 'framing_audit.json', {'trials': framing_summaries})
    for name in ('analyze_vehicle_framing.py', 'analyze_vehicle_latency.py'):
        shutil.copy2(Path(__file__).with_name(name), output / name)
    print(json.dumps({key: value for key, value in integrity.items() if key != 'trials'}, indent=2))
    return 0 if integrity['evidence_complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
