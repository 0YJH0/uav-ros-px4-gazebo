#!/usr/bin/env python3
"""Reassess recorded identity evidence without changing a completed flight."""

import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil

import vehicle_crossing_validation as evaluator

ROOT = Path(__file__).resolve().parents[1]
MASKED_LABELS = {'missing_matched_truth', 'unexpected_camera_frame',
                 'panel_occlusion_unscorable'}
SOURCE_FILES = ('scripts/reassess_vehicle_identity.py',
                'scripts/vehicle_crossing_validation.py', 'scripts/vehicle_lane_change.py')
INPUT_FILES = ('identity_observations.jsonl', 'identity_report.json', 'crossing_events.jsonl',
               'validation_summary.json', 'report.json', 'supervisor.json',
               'scene_service.jsonl', 'traffic_service.jsonl', 'flight.ulg',
               'implementation_snapshot.json')


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load_json(path):
    return json.loads(path.read_text()) if path.is_file() else {}


def load_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def reclassify(rows):
    result = []
    for original in rows:
        row = dict(original)
        row.update(original_label=original.get('label'), original_scores=original.get('scores'))
        if original.get('label') in MASKED_LABELS:
            row['reassessment_status'] = 'preserved_masked_or_unmatched'
        elif 'accepted_box' not in original or not isinstance(original.get('projected_boxes'), dict):
            row.update(label='projection_unscorable', scores={}, reason='missing_frozen_geometry',
                       reassessment_status='unscorable_missing_geometry')
        else:
            row.update(evaluator.evaluate_identity(original['accepted_box'], original['projected_boxes']))
            row['reassessment_status'] = 'reassessed'
        result.append(row)
    return result


def gate(checks):
    if any(value is False for value in checks):
        return 'fail'
    return 'pass' if checks and all(value is True for value in checks) else 'unknown'


def eq(data, key, value):
    return data[key] == value if key in data else None


def service_audit(trial):
    audit = {}
    for client in ('scene', 'traffic'):
        path = trial / (client + '_service.jsonl')
        if not path.is_file():
            audit[client] = {'status': 'unknown', 'reason': 'missing_receipts'}
            continue
        rows = load_rows(path)
        sequences = [row.get('sequence') for row in rows]
        valid = bool(rows) and all(type(value) is int and value > 0 for value in sequences)
        receipts = [gate([row.get(key) for key in ('success', 'binding_result', 'response_data')])
                    for row in rows]
        if valid:
            missing = sorted(set(range(1, max(sequences) + 1)) - set(sequences))
            duplicates = sorted(value for value, count in Counter(sequences).items() if count > 1)
        else:
            missing, duplicates = [], []
        complete = valid and not missing and not duplicates and sequences == sorted(sequences)
        audit[client] = {
            'status': 'fail' if 'fail' in receipts else 'pass' if complete and
                      all(status == 'pass' for status in receipts) else 'unknown',
            'records': len(rows), 'first_sequence': sequences[0] if valid else None,
            'last_sequence': sequences[-1] if valid else None,
            'missing_sequences': missing, 'duplicate_sequences': duplicates,
            'failed_receipts': receipts.count('fail'), 'unknown_receipts': receipts.count('unknown'),
        }
    return audit


def scenario_observed(identity):
    scenario = identity['traffic_scenario']
    checks = [identity.get('traffic_started'), identity.get('traffic_completed')]
    if scenario == 'crossing':
        overlap = identity.get('overlap_observations')
        checks.append(overlap >= 3 if overlap is not None else None)
    elif scenario == 'lane_change_overtaking':
        checks.extend([identity.get('overtaking_observed'),
                       (identity.get('lane_change') or {}).get('maneuver_observed')])
    elif scenario == 'overtaking':
        clearance = identity.get('minimum_world_lateral_clearance_m')
        checks.extend([identity.get('overtaking_observed'), clearance >= .5 if clearance is not None else None])
    else:
        return None
    return {'pass': True, 'fail': False, 'unknown': None}[gate(checks)]


def joint_checks(report, validation, supervisor, identity, original_identity, service, hashes):
    original_scenario = (validation['maneuver_observed'] if 'maneuver_observed' in validation else
                         scenario_observed(original_identity))
    safety = validation.get('ulog_safety', {})
    requests = validation.get('scene_requests', {})
    receipt_statuses = [row['status'] for row in service.values()]
    services = ('fail' if 'fail' in receipt_statuses or requests.get('failures', 0) > 0 or
                requests.get('receipt_errors', 0) > 0 else
                'pass' if all(status == 'pass' for status in receipt_statuses) and
                requests.get('total', 0) > 0 and requests.get('failures') == 0 and
                requests.get('receipt_errors') == 0 and requests.get('sequence_errors') == [] else 'unknown')
    recorded_hash = validation.get('ulog_sha256')
    ulog_matches = (hashes.get('flight.ulg') == recorded_hash
                    if recorded_hash and 'flight.ulg' in hashes else None)
    return {
        'task': gate([report.get('passed'), validation.get('task_passed')]),
        'identity': gate([identity.get('identity_independently_verified')]),
        'scenario': gate([original_scenario, scenario_observed(identity)]),
        'supervision': gate([eq(supervisor, 'error', None), eq(supervisor, 'interventions', []),
                             supervisor.get('landed_disarmed_before_shutdown'),
                             supervisor.get('parameters_verified')]),
        'services': services,
        'recorded_safety': gate([eq(safety, key, 0) for key in (
            'armed_failsafe_observations', 'armed_offboard_lost_observations', 'ulog_dropout_events')]
            + [eq(report, 'failsafe_observed', False), ulog_matches]),
    }


def reassess(trial, output):
    trial, output = Path(trial).resolve(), Path(output).resolve()
    if output.exists() or output == trial or output.is_relative_to(trial):
        raise ValueError('Output must be a new directory outside the original trial.')
    hashes = {name: digest(trial / name) for name in INPUT_FILES if (trial / name).is_file()}
    rows = load_rows(trial / 'identity_observations.jsonl')
    original_identity = load_json(trial / 'identity_report.json')
    if not original_identity or 'errors' not in original_identity or 'traffic_scenario' not in original_identity:
        raise ValueError('Original identity report must retain scenario and errors.')
    events = load_rows(trial / 'crossing_events.jsonl')
    validation = load_json(trial / 'validation_summary.json')
    report = load_json(trial / 'report.json')
    supervisor = load_json(trial / 'supervisor.json')
    updated = reclassify(rows)
    errors = list(original_identity['errors'])
    if any(row['reassessment_status'] == 'unscorable_missing_geometry' and
           row['original_label'] in ('crossing_vehicle', 'parked_vehicle') for row in updated):
        errors.append('unreassessed_wrong_identity_evidence')
    identity = evaluator.identity_summary(updated, events, errors,
        original_identity['traffic_scenario'], original_identity.get('distractor_color', 'auto'))
    service = service_audit(trial)
    checks = joint_checks(report, validation, supervisor, identity, original_identity, service, hashes)
    changes = Counter(f"{old.get('label')} -> {new.get('label')}"
                      for old, new in zip(rows, updated) if old.get('label') != new.get('label'))
    comparison = {
        'trial': str(trial), 'identity_evaluation_version': identity.get('identity_evaluation_version'),
        'evaluation_only': True, 'new_flight': False, 'tracking_performance_changed': False,
        'original_identity_verified': original_identity.get('identity_independently_verified'),
        'reassessed_identity_verified': identity['identity_independently_verified'],
        'original_phase_counts': original_identity.get('phase_counts'),
        'reassessed_phase_counts': identity['phase_counts'],
        'label_changes': dict(changes), 'changed_observations': sum(changes.values()),
        'observation_handling': dict(Counter(row['reassessment_status'] for row in updated)),
        'onboard_accepted_boxes_before': sum(row.get('accepted_box') is not None for row in rows),
        'onboard_accepted_boxes_after': sum(row.get('accepted_box') is not None for row in updated),
        'task_passed': report.get('passed'), 'recorded_task_passed': validation.get('task_passed'),
        'coverage_percent': report.get('follow_time_visible_fraction') * 100
                            if report.get('follow_time_visible_fraction') is not None else None,
        'recorded_coverage_percent': validation.get('coverage_percent'),
        'recorded_failure_reasons': validation.get('failure_reasons'),
        'recorded_safety': validation.get('ulog_safety'),
        'recorded_scene_requests': validation.get('scene_requests'),
        'service_receipt_audit': service,
        'recorded_supervisor': supervisor,
        'joint_check_status': checks,
        'strict_joint_passed': all(status == 'pass' for status in checks.values()),
        'strict_failure_reasons': [f'{name}_{status}' for name, status in checks.items() if status != 'pass'],
        'input_sha256': hashes,
        'missing_inputs': [name for name in INPUT_FILES if name not in hashes],
        'source_sha256': {name: digest(ROOT / name) for name in SOURCE_FILES},
        'dependencies': {name: importlib.metadata.version(name) for name in ('numpy', 'scipy')},
        'limitations': [
            'This changes only evaluation criteria; it is not a new flight or tracking-performance improvement.',
            'Original task, coverage, service and safety evidence is retained, not repaired by identity reassessment.',
            'Safety counters are from the recorded audit; the retained ULog hash is checked, not parsed again.',
            'Missing receipts, masked frames and unavailable truth remain missing evidence, not successful observations.',
            'Bounding-volume evidence is not per-pixel identity ground truth or a complete collision audit.',
        ],
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, expected in comparison['source_sha256'].items():
        destination = output / 'evaluation_sources' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, destination)
        if digest(destination) != expected:
            raise RuntimeError('Evaluation source changed during snapshot: ' + name)
    with (output / 'identity_observations.jsonl').open('x') as stream:
        for row in updated:
            stream.write(json.dumps(row, allow_nan=False) + '\n')
    final_hashes = {name: digest(trial / name) for name in INPUT_FILES if (trial / name).is_file()}
    changed = [name for name in INPUT_FILES if hashes.get(name) != final_hashes.get(name)]
    if changed:
        raise RuntimeError('Trial input changed during reassessment: ' + ', '.join(changed))
    write_json(output / 'identity_report.json', identity)
    write_json(output / 'comparison.json', comparison)
    return comparison


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trial', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    comparison = reassess(args.trial, args.output)
    print(json.dumps({key: comparison[key] for key in (
        'original_identity_verified', 'reassessed_identity_verified', 'coverage_percent',
        'joint_check_status', 'strict_joint_passed', 'strict_failure_reasons')}, indent=2))


if __name__ == '__main__':
    main()
