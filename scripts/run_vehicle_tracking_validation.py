#!/usr/bin/env python3
"""Supervise a fresh local SITL trial without changing the flight controller."""

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import shlex
import signal
import subprocess
import time


def check_sample_safety(sample):
    if sample and (sample.get('failsafe_observed') or (sample.get('status') or {}).get('failsafe')):
        raise RuntimeError('PX4 failsafe observed; stopping the mission before safety landing.')


def backend_launch_argument(artifacts):
    if artifacts is None:
        return ''
    return 'backend_artifacts:=' + shlex.quote(str(artifacts.resolve())) + ' '


def read_latest_sample(path):
    if not path.exists():
        return None
    with path.open('rb') as stream:
        size = stream.seek(0, 2)
        start = max(0, size - 65536)
        stream.seek(start)
        lines = stream.read().splitlines()
    if start:
        lines = lines[1:]
    for line in reversed(lines):
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                return value
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    return None


def capture_runtime_parameters(root, env, ros_prefix, timeout=45.0, *,
                               run=subprocess.run, clock=time.monotonic, sleep=time.sleep):
    import yaml
    captured, attempts = {}, []
    deadline = clock() + timeout
    for node in ('perception_node', 'px4_offboard_controller', 'vehicle_scene'):
        error = 'parameter discovery deadline exceeded'
        while clock() < deadline:
            remaining = deadline - clock()
            try:
                result = run(['bash', '-c', ros_prefix.removesuffix('exec ')
                              + f'ros2 param dump --no-daemon --spin-time 2 --timeout 5 /{node}'],
                             cwd=root, env=env, capture_output=True, text=True,
                             timeout=min(15.0, remaining))
                if result.returncode:
                    raise RuntimeError(result.stderr.strip() or result.stdout.strip())
                data = yaml.safe_load(result.stdout)
                parameters = data['/' + node]['ros__parameters']
                if not isinstance(parameters, dict) or not parameters:
                    raise ValueError('empty parameter response')
                captured[node] = parameters
                attempts.append({'node': node, 'ok': True})
                break
            except (subprocess.TimeoutExpired, RuntimeError, ValueError, KeyError, TypeError, yaml.YAMLError) as exc:
                error = str(exc)
                attempts.append({'node': node, 'ok': False, 'error': error})
                sleep(min(1.0, max(0.0, deadline - clock())))
        else:
            raise RuntimeError(f'Cannot capture parameters for {node}: {error}; attempts={attempts}')
    return captured, attempts


def safety_land(stop_mission, command_land, latest_sample, safely_landed,
                timeout=90.0, *, clock=time.monotonic, sleep=time.sleep):
    # Stop the competing offboard publisher before handing landing to PX4.
    stop_mission()
    result = command_land()
    if result not in (None, 0):
        raise RuntimeError(f'PX4 landing command failed with exit code {result}.')
    deadline = clock() + timeout
    while clock() < deadline and not safely_landed(latest_sample()):
        sleep(min(2.0, max(0.0, deadline - clock())))
    return safely_landed(latest_sample())


def detector_preflight(root, env, ros_prefix, *, run=subprocess.run, python_path=None,
                       backend='torch', artifacts=None, model_path=None):
    python = python_path or root / '.venv-yolo/bin/python'
    code = 'from ultralytics import YOLO; import rclpy; from cv_bridge import CvBridge'
    if backend == 'openvino':
        code += ('; import numpy as np; from uav_learning.vehicle_detector_backend import OpenVINOVehicleDetector; '
                 f'model=OpenVINOVehicleDetector({str(artifacts)!r}, {str(model_path)!r}); '
                 'model.predict(np.zeros((540,960,3),np.uint8), [2], .1, 960); '
                 'model.predict(np.zeros((320,320,3),np.uint8), [2], .1, 640)')
    result = run(['bash', '-c', ros_prefix + shlex.quote(str(python)) + ' -c '
                  + shlex.quote(code)],
                 cwd=root, env=env, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError('Detector runtime preflight failed: ' + result.stderr.strip())
    return str(python)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    parser.add_argument('--timeout', type=float, default=750.0)
    parser.add_argument('--model-path', default='yolo11s.pt')
    parser.add_argument('--vehicle-speed', type=float, default=0.8)
    parser.add_argument('--occlusion-start', type=float, default=15.0)
    parser.add_argument('--occlusion-duration', type=float, default=4.0)
    parser.add_argument('--freeze-manifest', type=Path)
    traffic = parser.add_mutually_exclusive_group()
    traffic.add_argument('--crossing', action='store_true')
    traffic.add_argument('--overtaking', action='store_true', help='Distractor overtakes in a separate lane.')
    traffic.add_argument('--lane-change-overtaking', action='store_true',
                         help='Same-lane rear approach, left-lane pass, then merge back ahead.')
    parser.add_argument('--distractor-color', choices=('auto', 'red', 'blue'), default='auto',
                        help='Color of moving and parked distractors; auto is blue for fixed-lane overtaking, red otherwise.')
    parser.add_argument('--parked-y', type=float, default=-12.0,
                        help='Parked vehicle lateral position in meters; -4.4 is curbside on the overtaking road.')
    parser.add_argument('--gui', action='store_true', help='Open Gazebo on the local graphical desktop.')
    parser.add_argument('--gui-config', type=Path, help='Optional Gazebo GUI configuration; requires --gui.')
    parser.add_argument('--recovery-competition', action='store_true')
    parser.add_argument('--hold-box-scale', action='store_true')
    parser.add_argument('--no-overlap-confirmation-continuity', action='store_true')
    parser.add_argument('--smooth-recovery-setpoints', action='store_true', help='Experimental recovery ramps; not promoted by the failed pilot.')
    parser.add_argument('--cpu-inference-threads', type=int, default=0)
    parser.add_argument('--detector-backend', choices=('torch', 'openvino'), default='torch')
    parser.add_argument('--backend-artifacts', type=Path)
    parser.add_argument('--perception-python', type=Path)
    args = parser.parse_args()
    scenario = ('lane_change_overtaking' if args.lane_change_overtaking else
                'overtaking' if args.overtaking else 'crossing')
    if args.distractor_color == 'auto':
        args.distractor_color = 'blue' if args.overtaking else 'red'
    root = Path(__file__).resolve().parents[1]
    if args.vehicle_speed <= 0 or args.occlusion_duration <= 0 or args.occlusion_start < 0:
        raise ValueError('Invalid scene parameters.')
    if not math.isfinite(args.parked_y):
        raise ValueError('parked-y must be finite.')
    if not 0 <= args.cpu_inference_threads <= 32:
        raise ValueError('cpu-inference-threads must be in [0, 32].')
    if args.freeze_manifest:
        from vehicle_experiment_study import verify_freeze
        verify_freeze(root, args.freeze_manifest)
    model_path = Path(args.model_path).resolve()
    if not model_path.is_file():
        raise RuntimeError('model-path must be an existing local weight file; no in-flight download.')
    if args.detector_backend == 'openvino' and not args.backend_artifacts:
        raise ValueError('OpenVINO requires pre-exported backend artifacts.')
    if args.perception_python and not args.perception_python.is_file():
        raise ValueError('perception-python must be an existing local interpreter.')
    if args.gui_config and (not args.gui or not args.gui_config.is_file()):
        raise ValueError('gui-config must exist and be used with --gui.')
    if args.gui and not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
        raise RuntimeError('Gazebo GUI requires a graphical display.')
    directory = Path(args.output).resolve()
    if directory.exists():
        raise RuntimeError('Use a new output directory; existing evidence is never overwritten.')
    for name in ('px4', 'MicroXRCEAgent', 'gz sim server'):
        check = subprocess.run(['pgrep', '-x', name], capture_output=True)
        if check.returncode == 0:
            raise RuntimeError(f'Existing {name} instance; refusing to share simulation.')
    directory.mkdir(parents=True)
    source_paths = [
        'ros2_ws/src/uav_learning/uav_learning/perception_node.py',
        'ros2_ws/src/uav_learning/uav_learning/vehicle_roi_detector.py',
        'ros2_ws/src/uav_learning/uav_learning/vehicle_target_lock.py',
        'ros2_ws/src/uav_learning/uav_learning/vehicle_byte_tracker.py',
        'ros2_ws/src/uav_learning/uav_learning/vehicle_recovery_competition.py',
        'ros2_ws/src/uav_learning/uav_learning/vehicle_detector_backend.py',
        'ros2_ws/src/uav_learning/uav_learning/vehicle_camera_motion.py',
        'ros2_ws/src/uav_learning/uav_learning/vehicle_frame_buffer.py',
        'ros2_ws/src/uav_learning/uav_learning/px4_offboard_controller.py',
        'ros2_ws/src/uav_learning/uav_learning/vehicle_scene.py',
        'ros2_ws/src/uav_learning/uav_learning/vehicle_gazebo_client.py',
        'ros2_ws/src/uav_learning/launch/vehicle_tracking.launch.py',
        'ros2_ws/src/uav_learning/config/models/tracking_car/model.sdf',
        'scripts/validate_vehicle_tracking.py', 'scripts/run_vehicle_tracking_validation.py',
        'scripts/vehicle_crossing_validation.py',
        'scripts/vehicle_lane_change.py',
    ]
    source_paths.extend(str(path.relative_to(root)) for path in sorted(
        (root / 'ros2_ws/src/uav_learning/config/models').rglob('*'))
        if path.is_file() and str(path.relative_to(root)) not in source_paths)
    snapshot = {'source_sha256': {path: hashlib.sha256((root / path).read_bytes()).hexdigest()
                                  for path in source_paths},
                'package_versions': {name: importlib.metadata.version(name)
                                     for name in ('ultralytics', 'torch', 'torchvision')},
                'target_roi_enabled': True,
                'model_path': str(model_path),
                'model_sha256': hashlib.sha256(model_path.read_bytes()).hexdigest(),
                'scenario': {'vehicle_speed': args.vehicle_speed,
                             'occlusion_start': args.occlusion_start,
                             'occlusion_duration': args.occlusion_duration,
                             'recovery_competition_enabled': args.recovery_competition,
                             'predict_box_scale_velocity': not args.hold_box_scale,
                             'overlap_confirmation_continuity': not args.no_overlap_confirmation_continuity,
                             'smooth_recovery_setpoints': args.smooth_recovery_setpoints,
                             'cpu_inference_threads': args.cpu_inference_threads,
                             'detector_backend': args.detector_backend,
                             'backend_artifacts': str(args.backend_artifacts.resolve()) if args.backend_artifacts else '',
                             'gui': args.gui,
                             'distractor_color': args.distractor_color,
                             'parked_vehicle_y': args.parked_y,
                             'crossing': args.crossing, 'overtaking': args.overtaking,
                             'lane_change_overtaking': args.lane_change_overtaking,
                             'traffic_scenario': scenario},
                'limitation': 'Source hashes establish provenance, not successful detection or identity.'}
    if args.backend_artifacts:
        snapshot['backend_artifact_sha256'] = {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in args.backend_artifacts.iterdir()
            if path.suffix in ('.xml', '.bin', '.json')}
    (directory / 'implementation_snapshot.json').write_text(json.dumps(snapshot, indent=2) + '\n')
    processes, logs = {}, []
    interventions = []
    started = time.monotonic()
    outcome = {'interventions': interventions, 'error': None}
    env = os.environ.copy()
    env['ROS_LOG_DIR'] = str(directory / 'ros_logs')
    env['ROS_DOMAIN_ID'] = '0'
    env['PYTHONUNBUFFERED'] = '1'
    ros_prefix = 'source /opt/ros/jazzy/setup.bash; source ros2_ws/install/setup.bash; exec '
    px4_bin = root / 'PX4-Autopilot/build/px4_sitl_default/bin'
    rootfs = px4_bin.parent / 'rootfs'

    def launch(name, command, cwd=root):
        log = (directory / f'{name}.log').open('w')
        logs.append(log)
        processes[name] = subprocess.Popen(
            ['bash', '-c', command], cwd=cwd, env=env,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        print(f'Started {name}: PID {processes[name].pid}', flush=True)

    def command(module, *arguments):
        result = subprocess.run([str(px4_bin / f'px4-{module}'), *arguments],
                                cwd=rootfs, env=env, capture_output=True, timeout=10)
        print(result.stdout.decode(errors='replace').strip(), flush=True)
        return result.returncode

    def capture_parameters():
        captured, attempts = capture_runtime_parameters(root, env, ros_prefix)
        outcome['parameter_capture_attempts'] = attempts
        (directory / 'runtime_parameters.json').write_text(json.dumps(captured, indent=2) + '\n')
        if args.freeze_manifest:
            from vehicle_experiment_study import verify_parameters
            frozen = json.loads(args.freeze_manifest.read_text())
            verify_parameters(captured, snapshot['scenario'], frozen['declared_parameters'])
            if captured['perception_node']['model_path'] != str(model_path):
                raise RuntimeError('Runtime detector weights differ from the frozen model.')
        outcome['parameters_verified'] = True

    def latest_sample():
        return read_latest_sample(directory / 'samples.jsonl')

    def safely_landed(sample):
        return bool(sample and sample.get('landed') and sample.get('status')
                    and sample['status']['arming_state'] == 1)

    def stop(name):
        process = processes.get(name)
        if process is None:
            return
        try:
            os.killpg(process.pid, signal.SIGINT)
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()

    try:
        perception_python = detector_preflight(root, env, ros_prefix, python_path=args.perception_python,
                                               backend=args.detector_backend, artifacts=args.backend_artifacts,
                                               model_path=model_path)
        outcome['perception_python'] = perception_python
        launch('agent', ros_prefix + 'MicroXRCEAgent udp4 -p 8888')
        time.sleep(1)
        if processes['agent'].poll() is not None:
            raise RuntimeError('DDS Agent failed to start.')
        launch('px4', f'source {shlex.quote(str(root / "scripts/px4_env.sh"))}; '
               'export PX4_SYS_AUTOSTART=4001 PX4_SIM_MODEL=gz_x500_perception HEADLESS=1; '
               f'exec {shlex.quote(str(px4_bin / "px4"))} -d', cwd=rootfs)
        readiness = time.monotonic() + 90
        while time.monotonic() < readiness:
            if processes['px4'].poll() is not None:
                raise RuntimeError('PX4 exited before readiness.')
            if 'Ready for takeoff!' in (directory / 'px4.log').read_text(errors='replace'):
                break
            time.sleep(1)
        else:
            raise RuntimeError('PX4 startup did not become ready within 90 seconds.')
        if args.gui:
            resources = ':'.join(str(path) for path in (
                root / 'PX4-Autopilot/Tools/simulation/gz/models',
                root / 'ros2_ws/src/uav_learning/config/models'))
            gui_command = (f'source {shlex.quote(str(root / "scripts/px4_env.sh"))}; '
                           'export QT_QPA_PLATFORM=xcb; '
                           f'export GZ_SIM_RESOURCE_PATH={shlex.quote(resources)}; '
                           'exec gz sim -g')
            if args.gui_config:
                gui_command += ' --gui-config ' + shlex.quote(str(args.gui_config.resolve()))
                outcome['gui_config_sha256'] = hashlib.sha256(args.gui_config.read_bytes()).hexdigest()
            launch('gui', gui_command)
            time.sleep(4)
            if processes['gui'].poll() is not None:
                raise RuntimeError('Gazebo GUI failed to start; mission was not launched.')
        launch('recorder', ros_prefix + shlex.quote(str(root / '.venv-yolo/bin/python'))
               + ' scripts/validate_vehicle_tracking.py --output ' + shlex.quote(str(directory)))
        time.sleep(2)
        if args.crossing or args.overtaking or args.lane_change_overtaking:
            launch('crossing', ros_prefix + shlex.quote(str(root / '.venv-yolo/bin/python'))
                   + ' scripts/vehicle_crossing_validation.py --output ' + shlex.quote(str(directory))
                   + f' --scenario {scenario}'
                   + f' --distractor-color {args.distractor_color}'
                   + f' --vehicle-speed {args.vehicle_speed}')
        launch('mission', ros_prefix + 'ros2 launch uav_learning vehicle_tracking.launch.py '
               + 'model_path:=' + shlex.quote(str(model_path))
               + ' perception_python:=' + shlex.quote(perception_python)
               + ' start_controller:=true occlusion_enabled:=true '
               + f'traffic_scenario:={scenario} '
               + f'distractor_color:={args.distractor_color} '
               + f'parked_vehicle_y:={args.parked_y} '
               + 'recovery_competition_enabled:=' + str(args.recovery_competition).lower() + ' '
               + 'predict_box_scale_velocity:=' + str(not args.hold_box_scale).lower() + ' '
               + 'overlap_confirmation_continuity:=' + str(not args.no_overlap_confirmation_continuity).lower() + ' '
               + 'smooth_recovery_setpoints:=' + str(args.smooth_recovery_setpoints).lower() + ' '
               + f'cpu_inference_threads:={args.cpu_inference_threads} '
               + f'detector_backend:={args.detector_backend} '
               + backend_launch_argument(args.backend_artifacts)
               + f'vehicle_speed:={args.vehicle_speed} occlusion_start:={args.occlusion_start} '
               + f'occlusion_duration:={args.occlusion_duration}')
        parameter_capture_pending = True
        last_status_log_s = -100.0
        while time.monotonic() - started < args.timeout:
            report_path = directory / 'report.json'
            if report_path.exists():
                try:
                    report = json.loads(report_path.read_text())
                except json.JSONDecodeError:
                    time.sleep(0.2)
                    continue
                outcome['report_passed'] = report['passed']
                print('Mission report: ' + json.dumps(report), flush=True)
                break
            for name, process in processes.items():
                if process.poll() is not None:
                    raise RuntimeError(f'{name} exited early with code {process.returncode}.')
            sample = latest_sample()
            if sample:
                check_sample_safety(sample)
                if time.monotonic() - last_status_log_s >= 10:
                    print(json.dumps({key: sample.get(key) for key in
                                      ('wall_s', 'state', 'position_ned', 'landed', 'target')}), flush=True)
                    last_status_log_s = time.monotonic()
                if parameter_capture_pending and sample.get('wall_s', 0) >= 10:
                    capture_parameters()
                    parameter_capture_pending = False
            time.sleep(0.5)
        else:
            raise RuntimeError('Trial exceeded supervisor timeout.')
    except (Exception, KeyboardInterrupt) as error:
        outcome['error'] = str(error) or 'KeyboardInterrupt'
        print('Trial error: ' + outcome['error'], flush=True)
    finally:
        sample = latest_sample()
        if sample and not safely_landed(sample) and 'px4' in processes and processes['px4'].poll() is None:
            interventions.append({'action': 'supervisor_safety_land',
                                  'wall_s': time.monotonic() - started})
            try:
                confirmed = safety_land(lambda: stop('mission'), lambda: command('commander', 'land'),
                                        latest_sample, safely_landed)
                outcome['safety_land_confirmed'] = confirmed
                if not confirmed:
                    outcome['safety_land_error'] = 'Landing/disarm not confirmed within 90 seconds.'
            except Exception as error:
                outcome['safety_land_error'] = str(error)
        outcome['landed_disarmed_before_shutdown'] = safely_landed(latest_sample())
        stop('mission')
        stop('crossing')
        stop('recorder')
        stop('gui')
        if 'px4' in processes and processes['px4'].poll() is None:
            try:
                command('shutdown')
            except Exception as error:
                outcome['shutdown_error'] = str(error)
        stop('px4')
        stop('agent')
        outcome['duration_s'] = time.monotonic() - started
        outcome['process_exit_codes'] = {name: process.poll() for name, process in processes.items()}
        if args.freeze_manifest:
            try:
                verify_freeze(root, args.freeze_manifest)
                outcome['freeze_verified'] = True
            except Exception as error:
                outcome['freeze_verified'] = False
                outcome['error'] = str(error)
        outcome['autonomous_passed'] = bool(outcome.get('report_passed')
                                           and not interventions and not outcome['error'])
        (directory / 'supervisor.json').write_text(json.dumps(outcome, indent=2) + '\n')
        for log in logs:
            log.close()
        print('Supervisor: ' + json.dumps(outcome), flush=True)
    return 0 if outcome['autonomous_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
