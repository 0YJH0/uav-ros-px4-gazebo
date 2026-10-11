#!/usr/bin/env python3
"""Run the separate identity study against an already completed frozen baseline."""

import argparse
import json
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from vehicle_experiment_study import (ROOT, digest, load_json, load_lines,
                                      publish_summary, trial_row, verify_freeze, write_json)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    base, directory = args.study.resolve(), args.output.resolve()
    status = load_json(base / 'study_status.json')
    if not status or not status.get('completed'):
        raise RuntimeError('Complete the baseline and grouped study before the separate crossing study.')
    if directory.exists():
        raise RuntimeError('Use a new output directory; evidence is never overwritten.')
    manifest = base / 'freeze_manifest.json'
    verify_freeze(ROOT, manifest)
    frozen = load_json(manifest)
    directory.mkdir(parents=True)
    helpers = [ROOT / 'scripts' / name for name in ('vehicle_crossing_validation.py', 'run_vehicle_crossing_study.py')]
    helper_hashes = {str(path.relative_to(ROOT)): digest(path) for path in helpers}
    for path in helpers:
        shutil.copy2(path, directory / path.name)
    write_json(directory / 'crossing_freeze.json', {'core_manifest': str(manifest),
                'core_manifest_sha256': digest(manifest), 'helper_sha256': helper_hashes,
                'scenario': {'crossing_start_sim_s': 35., 'crossing_duration_sim_s': 8.,
                             'lateral_span_m': 9., 'forward_offset_m': -2.}})
    plan = [{'name': f'crossing_{index:02d}', 'group': 'crossing_identity', 'vehicle_speed': 0.8,
             'occlusion_start': 15., 'occlusion_duration': 4., 'crossing': True} for index in range(1, 6)]
    write_json(directory / 'experiment_plan.json', plan)
    rows, stopped, active = [], False, None

    def verify():
        verify_freeze(ROOT, manifest)
        if any(digest(ROOT / name) != checksum for name, checksum in helper_hashes.items()):
            raise RuntimeError('Crossing helper changed after its stage freeze.')

    def interrupt(signum, frame):
        nonlocal stopped
        stopped = True
        if active is not None and active.poll() is None:
            active.send_signal(signal.SIGINT)

    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    publish_summary(directory, plan, rows)
    for trial in plan:
        if stopped:
            break
        verify()
        trial_dir = directory / trial['name']
        command = [sys.executable, str(ROOT / 'scripts/run_vehicle_tracking_validation.py'),
                   '--output', str(trial_dir), '--model-path', frozen['model_path'],
                   '--freeze-manifest', str(manifest), '--crossing']
        with (directory / (trial['name']+'_supervisor.log')).open('w') as log:
            print(json.dumps({'started': trial['name'], 'completed': len(rows)}), flush=True)
            active = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            last_update = 0
            while active.poll() is None:
                if time.monotonic()-last_update >= 30:
                    samples = load_lines(trial_dir / 'samples.jsonl')
                    last = samples[-1] if samples else {}
                    print(json.dumps({'active': trial['name'], 'wall_s': last.get('wall_s'),
                                      'state': last.get('state')}), flush=True)
                    last_update = time.monotonic()
                time.sleep(1)
            returncode, active = active.returncode, None
        row = trial_row(trial_dir, trial)
        row['returncode'] = returncode
        if returncode:
            row['success'] = False
            row['failure_reasons'].append(f'supervisor_exit_{returncode}')
        identity = load_json(trial_dir / 'identity_report.json') or {}
        row['identity_independently_verified'] = identity.get('identity_independently_verified', False)
        row['wrong_identity_observations'] = identity.get('wrong_identity_observations')
        row['identity_report_available'] = bool(identity)
        row['identity_pass'] = bool(row['success'] and row['identity_independently_verified'])
        rows.append(row)
        publish_summary(directory, plan, rows)
        write_json(directory / 'identity_summary.json', {
            'attempted': len(rows), 'planned': len(plan),
            'identity_passes': sum(item['identity_pass'] for item in rows),
            'identity_verified': sum(item['identity_independently_verified'] for item in rows),
            'reports_missing': sum(not item['identity_report_available'] for item in rows),
            'trials': rows})
        print(json.dumps({'finished': trial['name'], 'mission_pass': row['success'],
                          'identity_pass': row['identity_pass'], 'identity': identity}), flush=True)
        verify()
        time.sleep(3)
    write_json(directory / 'study_status.json', {'planned': len(plan), 'attempted': len(rows),
                                               'completed': len(rows) == len(plan), 'interrupted': stopped})
    return 0 if len(rows) == len(plan) else 2


if __name__ == '__main__':
    raise SystemExit(main())
