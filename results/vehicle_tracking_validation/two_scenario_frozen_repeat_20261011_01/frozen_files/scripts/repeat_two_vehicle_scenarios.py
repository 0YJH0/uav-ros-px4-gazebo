#!/usr/bin/env python3
"""Freeze and independently restart two vehicle scenes without replacing failures."""

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import time

from audit_vehicle_ulog import log_source
from repeat_frozen_crossing import compiled_px4_rootfs, verify_installed
from run_vehicle_tracking_validation import read_latest_sample
from vehicle_experiment_study import (ROOT, digest, freeze, load_json,
                                      verify_freeze, write_json)


def make_plan(count=10, gui=False):
    if count < 1:
        raise ValueError('count must be positive')
    result = []
    for index in range(1, count + 1):
        for group, scenario in (('left_overtaking', 'overtaking'),
                                ('lane_change', 'lane_change_overtaking')):
            result.append({
                'name': f'{group}_{index:02d}', 'group': group,
                'vehicle_speed': .8, 'occlusion_start': 15.,
                'occlusion_duration': 4., 'traffic_scenario': scenario,
                'crossing': False, 'overtaking': scenario == 'overtaking',
                'lane_change_overtaking': scenario == 'lane_change_overtaking',
                'distractor_color': 'red', 'parked_vehicle_y': -4.4,
                'recovery_competition_enabled': False,
                'predict_box_scale_velocity': True,
                'overlap_confirmation_continuity': True,
                'smooth_recovery_setpoints': False,
                'cpu_inference_threads': 0, 'detector_backend': 'torch',
                'backend_artifacts': '', 'gui': gui})
    return result


def now():
    return datetime.now(timezone.utc).isoformat()


def verify_reference(root, reference):
    snapshot = load_json(reference / 'implementation_snapshot.json')
    parameters = load_json(reference / 'runtime_parameters.json')
    if not snapshot or not snapshot.get('source_sha256') or not parameters:
        raise RuntimeError('Reference source snapshot and runtime parameters are required.')
    changed = [name for name, checksum in snapshot['source_sha256'].items()
               if not (root / name).is_file() or digest(root / name) != checksum]
    model = Path(snapshot['model_path'])
    if not model.is_file() or digest(model) != snapshot['model_sha256']:
        changed.append('model')
    if changed:
        raise RuntimeError('Reference implementation differs: ' + ', '.join(changed))
    allowed = {'name', 'group', 'traffic_scenario', 'crossing', 'overtaking',
               'lane_change_overtaking', 'gui'}
    for key, value in make_plan(1)[0].items():
        if key not in allowed and snapshot['scenario'].get(key) != value:
            raise RuntimeError('Reference scenario differs: ' + key)
    for key in ('overlap_candidate_recovery', 'bounded_scale_prediction',
                'overlap_confirmation_continuity'):
        if parameters.get('perception_node', {}).get(key) is not True:
            raise RuntimeError('Required reference improvement is disabled: ' + key)
    if parameters.get('px4_offboard_controller', {}).get('recovery_timeout') != 10.:
        raise RuntimeError('The 10 second blind-motion limit must be retained.')
    return snapshot, parameters


def verify_installation(root):
    verify_installed(root)
    share = root / 'ros2_ws/install/uav_learning/share/uav_learning'
    source = root / 'ros2_ws/src/uav_learning'
    changed = []
    for name in ('launch', 'config'):
        for path in (source / name).rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                installed = share / path.relative_to(source)
                if not installed.is_file() or digest(installed) != digest(path):
                    changed.append(str(path.relative_to(source)))
    if changed:
        raise RuntimeError('Installed launch/assets differ: ' + ', '.join(changed))


def prepare(directory, reference, count, gui=False):
    if directory.exists():
        raise RuntimeError('Use a new directory or --resume; never overwrite attempts.')
    snapshot, parameters = verify_reference(ROOT, reference)
    verify_installation(ROOT)
    rootfs = compiled_px4_rootfs(ROOT / 'PX4-Autopilot/build/px4_sitl_default/bin/px4')
    directory.mkdir(parents=True)
    (directory / 'attempts').mkdir()
    frozen = freeze(ROOT, directory, Path(snapshot['model_path']))
    frozen['declared_parameters'] = parameters
    helpers = ('repeat_two_vehicle_scenarios.py', 'audit_two_vehicle_scenarios.py',
               'repeat_frozen_crossing.py', 'audit_vehicle_ulog.py',
               'repeat_best_vehicle.py', 'vehicle_study_checks.py',
               'analyze_vehicle_framing.py', 'analyze_vehicle_latency.py',
               'vehicle_tracking_gui.config')
    for name in helpers:
        relative = 'scripts/' + name
        frozen['source_sha256'][relative] = digest(ROOT / relative)
        shutil.copy2(ROOT / relative, directory / 'frozen_files' / relative)
    write_json(directory / 'freeze_manifest.json', frozen)
    installed = ROOT / 'ros2_ws/install/uav_learning'
    shutil.copytree(installed, directory / 'installed_snapshot',
                    ignore=shutil.ignore_patterns('__pycache__'))
    external = [ROOT / 'PX4-Autopilot/build/px4_sitl_default/bin/px4-alias.sh',
                ROOT / 'PX4-Autopilot/src/modules/simulation/gz_bridge/server.config']
    external.extend(path for path in (
        ROOT / 'PX4-Autopilot/build/px4_sitl_default/src/modules/simulation/gz_plugins'
    ).rglob('*') if path.is_file())
    dependencies = {str(path): digest(path) for path in external}
    evidence = directory / 'reference_evidence'
    evidence.mkdir()
    for name in ('implementation_snapshot.json', 'runtime_parameters.json',
                 'report.json', 'identity_report.json', 'validation_summary.json'):
        if (reference / name).is_file():
            shutil.copy2(reference / name, evidence / name)
    plan = make_plan(count, gui)
    write_json(directory / 'plan.json', plan)
    write_json(directory / 'batch_protocol.json', {
        'created_utc': now(), 'reference': str(reference), 'planned': len(plan),
        'per_scenario_planned': count, 'order': 'alternating_left_then_lane_change',
        'pilot_excluded_from_repeat_statistics': True,
        'independent_process_restart': True, 'retry_failed_attempts': False,
        'gui': gui, 'model_path': snapshot['model_path'],
        'model_sha256': snapshot['model_sha256'], 'px4_rootfs': str(rootfs),
        'freeze_manifest_sha256': digest(directory / 'freeze_manifest.json'),
        'plan_sha256': digest(directory / 'plan.json'),
        'external_dependency_sha256': dependencies,
        'environment': {'python': sys.version, 'platform': platform.platform(),
                        'machine': platform.machine(), 'processor': platform.processor(),
                        'logical_cpu_count': os.cpu_count(),
                        'available_cpu_count': len(os.sched_getaffinity(0))},
        'attempt_contract': 'An attempts/<name>.json is persisted before launch. '
                            'Every started attempt is retained and never rerun. '
                            'Resume only executes previously unattempted plan entries.',
        'source_archive': 'Each trial executed_sources links to the shared frozen_files archive.',
        'safety_stop': 'Unconfirmed landing, interventions, armed safety events, '
                       'remaining simulator processes or provenance drift stop further launches. '
                       'Ordinary task/identity-evidence/scene scoring failures are retained and continue.',
        'limitations': ['Deterministic scene repeats measure runtime variability, not scene generalization.',
                       'GUI pilots are excluded: headless runtime load differs from visualized pilots.'
                       if not gui else 'GUI is enabled for both scene groups.',
                       'PX4 retained calibration and counters are recorded in ULogs, not reset.',
                       'Missing/unattempted trials are not reported as completed experiments.']})
    return plan


def verify(directory):
    protocol = load_json(directory / 'batch_protocol.json')
    if not protocol:
        raise RuntimeError('Missing batch protocol.')
    for name, key in (('freeze_manifest.json', 'freeze_manifest_sha256'),
                      ('plan.json', 'plan_sha256')):
        if digest(directory / name) != protocol[key]:
            raise RuntimeError('Frozen protocol input changed: ' + name)
    verify_freeze(ROOT, directory / 'freeze_manifest.json')
    verify_freeze(directory / 'frozen_files', directory / 'freeze_manifest.json')
    verify_installation(ROOT)
    for name, checksum in protocol['external_dependency_sha256'].items():
        if not Path(name).is_file() or digest(Path(name)) != checksum:
            raise RuntimeError('External dependency changed: ' + name)
    return protocol


def assert_no_simulation():
    names = ('px4', 'MicroXRCEAgent', 'gz sim server', 'gz sim gui')
    for name in names:
        result = subprocess.run(['pgrep', '-x', name], capture_output=True, text=True)
        if result.returncode == 0:
            raise RuntimeError('Existing simulation process; refusing to share: ' + name)
        if result.returncode != 1:
            raise RuntimeError('Cannot inspect simulation processes: ' + name)


def command_for(root, directory, trial, model):
    command = [str(root / '.venv-yolo/bin/python'),
               str(root / 'scripts/run_vehicle_tracking_validation.py'),
               '--output', str(directory / trial['name']), '--model-path', model,
               '--freeze-manifest', str(directory / 'freeze_manifest.json'),
               '--overtaking' if trial['overtaking'] else '--lane-change-overtaking',
               '--distractor-color', trial['distractor_color'],
               '--parked-y', str(trial['parked_vehicle_y']),
               '--vehicle-speed', str(trial['vehicle_speed']),
               '--occlusion-start', str(trial['occlusion_start']),
               '--occlusion-duration', str(trial['occlusion_duration']),
               '--detector-backend', trial['detector_backend'],
               '--cpu-inference-threads', str(trial['cpu_inference_threads'])]
    if trial['gui']:
        command.extend(['--gui', '--gui-config', str(root / 'scripts/vehicle_tracking_gui.config')])
    return command


def archive_trial(directory, trial, protocol):
    target = directory / trial['name']
    snapshot = load_json(target / 'implementation_snapshot.json')
    if not snapshot:
        raise RuntimeError('Trial has no implementation snapshot: ' + trial['name'])
    frozen = load_json(directory / 'freeze_manifest.json')
    changed = [name for name, checksum in snapshot['source_sha256'].items()
               if frozen['source_sha256'].get(name) != checksum]
    if snapshot.get('model_sha256') != protocol['model_sha256']:
        changed.append('model')
    if changed:
        raise RuntimeError('Executed source/model differs: ' + ', '.join(changed))
    archive = target / 'executed_sources'
    if not archive.exists():
        archive.symlink_to('../frozen_files', target_is_directory=True)
    if archive.resolve() != (directory / 'frozen_files').resolve():
        raise RuntimeError('Unexpected executed_sources archive.')
    text = (target / 'px4.log').read_text(errors='replace')
    source = log_source(Path(protocol['px4_rootfs']), text)
    destination = target / 'flight.ulg'
    if source is None or not source.is_file():
        if destination.is_file():
            return
        raise RuntimeError('ULog source unavailable: ' + trial['name'])
    checksum = digest(source)
    if destination.exists() and digest(destination) != checksum:
        raise RuntimeError('Archived ULog differs; refusing overwrite: ' + trial['name'])
    if not destination.exists():
        shutil.copy2(source, destination)
    write_json(target / 'archive_manifest.json', {
        'source_archive': '../frozen_files', 'ulog_source': str(source),
        'ulog_sha256': checksum, 'model_sha256': protocol['model_sha256'],
        'implementation_snapshot_sha256': digest(target / 'implementation_snapshot.json')})


def existing_attempts(directory, plan):
    expected = {trial['name'] for trial in plan}
    result = {}
    for path in sorted((directory / 'attempts').glob('*.json')):
        item = load_json(path)
        if not item or item.get('name') != path.stem or path.stem not in expected:
            raise RuntimeError('Invalid attempt ledger: ' + str(path))
        result[path.stem] = item
    for trial in plan:
        if (directory / trial['name']).exists() and trial['name'] not in result:
            raise RuntimeError('Trial directory without attempt ledger: ' + trial['name'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--count', type=int, default=10)
    parser.add_argument('--gui', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    directory, reference = args.output.resolve(), args.reference.resolve()
    plan = make_plan(args.count, args.gui)
    if not args.resume:
        prepare(directory, reference, args.count, args.gui)
    elif load_json(directory / 'plan.json') != plan:
        raise RuntimeError('Resume plan differs from the frozen plan.')
    protocol = verify(directory)
    if protocol['reference'] != str(reference):
        raise RuntimeError('Resume reference differs.')
    if args.prepare_only:
        print(json.dumps({'prepared': str(directory), 'planned': len(plan)}), flush=True)
        return 0

    # A lock plus durable pre-launch ledger prevents duplicate attempts on resume.
    lock = (directory / '.runner.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    from audit_two_vehicle_scenarios import audit_trial, summarize_batch
    attempts = existing_attempts(directory, plan)
    active, active_trial, stopped, error = None, None, False, None

    def status():
        write_json(directory / 'study_status.json', {
            'updated_utc': now(), 'runner_pid': os.getpid(),
            'planned': len(plan), 'attempted': len(attempts),
            'completed_attempts': sum(row.get('state') == 'completed' for row in attempts.values()),
            'completed': (sum(row.get('state') == 'completed' for row in attempts.values())
                          == len(plan) and active_trial is None),
            'interrupted': stopped, 'error': error,
            'active_trial': active_trial['name'] if active_trial else None})

    def interrupt(signum, frame):
        nonlocal stopped
        if not stopped and active is not None and active.poll() is None:
            active.send_signal(signal.SIGINT)
        stopped = True

    def finalize(trial, returncode, interrupted=False):
        item = attempts[trial['name']]
        item.update(state='interrupted' if interrupted else 'completed',
                    finished_utc=now(), returncode=returncode)
        try:
            archive_trial(directory, trial, protocol)
        except Exception as exc:
            item['archive_error'] = str(exc)
        write_json(directory / 'attempts' / (trial['name'] + '.json'), item)
        audit = audit_trial(ROOT, directory / trial['name'], trial,
                            load_json(directory / 'freeze_manifest.json')['source_sha256'])
        summarize_batch(directory)
        print(json.dumps({'finished': trial['name'], 'returncode': returncode,
                          'safe_to_continue': audit.get('safe_to_continue'),
                          'archive_error': item.get('archive_error')}), flush=True)
        if item.get('archive_error') or audit.get('safe_to_continue') is not True:
            raise RuntimeError('Safety/integrity stop after ' + trial['name'])

    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    try:
        assert_no_simulation()
        # An interrupted launch remains an attempted failure; it is never replayed.
        for trial in plan:
            item = attempts.get(trial['name'])
            if item is None:
                continue
            if item.get('state') == 'started':
                finalize(trial, None, interrupted=True)
            else:
                audit = audit_trial(ROOT, directory / trial['name'], trial,
                                    load_json(directory / 'freeze_manifest.json')['source_sha256'])
                if audit.get('safe_to_continue') is not True:
                    raise RuntimeError('Prior attempt requires safety review: ' + trial['name'])
        summarize_batch(directory)
        status()
        for trial in plan:
            if stopped or trial['name'] in attempts:
                continue
            verify(directory)
            assert_no_simulation()
            command = command_for(ROOT, directory, trial, protocol['model_path'])
            active_trial = trial
            attempts[trial['name']] = {
                'name': trial['name'], 'group': trial['group'], 'state': 'started',
                'started_utc': now(), 'command': command,
                'freeze_manifest_sha256': digest(directory / 'freeze_manifest.json')}
            write_json(directory / 'attempts' / (trial['name'] + '.json'), attempts[trial['name']])
            status()
            print(json.dumps({'started': trial['name'], 'attempted': len(attempts),
                              'planned': len(plan)}), flush=True)
            with (directory / (trial['name'] + '_supervisor.log')).open('x') as stream:
                active = subprocess.Popen(command, cwd=ROOT, stdout=stream,
                                          stderr=subprocess.STDOUT, start_new_session=True)
                update = -float('inf')
                while active.poll() is None:
                    if time.monotonic() - update >= 30:
                        sample = read_latest_sample(directory / trial['name'] / 'samples.jsonl') or {}
                        print(json.dumps({'active': trial['name'], 'wall_s': sample.get('wall_s'),
                                          'state': sample.get('state')}), flush=True)
                        update = time.monotonic()
                    time.sleep(1)
                returncode = active.returncode
                active = None
            finished = active_trial
            active_trial = None
            finalize(finished, returncode, interrupted=stopped)
            verify(directory)
            assert_no_simulation()
            status()
            if not stopped:
                time.sleep(3)
    except Exception as exc:
        error = str(exc)
        print(json.dumps({'stopped': error}), flush=True)
    finally:
        if active is not None and active.poll() is None:
            active.send_signal(signal.SIGINT)
            active.wait()
        if active_trial is not None:
            try:
                finalize(active_trial, getattr(active, 'returncode', None), interrupted=True)
            except Exception as exc:
                error = error or str(exc)
            active_trial = None
        summarize_batch(directory)
        status()
        lock.close()
    completed = sum(row.get('state') == 'completed' for row in attempts.values())
    return 0 if completed == len(plan) and not error and not stopped else 2


if __name__ == '__main__':
    raise SystemExit(main())
