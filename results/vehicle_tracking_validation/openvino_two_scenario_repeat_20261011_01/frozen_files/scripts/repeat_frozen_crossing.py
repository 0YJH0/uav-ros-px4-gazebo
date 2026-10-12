#!/usr/bin/env python3
"""Repeat an archived crossing implementation in an isolated runtime workspace."""

import argparse
import json
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import time

from vehicle_experiment_study import (METRICS, ROOT, digest, load_json, publish_summary,
                                      trial_row, verify_freeze, write_json)
from audit_vehicle_ulog import audit_studies
from vehicle_study_checks import inspect_study


def make_plan(count):
    if count < 1:
        raise ValueError('count must be positive')
    return [{'name': f'crossing_{index:02d}', 'group': 'frozen_crossing_79_65',
             'vehicle_speed': 0.8, 'occlusion_start': 15.0,
             'occlusion_duration': 4.0, 'crossing': True}
            for index in range(1, count + 1)]


def verify_installed(runtime):
    source = runtime / 'ros2_ws/src/uav_learning/uav_learning'
    installed = runtime / 'ros2_ws/install/uav_learning/lib/python3.12/site-packages/uav_learning'
    changed = [path.name for path in source.glob('*.py')
               if not (installed / path.name).is_file()
               or digest(path) != digest(installed / path.name)]
    if changed:
        raise RuntimeError('Installed frozen modules differ: ' + ', '.join(changed))


def compiled_px4_rootfs(binary):
    result = subprocess.run(['strings', str(binary)], capture_output=True, text=True, check=True)
    candidates = {Path(line).resolve() for line in result.stdout.splitlines()
                  if line.startswith('/') and line.endswith('/build/px4_sitl_default/rootfs')}
    if len(candidates) != 1:
        raise RuntimeError('Cannot identify a unique compiled PX4 rootfs; refusing to guess.')
    rootfs = candidates.pop()
    if not rootfs.is_dir() or not (rootfs.parent / 'etc').is_dir():
        raise RuntimeError('Compiled PX4 rootfs/configuration is unavailable: ' + str(rootfs))
    return rootfs


def verify_shared_px4(rootfs, manifest):
    repository = Path(rootfs).parents[3]
    changed = [name for name, checksum in manifest['source_sha256'].items()
               if name.startswith('PX4-Autopilot/') and
               (not (repository / name).is_file() or digest(repository / name) != checksum)]
    if changed:
        raise RuntimeError('Compiled-rootfs PX4 assets differ from the reference: ' + ', '.join(changed))


def prepare(base, directory):
    manifest = base / 'freeze_manifest.json'
    verify_freeze(base / 'frozen_files', manifest)
    frozen = load_json(manifest)
    actual_rootfs = compiled_px4_rootfs(base / 'frozen_files/PX4-Autopilot/build/px4_sitl_default/bin/px4')
    verify_shared_px4(actual_rootfs, frozen)
    directory.mkdir(parents=True, exist_ok=False)
    shutil.copy2(manifest, directory / 'freeze_manifest.json')
    runtime = directory / 'runtime'
    shutil.copytree(base / 'frozen_files', runtime)
    (runtime / '.venv-yolo').symlink_to(ROOT / '.venv-yolo', target_is_directory=True)
    build = runtime / 'PX4-Autopilot/build/px4_sitl_default'
    rootfs = build / 'rootfs'
    rootfs.mkdir()
    (rootfs / 'etc').symlink_to(build / 'etc', target_is_directory=True)
    # Module entrypoints invoke the identical archived PX4 executable.
    for path in (ROOT / 'PX4-Autopilot/build/px4_sitl_default/bin').glob('px4-*'):
        if path.is_symlink():
            (build / 'bin' / path.name).symlink_to('px4')
    live_build = ROOT / 'PX4-Autopilot/build/px4_sitl_default'
    shutil.copy2(live_build / 'bin/px4-alias.sh', build / 'bin/px4-alias.sh')
    assets = {
        'PX4_GZ_MODELS': runtime / 'PX4-Autopilot/Tools/simulation/gz/models',
        'PX4_GZ_WORLDS': runtime / 'PX4-Autopilot/Tools/simulation/gz/worlds',
        'PX4_GZ_PLUGINS': live_build / 'src/modules/simulation/gz_plugins',
        'PX4_GZ_SERVER_CONFIG': ROOT / 'PX4-Autopilot/src/modules/simulation/gz_bridge/server.config',
    }
    dependencies = {}
    dependencies[str(live_build / 'bin/px4-alias.sh')] = digest(live_build / 'bin/px4-alias.sh')
    for path in assets['PX4_GZ_PLUGINS'].rglob('*'):
        if path.is_file():
            dependencies[str(path)] = digest(path)
    dependencies[str(assets['PX4_GZ_SERVER_CONFIG'])] = digest(assets['PX4_GZ_SERVER_CONFIG'])
    bootstrap = '\n'.join('export ' + name + '=' + shlex.quote(str(path))
                          for name, path in assets.items())
    bootstrap += ('\nexport GZ_SIM_RESOURCE_PATH="$PX4_GZ_MODELS:$PX4_GZ_WORLDS"'
                  '\nexport GZ_SIM_SYSTEM_PLUGIN_PATH="$PX4_GZ_PLUGINS"'
                  '\nexport GZ_SIM_SERVER_CONFIG_PATH="$PX4_GZ_SERVER_CONFIG"\n')
    (rootfs / 'gz_env.sh').write_text(bootstrap)
    # Reuse only immutable ROS underlay binaries; frozen flight nodes install above it.
    command = ('source /opt/ros/jazzy/setup.bash; source '
               + shlex.quote(str(ROOT / 'ros2_ws/install/setup.bash'))
               + '; exec colcon build --packages-select px4_msgs uav_interfaces uav_learning')
    with (directory / 'runtime_build.log').open('w') as stream:
        subprocess.run(['bash', '-c', command], cwd=runtime / 'ros2_ws',
                       stdout=stream, stderr=subprocess.STDOUT, check=True)
    verify_freeze(runtime, directory / 'freeze_manifest.json')
    verify_installed(runtime)
    live_hashes = {name: digest(ROOT / name) for name in frozen['source_sha256']
                   if (ROOT / name).is_file()}
    write_json(directory / 'repeat_provenance.json', {
        'reference_study': str(base), 'reference_trial': 'crossing_pilot_01',
        'reference_coverage': 0.796515099775959,
        'reference_manifest_sha256': digest(manifest),
        'runtime': str(runtime), 'live_source_before': live_hashes,
        'px4_rootfs': str(actual_rootfs),
        'external_dependency_sha256': dependencies,
        'execution': 'Unmodified archived nodes, launch, supervisor, recorder and crossing helper. '
                     'Only relocation/bootstrap/build entrypoints are generated. '
                     'The DDS Agent and system ROS/Gazebo/venv dependencies are reused.',
        'limits': 'Identical deterministic scenes measure restart/runtime variability, not scene diversity. '
                  'The reference pilot is excluded from the new ten-trial denominator. '
                  'PX4 uses its compiled rootfs and retains automatic calibration state.'})
    return runtime


def verify(directory):
    provenance = load_json(directory / 'repeat_provenance.json')
    runtime = Path(provenance['runtime'])
    verify_freeze(runtime, directory / 'freeze_manifest.json')
    verify_installed(runtime)
    if provenance.get('px4_rootfs'):
        verify_shared_px4(provenance['px4_rootfs'], load_json(directory / 'freeze_manifest.json'))
    for name, checksum in provenance['external_dependency_sha256'].items():
        if digest(Path(name)) != checksum:
            raise RuntimeError('Runtime dependency drift: ' + name)
    for name, checksum in provenance.get('reporting_helper_sha256', {}).items():
        if digest(ROOT / name) != checksum:
            raise RuntimeError('Reporting helper drift: ' + name)
    for name, checksum in provenance.get('bootstrap_sha256', {}).items():
        if digest(runtime / name) != checksum:
            raise RuntimeError('Runtime bootstrap drift: ' + name)
    for name, checksum in provenance['live_source_before'].items():
        if digest(ROOT / name) != checksum:
            raise RuntimeError('Live development source changed: ' + name)
    return runtime


def completed_trial(target, trial, returncode):
    row = trial_row(target, trial)
    row['returncode'] = returncode
    row['flight_success'] = bool(row['success'] and returncode == 0)
    identity = load_json(target / 'identity_report.json') or {}
    row['identity_independently_verified'] = bool(identity.get('identity_independently_verified'))
    for name in ('wrong_identity_observations', 'scorable_identity_switches',
                 'after_last_overlap_confirmation_wall_s', 'matched_truth_fraction'):
        row[name] = identity.get(name)
    row['identity_report_available'] = bool(identity)
    row['identity_pass'] = bool(row['flight_success'] and row['identity_independently_verified'])
    row['success'] = row['identity_pass']
    if returncode != 0:
        row['failure_reasons'].append(f'supervisor_exit_{returncode}')
    if not row['identity_independently_verified']:
        row['failure_reasons'].append('independent_identity_not_verified')
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--count', type=int, default=10)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--prepared', action='store_true')
    args = parser.parse_args()
    METRICS.update({'after_last_overlap_confirmation_wall_s': 'max',
                    'scorable_identity_switches': 'max', 'wrong_identity_observations': 'max'})
    directory = args.output.resolve()
    plan = make_plan(args.count)
    if not args.prepared:
        prepare(args.reference.resolve(), directory)
        write_json(directory / 'plan.json', plan)
    elif load_json(directory / 'plan.json') != plan:
        raise RuntimeError('Prepared experiment plan differs.')
    runtime = verify(directory)
    if args.prepare_only:
        print('Prepared exact archived runtime: ' + str(runtime), flush=True)
        return
    if (directory / 'study_summary.json').exists():
        raise RuntimeError('This batch was already started; never overwrite or retry attempts.')
    provenance = load_json(directory / 'repeat_provenance.json')
    helpers = ('repeat_frozen_crossing.py', 'vehicle_experiment_study.py',
               'audit_vehicle_ulog.py', 'vehicle_study_checks.py')
    provenance['reporting_helper_sha256'] = {'scripts/' + name: digest(ROOT / 'scripts' / name)
                                             for name in helpers}
    extra = directory / 'reporting_helpers'
    extra.mkdir()
    for name in helpers:
        shutil.copy2(ROOT / 'scripts' / name, extra / name)
    bootstrap = ('PX4-Autopilot/build/px4_sitl_default/rootfs/gz_env.sh',
                 'PX4-Autopilot/build/px4_sitl_default/bin/px4-alias.sh')
    provenance['bootstrap_sha256'] = {name: digest(runtime / name) for name in bootstrap}
    write_json(directory / 'repeat_provenance.json', provenance)
    rows, active, stopped = [], None, False

    def interrupt(signum, frame):
        nonlocal stopped
        stopped = True
        if active is not None and active.poll() is None:
            active.send_signal(signal.SIGINT)

    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    publish_summary(directory, plan, rows)
    error, active_name = None, None

    def record_status():
        write_json(directory / 'study_status.json', {
            'completed': len(rows) == len(plan) and error is None and not stopped,
            'attempted': len(rows), 'planned': len(plan), 'interrupted': stopped,
            'active_trial': active_name, 'error': error})

    try:
        record_status()
        for trial in plan:
            if stopped:
                break
            verify(directory)
            target = directory / trial['name']
            active_name = trial['name']
            record_status()
            command = [sys.executable, str(runtime / 'scripts/run_vehicle_tracking_validation.py'),
                       '--output', str(target), '--model-path', str(runtime / 'yolo11s.pt'),
                       '--freeze-manifest', str(directory / 'freeze_manifest.json'), '--crossing']
            print(json.dumps({'started': trial['name'], 'completed': len(rows), 'planned': len(plan)}), flush=True)
            with (directory / (trial['name'] + '_supervisor.log')).open('w') as stream:
                active = subprocess.Popen(command, cwd=runtime, stdout=stream, stderr=subprocess.STDOUT)
                while active.poll() is None:
                    time.sleep(1)
                returncode = active.returncode
                active = None
            row = completed_trial(target, trial, returncode)
            rows.append(row)
            active_name = None
            publish_summary(directory, plan, rows)
            audit_studies(directory, rootfs=Path(provenance.get(
                'px4_rootfs', str(ROOT / 'PX4-Autopilot/build/px4_sitl_default/rootfs'))))
            verify(directory)
            for name in ('px4', 'MicroXRCEAgent'):
                if subprocess.run(['pgrep', '-x', name], capture_output=True).returncode == 0:
                    raise RuntimeError('A trial left a running process: ' + name)
            record_status()
            inspection = inspect_study(directory)
            write_json(directory / 'completion_check.json', inspection)
            write_json(directory / 'failure_analysis.json', {
                'criteria_causes_counts': inspection['failure_counts'], 'trials': inspection['trials']})
            print(json.dumps({'finished': trial['name'], 'success': row['success'],
                              'flight_success': row['flight_success'],
                              'identity_verified': row['identity_independently_verified'],
                              'visibility': row['visibility'], 'unplanned_losses': row['unplanned_losses'],
                              'failures': sum(not item['success'] for item in rows)}), flush=True)
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        # Let the original supervisor finish its safety landing on interruption.
        try:
            if active is not None and active.poll() is None:
                active.send_signal(signal.SIGINT)
                active.wait()
            if active_name is not None:
                trial = next(item for item in plan if item['name'] == active_name)
                row = completed_trial(directory / active_name, trial,
                                      getattr(active, 'returncode', None))
                row['failure_reasons'].append('batch_error:' + str(error))
                rows.append(row)
                publish_summary(directory, plan, rows)
                active_name = None
        finally:
            record_status()


if __name__ == '__main__':
    main()
