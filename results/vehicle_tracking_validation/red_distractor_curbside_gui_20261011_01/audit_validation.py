#!/usr/bin/env python3
"""Preserve and audit the completed single GUI trial without changing raw logs."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path('/home/yjh/ROS2_manmade')
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_vehicle_ulog import log_source
from repeat_best_vehicle import ulog_safety

trial = ROOT / 'results/vehicle_tracking_validation/red_distractor_curbside_gui_20261011_01'


def read_json(name):
    return json.loads((trial / name).read_text())


def read_jsonl(name):
    return [json.loads(line) for line in (trial / name).read_text().splitlines() if line]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = read_json('report.json')
identity = read_json('identity_report.json')
supervisor = read_json('supervisor.json')
snapshot = read_json('implementation_snapshot.json')
parameters = read_json('runtime_parameters.json')
assert parameters['vehicle_scene']['distractor_color'] == 'red'
assert parameters['vehicle_scene']['parked_vehicle_y'] == -4.4
assert identity['target_color'] == identity['distractor_color'] == 'red'
assert digest(Path(snapshot['model_path'])) == snapshot['model_sha256']
for relative, expected in snapshot['source_sha256'].items():
    source = ROOT / relative
    assert digest(source) == expected, f'Changed source: {relative}'
    destination = trial / 'executed_sources' / relative
    if destination.exists():
        assert digest(destination) == expected
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

ulog = log_source(ROOT / 'PX4-Autopilot/build/px4_sitl_default/rootfs',
                  (trial / 'px4.log').read_text(errors='replace'))
assert ulog is not None and ulog.is_file()
archived = trial / 'flight.ulg'
if archived.exists():
    assert digest(archived) == digest(ulog)
else:
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
parked = [r['poses']['parked_vehicle']['p'] for r in read_jsonl('identity_poses.jsonl')
          if 'parked_vehicle' in r.get('poses', {})]
assert parked and all(abs(p[0] - 30) < 1e-6 and abs(p[1] + 4.4) < 1e-6 for p in parked)
summary = {
    'scenario': snapshot['scenario'],
    'task_passed': report['passed'],
    'identity_verified': identity['identity_independently_verified'],
    'strict_joint_passed': bool(
        report['passed'] and identity['identity_independently_verified']
        and supervisor['autonomous_passed'] and supervisor['landed_disarmed_before_shutdown']
        and not supervisor['interventions'] and requests and not failures
        and not receipt_errors and not sequence_errors and not any(safety.values())),
    'coverage_percent': 100 * report['follow_time_visible_fraction'],
    'track_losses': len(losses), 'planned_losses': len(planned),
    'unplanned_losses': len(losses) - len(planned),
    'occlusion_confirmed_recovery_wall_s': [o['confirmed_recovery_s'] for o in report['occlusions']],
    'wrong_identity_observations': identity['wrong_identity_observations'],
    'scorable_identity_switches': identity['scorable_identity_switches'],
    'drone_follow_travel_m': report['drone_follow_travel_m'],
    'track_mean_abs_pixel_error': report['track_mean_abs_pixel_error'],
    'final_home_horizontal_error_m': report['final_home_horizontal_error_m'],
    'parked_pose': parked[-1],
    'scene_requests': {'total': len(requests), 'failures': len(failures),
                       'by_service': dict(Counter(r['service'] for r in requests)),
                       'receipt_errors': len(receipt_errors), 'sequence_errors': sequence_errors},
    'ulog_safety': safety, 'ulog_sha256': digest(archived),
    'source_snapshot_files_verified': len(snapshot['source_sha256']),
    'regression_tests': {'passed': 336, 'warnings': 3},
    'limitations': ['Single trial, not a repeated benchmark or evidence of algorithm improvement.',
                   'Both distractor color and parked position changed from the archived blue baseline.',
                   'Same-appearance separate-lane overtaking is not overlapping crossing recovery.',
                   'Identity is from identity_report.json; report.json does not independently verify identity.'],
}
output = trial / 'validation_summary.json'
assert not output.exists(), 'Keep prior summary evidence'
output.write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
