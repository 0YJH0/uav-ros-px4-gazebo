#!/usr/bin/env python3
"""Continue unattempted trials only; preserve the original freeze and failed rows."""

import argparse
import json
from pathlib import Path
import signal
import subprocess
import sys
import time

from vehicle_experiment_study import (ROOT, load_json, load_lines, publish_summary,
                                      trial_row, verify_freeze, write_json)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', required=True, type=Path)
    args = parser.parse_args()
    directory = args.study.resolve()
    plan = load_json(directory / 'experiment_plan.json')
    previous = load_json(directory / 'study_summary.json')
    rows = previous['trials']
    if [row['name'] for row in rows] != [trial['name'] for trial in plan[:len(rows)]]:
        raise RuntimeError('Previous records are not an exact prefix of the frozen plan.')
    manifest = directory / 'freeze_manifest.json'
    verify_freeze(ROOT, manifest)
    frozen = load_json(manifest)
    stopped, active = False, None
    write_json(directory / 'continuation.json', {
        'completed_prefix': len(rows), 'existing_rows_preserved': True,
        'reason': 'Original batch stopped after baseline_09 due to auxiliary pytest cache drift. '
                  'Only the generated nodeids cache was restored to its frozen value. '
                  'No detection, model, scene, control, or original supervisor code changed.',
        'resume_helper': str(Path(__file__).resolve())})

    def interrupt(signum, frame):
        nonlocal stopped
        stopped = True
        if active is not None and active.poll() is None:
            active.send_signal(signal.SIGINT)

    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    for trial in plan[len(rows):]:
        if stopped:
            break
        verify_freeze(ROOT, manifest)
        trial_dir = directory / trial['name']
        if trial_dir.exists():
            raise RuntimeError('Unrecorded trial directory exists; evidence cannot be overwritten.')
        command = [sys.executable, str(ROOT / 'scripts/run_vehicle_tracking_validation.py'),
                   '--output', str(trial_dir), '--model-path', frozen['model_path'],
                   '--vehicle-speed', str(trial['vehicle_speed']),
                   '--occlusion-start', str(trial['occlusion_start']),
                   '--occlusion-duration', str(trial['occlusion_duration']),
                   '--freeze-manifest', str(manifest)]
        with (directory / (trial['name']+'_supervisor.log')).open('x') as log:
            print(json.dumps({'started': trial['name'], 'completed': len(rows), 'planned': len(plan)}), flush=True)
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
        rows.append(row)
        publish_summary(directory, plan, rows)
        print(json.dumps({'finished': trial['name'], 'success': row['success'],
                          'visibility': row['visibility'], 'completed': len(rows)}), flush=True)
        verify_freeze(ROOT, manifest)
        time.sleep(3)
    write_json(directory / 'study_status.json', {'planned': len(plan), 'attempted': len(rows),
                                               'completed': len(rows) == len(plan), 'interrupted': stopped})
    return 0 if len(rows) == len(plan) else 2


if __name__ == '__main__':
    raise SystemExit(main())
