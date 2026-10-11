#!/usr/bin/env python3
"""Read-only integrity checks and explicit failure criteria for frozen repeats."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re

from vehicle_experiment_study import digest, load_json, write_json


def failure_causes(report, identity):
    causes = []
    if not report:
        causes.append('missing_or_invalid_report')
    else:
        for field in ('completed', 'track_complete_event', 'landed', 'disarmed'):
            if not report.get(field):
                causes.append(field + '_not_confirmed')
        for field, cutoff, label in (
                ('follow_time_visible_fraction', 0.8, 'confirmed_coverage_below_0_8'),
                ('track_detection_fraction', 0.8, 'track_detection_fraction_below_0_8'),
                ('vehicle_travel_m', 1.0, 'vehicle_motion_insufficient'),
                ('drone_track_travel_m', 1.0, 'drone_motion_insufficient')):
            value = report.get(field)
            if value is None:
                causes.append(field + '_missing')
            elif value < cutoff or (cutoff == 1.0 and value == cutoff):
                causes.append(label)
        home = report.get('final_home_horizontal_error_m')
        if home is None:
            causes.append('home_error_missing')
        elif home > 1.0:
            causes.append('home_error_above_1_m')
        if report.get('failsafe_observed'):
            causes.append('px4_failsafe_observed')
        if report.get('occlusions') and not report.get('occlusion_recovery_passed'):
            causes.append('occlusion_entry_not_locked' if any(
                not row.get('entry_locked') for row in report['occlusions'])
                else 'occlusion_criteria_failed')
        if not report.get('passed') and not causes:
            causes.append('reported_task_failure_unspecified')
    if not identity:
        causes.append('missing_or_invalid_identity_report')
    elif not identity.get('identity_independently_verified'):
        if identity.get('overlap_observations', 0) < 3:
            causes.append('insufficient_overlap_evidence')
        phases = identity.get('phase_counts', {})
        for phase in ('pre', 'post'):
            if phases.get(phase, {}).get('tracked_vehicle', 0) < 10:
                causes.append(phase + '_identity_evidence_insufficient')
        if identity.get('matched_truth_fraction', 0) < 0.9:
            causes.append('matched_truth_insufficient')
        if identity.get('wrong_identity_observations', 0):
            causes.append('wrong_identity_observations')
        causes.extend(identity.get('errors', []))
        if not any(cause in causes for cause in (
                'insufficient_overlap_evidence', 'pre_identity_evidence_insufficient',
                'post_identity_evidence_insufficient', 'matched_truth_insufficient',
                'wrong_identity_observations')) and not identity.get('errors'):
            causes.append('identity_not_verified')
    return list(dict.fromkeys(causes))


def inspect_study(directory):
    directory = Path(directory).resolve()
    summary = load_json(directory / 'study_summary.json') or {}
    plan = load_json(directory / 'plan.json') or []
    status = load_json(directory / 'study_status.json') or {}
    manifest = load_json(directory / 'freeze_manifest.json') or {}
    provenance = load_json(directory / 'repeat_provenance.json') or {}
    ab_protocol = load_json(directory / 'ab_protocol.json') or {}
    audit = load_json(directory / 'px4_parameter_audit.json') or {}
    rows = summary.get('trials', [])
    errors, results, counts, pids = [], [], Counter(), []
    expected_names = [row['name'] for row in plan]
    actual_names = [row['name'] for row in rows]
    if not plan or actual_names != expected_names[:len(rows)] or len(set(actual_names)) != len(rows):
        errors.append('plan_or_trial_order_invalid')
    finished = bool(plan and actual_names == expected_names and status.get('completed')
                    and not status.get('error') and not status.get('interrupted')
                    and not status.get('active_trial'))
    if not finished:
        errors.append('batch_incomplete')
    if status.get('attempted') != len(rows) or status.get('planned') != len(plan):
        errors.append('status_count_mismatch')
    runtime = (directory / 'frozen_files' if ab_protocol else
               Path(provenance['runtime']) if provenance.get('runtime') else directory / 'runtime')
    if not manifest.get('source_sha256'):
        errors.append('missing_freeze_manifest')
    for name, checksum in manifest.get('source_sha256', {}).items():
        path = runtime / name
        if not path.is_file() or digest(path) != checksum:
            errors.append('frozen_source_mismatch:' + name)
    # Historical helpers are checked against their archived copies, not new tools.
    for name, checksum in provenance.get('reporting_helper_sha256', {}).items():
        path = directory / 'reporting_helpers' / Path(name).name
        if not path.is_file() or digest(path) != checksum:
            errors.append('archived_helper_mismatch:' + name)
    for name, checksum in ab_protocol.get('helper_sha256', {}).items():
        path = directory / 'reporting_helpers' / name
        if not path.is_file() or digest(path) != checksum:
            errors.append('archived_helper_mismatch:' + name)
    source = runtime / 'ros2_ws/src/uav_learning/uav_learning'
    installed = (directory / 'installed_snapshot' if ab_protocol else
                 runtime / 'ros2_ws/install/uav_learning/lib/python3.12/site-packages/uav_learning')
    for path in source.glob('*.py'):
        other = installed / path.name
        if not other.is_file() or digest(path) != digest(other):
            errors.append('installed_module_mismatch:' + path.name)
    known_logs = {row['directory']: row for row in audit.get('trials', [])}
    for row in rows:
        trial_dir = Path(row['directory'])
        report = load_json(trial_dir / 'report.json')
        identity = load_json(trial_dir / 'identity_report.json')
        supervisor = load_json(trial_dir / 'supervisor.json') or {}
        snapshot = load_json(trial_dir / 'implementation_snapshot.json') or {}
        causes = failure_causes(report, identity)
        if supervisor.get('error'):
            causes.append('supervisor_error:' + supervisor['error'])
        if row.get('returncode', 0) != 0:
            causes.append('supervisor_exit_' + str(row['returncode']))
        counts.update(causes)
        if not report or not identity:
            errors.append('missing_trial_report:' + row['name'])
        if not snapshot.get('source_sha256'):
            errors.append('missing_trial_snapshot:' + row['name'])
        for name, checksum in snapshot.get('source_sha256', {}).items():
            if checksum != manifest.get('source_sha256', {}).get(name):
                errors.append('trial_source_mismatch:' + row['name'] + ':' + name)
        if snapshot.get('model_sha256') != manifest.get('source_sha256', {}).get('yolo11s.pt'):
            errors.append('trial_model_mismatch:' + row['name'])
        if not all(supervisor.get(key) for key in ('freeze_verified', 'parameters_verified')):
            errors.append('trial_runtime_not_verified:' + row['name'])
        if not (trial_dir / 'runtime_parameters.json').is_file():
            errors.append('missing_runtime_parameters:' + row['name'])
        archive = trial_dir / 'flight.ulg'
        recorded = known_logs.get(str(trial_dir), {})
        if (not recorded.get('available') or not archive.is_file()
                or digest(archive) != recorded.get('ulog_sha256')):
            errors.append('ulog_missing_or_hash_mismatch:' + row['name'])
        text_path = directory / (row['name'] + '_supervisor.log')
        match = re.search(r'Started px4: PID (\d+)', text_path.read_text(errors='replace')) if text_path.is_file() else None
        if match:
            pids.append(int(match.group(1)))
        else:
            errors.append('px4_start_not_recorded:' + row['name'])
        flight_pass = bool(report and report.get('passed') and supervisor.get('autonomous_passed')
                           and not supervisor.get('error') and row.get('returncode', 0) == 0)
        identity_pass = bool(identity and identity.get('identity_independently_verified'))
        strict_pass = flight_pass and identity_pass
        if row.get('success') != strict_pass:
            errors.append('summary_success_mismatch:' + row['name'])
        results.append({'name': row['name'], 'flight_pass': flight_pass,
                        'identity_verified': identity_pass, 'strict_pass': strict_pass,
                        'failure_causes': causes})
    if len(set(pids)) != len(pids):
        errors.append('duplicate_px4_pid')
    return {'directory': str(directory), 'planned': len(plan), 'attempted': len(rows),
            'all_attempts_finished': finished, 'evidence_complete': not errors,
            'attempt_evidence_complete': not any(error != 'batch_incomplete' for error in errors),
            'integrity_errors': errors, 'unique_px4_starts': len(set(pids)),
            'flight_passes': sum(row['flight_pass'] for row in results),
            'identity_verified': sum(row['identity_verified'] for row in results),
            'strict_passes': sum(row['strict_pass'] for row in results),
            'failure_counts': dict(counts), 'trials': results,
            'limitation': 'Evidence integrity is not task success. Failed attempts remain in the denominator; '
                          'historical copies are checked independently of current development helpers.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--output', type=Path, help='New external JSON file; never overwrite existing evidence.')
    args = parser.parse_args()
    if args.output and (args.output.exists() or args.output.resolve().is_relative_to(args.study.resolve())):
        parser.error('--output must be a new file outside the study directory.')
    result = inspect_study(args.study)
    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, indent=2))
    return 0 if result['evidence_complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
