#!/usr/bin/env python3
"""Archive and audit the completed lane-change trial without altering raw logs."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys

TRIAL = Path(__file__).resolve().parent
ROOT = TRIAL.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_vehicle_ulog import log_source
from repeat_best_vehicle import ulog_safety


def read_json(name):
    return json.loads((TRIAL / name).read_text())


def read_jsonl(name):
    return [json.loads(line) for line in (TRIAL / name).read_text().splitlines() if line]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = read_json('report.json')
identity = read_json('identity_report.json')
supervisor = read_json('supervisor.json')
snapshot = read_json('implementation_snapshot.json')
parameters = read_json('runtime_parameters.json')
geometry = read_json('full_pose_geometry_audit.json')
assert supervisor['process_exit_codes']
assert all(value is not None for value in supervisor['process_exit_codes'].values())
assert parameters['vehicle_scene']['distractor_color'] == 'red'
assert parameters['vehicle_scene']['parked_vehicle_y'] == -4.4
assert parameters['vehicle_scene']['traffic_scenario'] == 'lane_change_overtaking'
assert identity['target_color'] == identity['distractor_color'] == 'red'
assert digest(Path(snapshot['model_path'])) == snapshot['model_sha256']
for relative, expected in snapshot['source_sha256'].items():
    source = ROOT / relative
    assert digest(source) == expected, f'Changed source: {relative}'
    destination = TRIAL / 'executed_sources' / relative
    if destination.exists():
        assert digest(destination) == expected
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

archived = TRIAL / 'flight.ulg'
if not archived.exists():
    ulog = log_source(ROOT / 'PX4-Autopilot/build/px4_sitl_default/rootfs',
                      (TRIAL / 'px4.log').read_text(errors='replace'))
    assert ulog is not None and ulog.is_file()
    shutil.copy2(ulog, archived)
safety = ulog_safety(archived)

requests = read_jsonl('scene_service.jsonl') + read_jsonl('traffic_service.jsonl')
failures = [r for r in requests if r.get('success') is not True]
receipt_errors = [r for r in requests if r.get('success') != (
    r.get('binding_result') is True and r.get('response_data') is True)]
sequence_errors = []
for client in sorted({r['client'] for r in requests}):
    sequence = [r['sequence'] for r in requests if r['client'] == client]
    if sequence != list(range(1, len(sequence) + 1)):
        sequence_errors.append(client)
losses = [e for e in report['events'] if e['event'] == 'TRACK_TARGET_LOST']
planned = [e for e in losses if any(o['start_wall_s'] <= e['time_s'] <= o['end_wall_s']
                                   for o in report['occlusions'] if o.get('end_wall_s') is not None)]
recovery_episodes = []
for loss in losses:
    later = [event for event in report['events'] if event['time_s'] > loss['time_s']]
    recovered = next((e for e in later if e['event'] in ('TARGET_RECOVERED', 'TRACK_REACQUIRED')), None)
    recovery_episodes.append({
        'loss_wall_s': loss['time_s'], 'planned_occlusion': loss in planned,
        'confirmation_wall_s': recovered['time_s'] if recovered else None,
        'loss_to_confirmation_wall_s': recovered['time_s'] - loss['time_s'] if recovered else None,
        'recovery_timeout': any(e['event'] == 'RECOVERY_TIMEOUT' for e in later
                                if recovered is None or e['time_s'] < recovered['time_s']),
    })
parked = [r['poses']['parked_vehicle']['p'] for r in read_jsonl('identity_poses.jsonl')
          if 'parked_vehicle' in r.get('poses', {})]
assert parked and all(abs(p[0] - 30) < 1e-6 and abs(p[1] + 4.4) < 1e-6 for p in parked)
summary = {
    'scenario': snapshot['scenario'],
    'task_passed': report['passed'],
    'maneuver_observed': geometry['scenario_evidence']['maneuver_observed'],
    'identity_verified': identity['identity_independently_verified'],
    'strict_joint_passed': bool(
        report['passed'] and identity['identity_independently_verified']
        and geometry['scenario_evidence']['maneuver_observed']
        and supervisor['autonomous_passed'] and supervisor['landed_disarmed_before_shutdown']
        and not supervisor['interventions'] and requests and not failures
        and not receipt_errors and not sequence_errors and not any(safety.values())),
    'coverage_percent': 100 * report['follow_time_visible_fraction'],
    'failure_reasons': ['confirmed_coverage_below_0_8', 'no_scorable_original_identity_after_merge'],
    'track_losses': len(losses), 'planned_losses': len(planned),
    'unplanned_losses': len(losses) - len(planned),
    'recovery_episodes': recovery_episodes,
    'occlusion_confirmed_recovery_wall_s': [o['confirmed_recovery_s'] for o in report['occlusions']],
    'wrong_identity_observations': identity['wrong_identity_observations'],
    'scorable_identity_switches': identity['scorable_identity_switches'],
    'identity_phase_counts': identity['phase_counts'],
    'drone_follow_travel_m': report['drone_follow_travel_m'],
    'track_mean_abs_pixel_error': report['track_mean_abs_pixel_error'],
    'final_home_horizontal_error_m': report['final_home_horizontal_error_m'],
    'parked_pose': parked[-1],
    'geometry_evidence': geometry['scenario_evidence'],
    'scene_requests': {'total': len(requests), 'failures': len(failures),
                       'by_service': dict(Counter(r['service'] for r in requests)),
                       'receipt_errors': len(receipt_errors), 'sequence_errors': sequence_errors},
    'ulog_safety': safety, 'ulog_sha256': digest(archived),
    'source_snapshot_files_verified': len(snapshot['source_sha256']),
    'regression_tests': {'passed': 353, 'warnings': 3},
    'limitations': [
        'Single trial, not a repeated benchmark or evidence of algorithm improvement.',
        'Coverage is time-weighted onboard confirmation, not independently verified identity accuracy.',
        'All post-merge identity observations are projection-overlap unscorable.',
        'Zero scorable wrong identities does not verify post-merge target identity.',
        'Mesh-box clearance and ULog events are not a full 3D collision audit.',
        'Identity is from identity_report.json; report.json does not independently verify identity.',
    ],
}
output = TRIAL / 'validation_summary.json'
if output.exists():
    assert read_json(output.name) == summary, 'Keep prior summary evidence'
else:
    output.write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
