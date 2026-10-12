#!/usr/bin/env python3
"""Audit one completed trial and archive evidence without altering raw logs."""

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys

import numpy as np

TRIAL = Path(__file__).resolve().parent
ROOT = TRIAL.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_vehicle_ulog import log_source
from repeat_best_vehicle import ulog_safety


def read_json(name):
    return json.loads((TRIAL / name).read_text())


def read_jsonl(name):
    with (TRIAL / name).open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def copy_verified(source, destination, expected=None):
    expected = expected or digest(source)
    if digest(source) != expected:
        raise RuntimeError(f'Source changed since execution snapshot: {source}')
    if destination.exists():
        if digest(destination) != expected:
            raise RuntimeError(f'Existing archive differs; preserving it: {destination}')
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return expected


def distribution(values):
    values = [float(value) for value in values
              if value is not None and math.isfinite(float(value))]
    if not values:
        return {'count': 0, 'mean_s': None, 'p95_s': None, 'maximum_s': None}
    return {'count': len(values), 'mean_s': float(np.mean(values)),
            'p95_s': float(np.percentile(values, 95)), 'maximum_s': max(values)}


def main():
    supervisor = read_json('supervisor.json')
    exits = supervisor.get('process_exit_codes', {})
    if not exits or any(value is None for value in exits.values()):
        raise RuntimeError('Wait for all simulator processes to exit before final auditing')
    report = read_json('report.json')
    identity = read_json('identity_report.json')
    snapshot = read_json('implementation_snapshot.json')
    parameters = read_json('runtime_parameters.json')
    geometry = read_json('full_pose_geometry_audit.json')
    causes = []
    reference = TRIAL.parent / 'overlap_scale_gui_20261011_01/runtime_parameters.json'
    baseline_parameters = json.loads(reference.read_text())
    parameter_differences = []
    for node in sorted(set(baseline_parameters) | set(parameters)):
        before, after = baseline_parameters.get(node, {}), parameters.get(node, {})
        for name in sorted(set(before) | set(after)):
            if before.get(name) != after.get(name) or (name in before) != (name in after):
                parameter_differences.append({'node': node, 'parameter': name,
                                              'before_present': name in before,
                                              'before': before.get(name), 'after': after.get(name)})
    expected_additions = {'overlap_confirmation_continuity'}
    comparable_parameters = (len(parameter_differences) == 1 and all(
        item['node'] == 'perception_node' and item['parameter'] in expected_additions
        and not item['before_present'] and item['after'] is True
        for item in parameter_differences))
    if not comparable_parameters:
        causes.append('unexpected_parameter_difference_from_reference')

    required_parameters = {
        'perception_node': {'overlap_candidate_recovery': True, 'bounded_scale_prediction': True,
                            'overlap_confirmation_continuity': True, 'target_reacquire_timeout': 10.0},
        'px4_offboard_controller': {'recovery_timeout': 10.0, 'recovery_max_distance': 4.0,
                                   'recovery_max_speed': .8},
        'vehicle_scene': {'distractor_color': 'red', 'parked_vehicle_y': -4.4,
                          'traffic_scenario': 'lane_change_overtaking', 'vehicle_speed': .8,
                          'occlusion_start': 15.0, 'occlusion_duration': 4.0},
    }
    parameter_errors = []
    for node, expected in required_parameters.items():
        for name, value in expected.items():
            actual = parameters.get(node, {}).get(name)
            if actual != value or (isinstance(value, bool) and not isinstance(actual, bool)):
                parameter_errors.append({'node': node, 'parameter': name,
                                         'expected': value, 'actual': actual})
    if parameter_errors:
        causes.append('runtime_parameters_not_as_requested')
    if identity.get('target_color') != 'red' or identity.get('distractor_color') != 'red':
        causes.append('identity_scene_color_mismatch')
    if identity.get('identity_evaluation_version') != 'exclusive_projection_v2':
        causes.append('independent_identity_evaluation_version_not_v2')
    if not snapshot.get('source_sha256'):
        raise RuntimeError('Missing executed-source hashes')
    if digest(Path(snapshot['model_path'])) != snapshot['model_sha256']:
        raise RuntimeError('Model changed since execution snapshot')
    for relative, expected in snapshot['source_sha256'].items():
        copy_verified(ROOT / relative, TRIAL / 'executed_sources' / relative, expected)
    copy_verified(Path('/tmp/audit_lane_change_poses.py'), TRIAL / 'audit_lane_change_poses.py',
                  geometry['audit_script_sha256'])

    archived = TRIAL / 'flight.ulg'
    source_ulog = log_source(ROOT / 'PX4-Autopilot/build/px4_sitl_default/rootfs',
                             (TRIAL / 'px4.log').read_text(errors='replace'))
    if source_ulog is None or not source_ulog.is_file():
        raise RuntimeError('Cannot find the flight ULog named by this trial')
    ulog_sha256 = copy_verified(source_ulog, archived)
    safety = ulog_safety(archived)

    requests = []
    request_files = {}
    for name in ('scene_service.jsonl', 'traffic_service.jsonl'):
        records = read_jsonl(name)
        request_files[name] = {'rows': len(records), 'sha256': digest(TRIAL / name)}
        requests.extend(records)
        if not records:
            causes.append('empty_service_receipts:' + name)
    failures = [row for row in requests if row.get('success') is not True]
    receipt_errors = [row for row in requests if row.get('success') != (
        row.get('binding_result') is True and row.get('response_data') is True)]
    sequence_errors, sequences = [], {}
    for client in sorted({row['client'] for row in requests}):
        values = [row['sequence'] for row in requests if row['client'] == client]
        duplicate = sorted(value for value, count in Counter(values).items() if count > 1)
        missing = sorted(set(range(1, max(values) + 1)) - set(values))
        sequences[client] = {'count': len(values), 'first': values[0], 'last': values[-1],
                             'missing': missing, 'duplicates': duplicate,
                             'increasing': all(b > a for a, b in zip(values, values[1:]))}
        if values != list(range(1, len(values) + 1)):
            sequence_errors.append(client)
    for condition, cause in ((bool(failures), 'scene_service_requests_failed'),
                              (bool(receipt_errors), 'service_receipt_semantics_mismatch'),
                              (bool(sequence_errors), 'service_receipt_sequence_incomplete')):
        if condition:
            causes.append(cause)

    for field in ('completed', 'track_complete_event', 'landed', 'disarmed'):
        if not report.get(field):
            causes.append(field + '_not_confirmed')
    for field, cutoff, cause in (
            ('follow_time_visible_fraction', .8, 'confirmed_coverage_below_0_8'),
            ('track_detection_fraction', .8, 'track_detection_fraction_below_0_8')):
        if report.get(field) is None or report[field] < cutoff:
            causes.append(cause)
    for field in ('vehicle_travel_m', 'drone_track_travel_m'):
        if report.get(field) is None or report[field] <= 1.:
            causes.append(field + '_insufficient')
    home = report.get('final_home_horizontal_error_m')
    if home is None or home > 1.:
        causes.append('home_error_missing_or_above_1_m')
    if report.get('occlusions') and not report.get('occlusion_recovery_passed'):
        causes.append('planned_occlusion_criteria_not_met')
    if not report.get('passed'):
        causes.append('task_not_passed')
    if report.get('failsafe_observed'):
        causes.append('px4_failsafe_observed')
    for name, count in safety.items():
        if count:
            causes.append(name)
    if not identity.get('identity_independently_verified'):
        causes.append('independent_identity_not_verified')
        for phase in ('pre', 'post'):
            if identity.get('phase_counts', {}).get(phase, {}).get('tracked_vehicle', 0) < 10:
                causes.append(phase + '_identity_evidence_insufficient')
    if identity.get('wrong_identity_observations', 0):
        causes.append('wrong_identity_observations')
    causes.extend(identity.get('errors', []))
    if not geometry['scenario_evidence'].get('maneuver_observed'):
        causes.append('lane_change_maneuver_not_verified')
    if not supervisor.get('autonomous_passed'):
        causes.append('supervisor_autonomous_not_passed')
    if not supervisor.get('landed_disarmed_before_shutdown'):
        causes.append('not_landed_and_disarmed_before_shutdown')
    if supervisor.get('interventions'):
        causes.append('supervisor_intervention')
    if supervisor.get('error'):
        causes.append('supervisor_error:' + supervisor['error'])

    losses = [event for event in report['events'] if event['event'] == 'TRACK_TARGET_LOST']
    recovery_episodes = []
    for loss in losses:
        planned = any(occlusion['start_wall_s'] <= loss['time_s'] <= occlusion['end_wall_s']
                      for occlusion in report['occlusions'] if occlusion.get('end_wall_s') is not None)
        later = [event for event in report['events'] if event['time_s'] > loss['time_s']]
        recovered = next((event for event in later
                          if event['event'] in ('TARGET_RECOVERED', 'TRACK_REACQUIRED')), None)
        recovery_episodes.append({
            'loss_wall_s': loss['time_s'], 'planned_occlusion': planned,
            'confirmation_wall_s': recovered['time_s'] if recovered else None,
            'loss_to_confirmation_wall_s': recovered['time_s'] - loss['time_s'] if recovered else None,
            'recovery_timeout': any(event['event'] == 'RECOVERY_TIMEOUT' for event in later
                                    if recovered is None or event['time_s'] < recovered['time_s']),
        })
    associations = read_jsonl('association.jsonl')
    frame_stamps = [(row['stamp']['sec'], row['stamp']['nanosec']) for row in associations]
    duplicate_stamps = len(frame_stamps) - len(set(frame_stamps))
    non_increasing = sum(before >= after for before, after in zip(frame_stamps, frame_stamps[1:]))
    if not associations or duplicate_stamps or non_increasing:
        causes.append('association_frame_stamp_integrity_failed')
    frame_evidence = {
        'records': len(associations), 'unique_image_stamps': len(set(frame_stamps)),
        'duplicate_image_stamps': duplicate_stamps, 'non_increasing_image_stamps': non_increasing,
        'first_image_stamp': list(frame_stamps[0]) if frame_stamps else None,
        'last_image_stamp': list(frame_stamps[-1]) if frame_stamps else None,
        'confirmed_frames': sum(row.get('identity_confirmed', False) for row in associations),
        'locked_tracker_ids': sorted({row['locked_track_id'] for row in associations
                                      if row.get('locked_track_id') is not None}),
        'frame_key': 'image stamp (sec, nanosec); tracker ID is not a frame ID',
    }
    timing = {field: distribution(row.get(field) for row in associations)
              for field in ('processing_s', 'target_publish_age_s', 'queue_wait_s')}
    timing['full_frame_yolo_s'] = distribution(
        row.get('detector', {}).get('full_frame_yolo_s') for row in associations)
    planned_count = sum(episode['planned_occlusion'] for episode in recovery_episodes)
    summary = {
        'scenario': snapshot['scenario'],
        'task_passed': report.get('passed', False),
        'maneuver_observed': geometry['scenario_evidence']['maneuver_observed'],
        'identity_verified': identity.get('identity_independently_verified', False),
        'identity_evaluation_version': identity.get('identity_evaluation_version'),
        'strict_joint_passed': not causes,
        'failure_reasons': list(dict.fromkeys(causes)),
        'coverage_percent': 100 * report['follow_time_visible_fraction'],
        'track_losses': len(losses), 'planned_losses': planned_count,
        'unplanned_losses': len(losses) - planned_count,
        'observation_gap_events': sum(event['event'] == 'TRACK_OBSERVATION_GAP' for event in report['events']),
        'recovery_episodes': recovery_episodes,
        'occlusion_confirmed_recovery_wall_s': [row.get('confirmed_recovery_s') for row in report['occlusions']],
        'wrong_identity_observations': identity['wrong_identity_observations'],
        'scorable_identity_switches': identity['scorable_identity_switches'],
        'identity_phase_counts': identity['phase_counts'],
        'identity_scorable_observations': identity['scorable_observations'],
        'identity_observations_total': identity['observations_total'],
        'drone_follow_travel_m': report['drone_follow_travel_m'],
        'track_mean_abs_pixel_error': report['track_mean_abs_pixel_error'],
        'track_p95_abs_pixel_error': report['track_p95_abs_pixel_error'],
        'final_home_horizontal_error_m': report['final_home_horizontal_error_m'],
        'geometry_evidence': geometry['scenario_evidence'],
        'scene_requests': {'total': len(requests), 'failures': len(failures),
                           'by_service': dict(Counter(row['service'] for row in requests)),
                           'receipt_errors': len(receipt_errors), 'sequence_errors': sequence_errors,
                           'client_sequences': sequences, 'files': request_files},
        'ulog_safety': safety, 'ulog_sha256': ulog_sha256,
        'source_snapshot_files_verified': len(snapshot['source_sha256']),
        'required_parameters': required_parameters, 'parameter_errors': parameter_errors,
        'parameter_comparison': {
            'reference': str(reference.relative_to(ROOT)), 'reference_sha256': digest(reference),
            'only_requested_continuity_addition': comparable_parameters,
            'differences': parameter_differences},
        'timing_all_recorded_associations': timing,
        'association_frame_integrity': frame_evidence,
        'input_sha256': {name: digest(TRIAL / name) for name in (
            'report.json', 'identity_report.json', 'supervisor.json', 'implementation_snapshot.json',
            'runtime_parameters.json', 'full_pose_geometry_audit.json', 'association.jsonl')},
        'audit_script_sha256': digest(Path(__file__).resolve()),
        'limitations': [
            'One independent restart, not a repeated benchmark or proof of general improvement.',
            'Only the continuity runtime flag is added, but trajectories and processing latency may differ between runs.',
            'Coverage is time-weighted onboard target confirmation, not detector mAP or verified identity accuracy.',
            'Partial-overlap identity scoring uses projected volumes and exclusive regions, not instance masks.',
            'Unscorable frames are not assumed to have correct identity; zero wrong identities applies to scored frames.',
            'Recovery durations use wall seconds; traffic phases and independent identity latency use simulation seconds.',
            'Mesh-box separation and ULog counters do not certify absence of all possible physical collisions.',
            'Timing statistics cover every recorded association, not just the TRACK state.',
            'Independent identity comes from identity_report.json, not the placeholder in report.json.',
        ],
    }
    output = TRIAL / 'validation_summary.json'
    if output.exists():
        if read_json(output.name) != summary:
            raise RuntimeError('Preserving existing differing validation_summary.json')
    else:
        output.write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    print(json.dumps(summary, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
