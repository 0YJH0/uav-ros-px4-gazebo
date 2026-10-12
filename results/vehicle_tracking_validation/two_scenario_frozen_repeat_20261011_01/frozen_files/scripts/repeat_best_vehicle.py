#!/usr/bin/env python3
"""Repeat the selected current overtaking pilot without modifying flight code."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

import numpy as np
from pyulog import ULog

from audit_vehicle_ulog import audit_studies
from repeat_frozen_crossing import completed_trial, compiled_px4_rootfs, verify_installed
from run_vehicle_tracking_validation import read_latest_sample
from vehicle_experiment_study import (METRICS, ROOT, digest, freeze, load_json,
                                      publish_summary, verify_freeze, write_json)
from vehicle_study_checks import failure_causes


def make_plan(count):
    if count < 1:
        raise ValueError('count must be positive')
    return [{'name': f'overtaking_{index:02d}', 'group': 'selected_overtaking',
             'vehicle_speed': .8, 'occlusion_start': 15., 'occlusion_duration': 4.,
             'crossing': False, 'overtaking': True, 'gui': True,
             'recovery_competition_enabled': False, 'predict_box_scale_velocity': True,
             'smooth_recovery_setpoints': False, 'cpu_inference_threads': 0,
             'detector_backend': 'torch'} for index in range(1, count+1)]


def verify_reference(reference):
    snapshot = load_json(reference / 'implementation_snapshot.json')
    if not snapshot or not snapshot.get('source_sha256'):
        raise RuntimeError('Reference implementation snapshot is required.')
    changed = [name for name, checksum in snapshot['source_sha256'].items()
               if not (ROOT / name).is_file() or digest(ROOT / name) != checksum]
    if changed or digest(Path(snapshot['model_path'])) != snapshot['model_sha256']:
        raise RuntimeError('Live implementation differs from selected pilot: ' + ', '.join(changed))
    for key, value in make_plan(1)[0].items():
        if key not in ('name', 'group') and snapshot['scenario'].get(key) != value:
            raise RuntimeError('Selected scenario differs: ' + key)
    return snapshot


def selected_row(target, trial, returncode):
    row = completed_trial(target, trial, returncode)
    report = load_json(target / 'report.json') or {}
    identity = load_json(target / 'identity_report.json') or {}
    supervisor = load_json(target / 'supervisor.json') or {}
    losses = [event['time_s'] for event in report.get('events', [])
              if event['event'] == 'TRACK_TARGET_LOST']
    panels = report.get('occlusions', [])
    temporal_planned = [stamp for stamp in losses if any(
        panel['start_wall_s'] <= stamp <= panel['end_wall_s']
        for panel in panels if panel.get('end_wall_s') is not None)]
    row['outside_panel_losses'] = len(losses) - len(temporal_planned) if report else None
    row['inside_panel_losses'] = len(temporal_planned) if report else None
    row['scene_update_errors'] = len(identity.get('errors', []))
    row['overtaking_observed'] = identity.get('overtaking_observed', False)
    row['minimum_world_lateral_clearance_m'] = identity.get('minimum_world_lateral_clearance_m')
    causes = failure_causes(report, identity)
    # Separate-lane overtaking does not require the old crossing-overlap criterion.
    causes = [cause for cause in causes if cause != 'insufficient_overlap_evidence']
    if not identity.get('overtaking_observed'):
        causes.append('overtaking_not_observed')
    clearance = identity.get('minimum_world_lateral_clearance_m')
    if clearance is None or clearance < .5:
        causes.append('overtaking_clearance_not_verified')
    if supervisor.get('error'):
        causes.append('supervisor_error:' + supervisor['error'])
    row['criteria_failure_causes'] = list(dict.fromkeys(causes))
    return row


def ulog_safety(path):
    ulog = ULog(str(path), message_name_filter_list=['vehicle_status', 'failsafe_flags'])
    status = ulog.get_dataset('vehicle_status').data
    flags = ulog.get_dataset('failsafe_flags').data
    indices = np.searchsorted(status['timestamp'], flags['timestamp'], side='right') - 1
    valid = indices >= 0
    indices = np.maximum(indices, 0)
    armed = status['arming_state'] == 2
    offboard = valid & armed[indices] & (status['nav_state'][indices] == 14)
    return {'armed_failsafe_observations': int(((status['failsafe'] != 0) & armed).sum()),
            'armed_offboard_lost_observations': int((offboard & (flags['offboard_control_signal_lost'] != 0)).sum()),
            'ulog_dropout_events': len(ulog.dropouts)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--count', type=int, default=10)
    args = parser.parse_args()
    plan = make_plan(args.count)
    directory, reference = args.output.resolve(), args.reference.resolve()
    if directory.exists():
        raise RuntimeError('Use a new study directory; failed attempts are never replaced.')
    snapshot = verify_reference(reference)
    verify_installed(ROOT)
    rootfs = compiled_px4_rootfs(ROOT / 'PX4-Autopilot/build/px4_sitl_default/bin/px4')
    directory.mkdir(parents=True)
    frozen = freeze(ROOT, directory, Path(snapshot['model_path']))
    # Enforce the actual selected launch parameters, including the overtaking scene.
    # This changes only experiment expectations, never the running node parameters.
    frozen['declared_parameters'] = load_json(reference / 'runtime_parameters.json')
    helpers = ('repeat_best_vehicle.py', 'repeat_frozen_crossing.py', 'audit_vehicle_ulog.py',
               'vehicle_study_checks.py', 'analyze_vehicle_framing.py', 'analyze_vehicle_latency.py',
               'vehicle_tracking_gui.config')
    for name in helpers:
        relative = 'scripts/' + name
        frozen['source_sha256'][relative] = digest(ROOT / relative)
        shutil.copy2(ROOT / relative, directory / 'frozen_files' / relative)
    write_json(directory / 'freeze_manifest.json', frozen)
    write_json(directory / 'plan.json', plan)
    shutil.copytree(reference / 'executed_sources', directory / 'reference_executed_sources')
    (directory / 'reference_evidence').mkdir()
    for name in ('report.json', 'identity_report.json', 'implementation_snapshot.json',
                 'runtime_parameters.json', 'completion_audit.json'):
        shutil.copy2(reference / name, directory / 'reference_evidence' / name)
    external = [ROOT / 'PX4-Autopilot/build/px4_sitl_default/bin/px4-alias.sh',
                ROOT / 'PX4-Autopilot/src/modules/simulation/gz_bridge/server.config']
    external.extend(path for path in (ROOT / 'PX4-Autopilot/build/px4_sitl_default/src/modules/simulation/gz_plugins').rglob('*')
                    if path.is_file())
    dependencies = {str(path): digest(path) for path in external}
    write_json(directory / 'batch_protocol.json', {
        'reference': str(reference), 'reference_coverage': load_json(reference / 'report.json')['follow_time_visible_fraction'],
        'selection': 'Fixed user-selected different-color separate-lane overtaking reference; no retuning.',
        'reference_task_passed': load_json(reference / 'report.json')['passed'],
        'reference_identity_verified': load_json(reference / 'identity_report.json')['identity_independently_verified'],
        'planned': len(plan), 'pilot_excluded_from_repeat_statistics': True,
        'runtime_changes': 'None: same code, model, parameters, scene and GUI; independent process restart per attempt.',
        'px4_rootfs': str(rootfs), 'external_dependency_sha256': dependencies,
        'safety_stop': 'Stop after wrong identity, safety event, intervention, or integrity drift. Ordinary task/scene failures continue without retry.',
        'loss_accounting': 'unplanned_losses retains legacy valid-entry accounting; outside_panel_losses counts only losses outside temporal panel intervals.',
        'limitations': ['Deterministic scene repetitions test runtime variability, not scene generalization.',
                       'Calibration and flight counters can persist in PX4 rootfs and are audited, not reset.',
                       'Different-color overtaking is not the old same-appearance crossing benchmark.']})
    METRICS.update({key: 'max' for key in ('outside_panel_losses', 'scene_update_errors',
        'wrong_identity_observations', 'scorable_identity_switches',
        'armed_failsafe_observations', 'armed_offboard_lost_observations', 'ulog_dropout_events')})
    rows, active, active_trial, stopped, error = [], None, None, False, None

    def verify():
        verify_freeze(ROOT, directory / 'freeze_manifest.json')
        verify_installed(ROOT)
        if any(digest(Path(name)) != checksum for name, checksum in dependencies.items()):
            raise RuntimeError('External runtime dependency changed.')

    def status():
        write_json(directory / 'study_status.json', {
            'planned': len(plan), 'attempted': len(rows),
            'completed': len(rows) == len(plan) and error is None and not stopped,
            'interrupted': stopped, 'active_trial': active_trial['name'] if active_trial else None,
            'error': error})

    def interrupt(signum, frame):
        nonlocal stopped
        stopped = True
        if active is not None and active.poll() is None:
            active.send_signal(signal.SIGINT)

    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    publish_summary(directory, plan, rows)
    status()
    try:
        for trial in plan:
            if stopped:
                break
            verify()
            active_trial = trial
            status()
            target = directory / trial['name']
            command = [str(ROOT / '.venv-yolo/bin/python'), str(ROOT / 'scripts/run_vehicle_tracking_validation.py'),
                       '--output', str(target), '--model-path', snapshot['model_path'],
                       '--freeze-manifest', str(directory / 'freeze_manifest.json'),
                       '--overtaking', '--gui', '--gui-config', str(ROOT / 'scripts/vehicle_tracking_gui.config'),
                       '--vehicle-speed', str(trial['vehicle_speed']), '--occlusion-start', str(trial['occlusion_start']),
                       '--occlusion-duration', str(trial['occlusion_duration'])]
            print(json.dumps({'started': trial['name'], 'completed': len(rows), 'planned': len(plan)}), flush=True)
            with (directory / (trial['name'] + '_supervisor.log')).open('w') as stream:
                active = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
                update = -float('inf')
                while active.poll() is None:
                    if time.monotonic() - update >= 30:
                        sample = read_latest_sample(target / 'samples.jsonl') or {}
                        print(json.dumps({'active': trial['name'], 'wall_s': sample.get('wall_s'),
                                          'state': sample.get('state')}), flush=True)
                        update = time.monotonic()
                    time.sleep(1)
                returncode = active.returncode
                active = None
            row = selected_row(target, trial, returncode)
            rows.append(row)
            active_trial = None
            publish_summary(directory, plan, rows)
            audit_studies(directory, rootfs=rootfs)
            if (target / 'flight.ulg').is_file():
                row.update(ulog_safety(target / 'flight.ulg'))
                if row['armed_failsafe_observations'] or row['armed_offboard_lost_observations']:
                    row['safety_event'] = True
                    row['success'] = False
                    row['criteria_failure_causes'].append('ulog_armed_safety_event')
            else:
                raise RuntimeError('ULog unavailable after attempt: ' + trial['name'])
            publish_summary(directory, plan, rows)
            print(json.dumps({'finished': trial['name'], 'coverage': row['visibility'],
                'flight_pass': row['flight_success'], 'identity_pass': row['identity_independently_verified'],
                'strict_pass': row['success'], 'outside_panel_losses': row['outside_panel_losses'],
                'scene_errors': row['scene_update_errors'], 'safety_event': row['safety_event']}), flush=True)
            verify()
            for name in ('px4', 'MicroXRCEAgent', 'gz sim server'):
                if subprocess.run(['pgrep', '-x', name], capture_output=True).returncode == 0:
                    raise RuntimeError('A trial left a running process: ' + name)
            if row.get('wrong_identity_observations') or row['safety_event'] or row['interventions']:
                stopped, error = True, 'safety_stop_after_' + trial['name']
            status()
            time.sleep(3)
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        try:
            if active is not None and active.poll() is None:
                active.send_signal(signal.SIGINT)
                active.wait()
            if active_trial is not None:
                row = selected_row(directory / active_trial['name'], active_trial,
                                   getattr(active, 'returncode', None))
                row['success'] = False
                row['failure_reasons'].append('batch_error:' + str(error))
                rows.append(row)
                active_trial = None
            publish_summary(directory, plan, rows)
            shutil.copytree(ROOT / 'ros2_ws/install/uav_learning/lib/python3.12/site-packages/uav_learning',
                            directory / 'installed_snapshot', ignore=shutil.ignore_patterns('__pycache__'))
            write_json(directory / 'failure_analysis.json', {
                'criteria_counts': dict(Counter(cause for row in rows for cause in row['criteria_failure_causes'])),
                'trials': [{'name': row['name'], 'strict_pass': row['success'],
                            'criteria_failure_causes': row['criteria_failure_causes']} for row in rows]})
        finally:
            status()
    return 0 if len(rows) == len(plan) and error is None else 2


if __name__ == '__main__':
    raise SystemExit(main())
