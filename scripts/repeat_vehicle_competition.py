#!/usr/bin/env python3
"""Frozen, restart-per-trial A/B study with a single perception feature switch."""

import argparse
import json
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path

from audit_vehicle_ulog import audit_studies
from repeat_frozen_crossing import compiled_px4_rootfs, completed_trial, verify_installed
from vehicle_experiment_study import (ROOT, METRICS, digest, freeze, load_json,
                                      publish_summary, verify_freeze, write_json)


def make_plan(pairs):
    if pairs < 1:
        raise ValueError('pairs must be positive')
    plan = []
    for pair in range(1, pairs + 1):
        for enabled in ((False, True) if pair % 2 else (True, False)):
            plan.append({'name': f'crossing_{len(plan) + 1:02d}', 'pair': pair,
                         'group': 'competition' if enabled else 'baseline',
                         'recovery_competition_enabled': enabled, 'vehicle_speed': .8,
                         'occlusion_start': 15., 'occlusion_duration': 4., 'crossing': True})
    return plan


def make_latency_scale_plan(rounds):
    if rounds < 1:
        raise ValueError('rounds must be positive')
    configurations = [('baseline', True, 'torch'), ('scale_hold', False, 'torch'), ('openvino', True, 'openvino')]
    plan = []
    for round_index in range(rounds):
        order = configurations[round_index % 3:] + configurations[:round_index % 3]
        for group, scale_velocity, backend in order:
            plan.append({'name': f'crossing_{len(plan)+1:02d}', 'pair': round_index+1, 'group': group,
                         'vehicle_speed': .8, 'occlusion_start': 15., 'occlusion_duration': 4., 'crossing': True,
                         'recovery_competition_enabled': False, 'cpu_inference_threads': 0,
                         'predict_box_scale_velocity': scale_velocity, 'detector_backend': backend})
    return plan


def preserve_interpreter_path(path):
    # Resolving a venv's python symlink selects the system interpreter instead.
    return str(Path(path).absolute())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pairs', type=int, default=5)
    parser.add_argument('--model-path', type=Path, default=ROOT / 'yolo11s.pt')
    parser.add_argument('--latency-scale', action='store_true')
    parser.add_argument('--rounds', type=int, default=1)
    parser.add_argument('--backend-artifacts', type=Path)
    parser.add_argument('--perception-python', type=Path)
    args = parser.parse_args()
    plan = make_latency_scale_plan(args.rounds) if args.latency_scale else make_plan(args.pairs)
    if args.latency_scale and (not args.backend_artifacts or not args.perception_python):
        raise ValueError('Latency/scale study needs shared backend artifacts and one shared perception interpreter.')
    if args.backend_artifacts:
        for trial in plan:
            trial['backend_artifacts'] = str(args.backend_artifacts.resolve())
    directory, model = args.output.resolve(), args.model_path.resolve()
    if directory.exists():
        raise RuntimeError('New output directory required; never replace failed trials.')
    verify_installed(ROOT)
    rootfs = compiled_px4_rootfs(ROOT / 'PX4-Autopilot/build/px4_sitl_default/bin/px4')
    directory.mkdir(parents=True)
    write_json(directory / 'plan.json', plan)
    try:
        frozen = freeze(ROOT, directory, model, args.backend_artifacts)
    except Exception as exc:
        publish_summary(directory, plan, [])
        write_json(directory / 'study_status.json', {'planned': len(plan), 'attempted': 0,
                   'completed': False, 'interrupted': False, 'phase': 'freeze', 'error': repr(exc)})
        raise
    helpers = ('repeat_vehicle_competition.py', 'repeat_frozen_crossing.py',
               'audit_vehicle_ulog.py', 'vehicle_study_checks.py')
    helper_hashes = {name: digest(ROOT / 'scripts' / name) for name in helpers}
    (directory / 'reporting_helpers').mkdir()
    for name in helpers:
        shutil.copy2(ROOT / 'scripts' / name, directory / 'reporting_helpers' / name)
    write_json(directory / 'ab_protocol.json', {
        'pairs': args.rounds if args.latency_scale else args.pairs,
        'groups': list(dict.fromkeys(trial['group'] for trial in plan)),
        'only_runtime_difference': ('scale_hold: predict_box_scale_velocity; openvino: detector_backend'
                                    if args.latency_scale else 'perception_node.recovery_competition_enabled'),
        'order': 'Cyclic three-group order' if args.latency_scale else 'AB, BA alternation by pair; no retry or replacement',
        'perception_python': str(args.perception_python) if args.perception_python else '.venv-yolo/bin/python',
        'limitations': 'One round is an exploratory comparison, not repeated statistical evidence.',
        'px4_rootfs': str(rootfs), 'helper_sha256': helper_hashes,
        'safety_stop': 'Stop remaining trials on wrong identity, PX4 failsafe or supervisor intervention.',
        'limits': 'Independent restarts in a deterministic scene are not independent scene samples.'})
    METRICS.update({'after_last_overlap_confirmation_wall_s': 'max',
                    'scorable_identity_switches': 'max', 'wrong_identity_observations': 'max'})
    rows, stopped, active, error = [], False, None, None

    def verify():
        verify_freeze(ROOT, directory / 'freeze_manifest.json')
        verify_installed(ROOT)
        if any(digest(ROOT / 'scripts' / name) != checksum for name, checksum in helper_hashes.items()):
            raise RuntimeError('A/B helper changed during frozen study.')

    def interrupt(signum, frame):
        nonlocal stopped
        stopped = True
        if active is not None and active.poll() is None:
            active.send_signal(signal.SIGINT)

    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    publish_summary(directory, plan, rows)
    try:
        for trial in plan:
            if stopped:
                break
            verify()
            command = [sys.executable, str(ROOT / 'scripts/run_vehicle_tracking_validation.py'),
                       '--output', str(directory / trial['name']), '--model-path', frozen['model_path'],
                       '--freeze-manifest', str(directory / 'freeze_manifest.json'), '--crossing']
            if trial['recovery_competition_enabled']:
                command.append('--recovery-competition')
            if not trial.get('predict_box_scale_velocity', True):
                command.append('--hold-box-scale')
            if 'detector_backend' in trial:
                command.extend(['--detector-backend', trial['detector_backend']])
            if args.backend_artifacts:
                command.extend(['--backend-artifacts', str(args.backend_artifacts.resolve())])
            if args.perception_python:
                command.extend(['--perception-python', preserve_interpreter_path(args.perception_python)])
            print(json.dumps({'started': trial}), flush=True)
            with (directory / (trial['name'] + '_supervisor.log')).open('w') as log:
                active = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                returncode = active.wait()
                active = None
            row = completed_trial(directory / trial['name'], trial, returncode)
            row['pair'] = trial['pair']
            row['recovery_competition_enabled'] = trial['recovery_competition_enabled']
            rows.append(row)
            publish_summary(directory, plan, rows)
            audit_studies(directory, rootfs=rootfs)
            print(json.dumps({'finished': row}), flush=True)
            verify()
            supervisor = load_json(directory / trial['name'] / 'supervisor.json') or {}
            if (row.get('wrong_identity_observations', 0) or row.get('safety_event')
                    or supervisor.get('interventions')):
                error = 'safety_stop_after_' + trial['name']
                stopped = True
            time.sleep(3)
    except Exception as exc:
        error = repr(exc)
        raise
    finally:
        shutil.copytree(ROOT / 'ros2_ws/install/uav_learning/lib/python3.12/site-packages/uav_learning',
                        directory / 'installed_snapshot', ignore=shutil.ignore_patterns('__pycache__'))
        write_json(directory / 'study_status.json', {
            'planned': len(plan), 'attempted': len(rows), 'completed': len(rows) == len(plan),
            'interrupted': stopped, 'error': error})
    return 0 if len(rows) == len(plan) else 2


if __name__ == '__main__':
    raise SystemExit(main())
