#!/usr/bin/env python3
"""Timestamp-matched audit of previously correct frames rejected by a lock change."""

import argparse
import hashlib
import json
from pathlib import Path


def load(path):
    return {(row['stamp']['sec'], row['stamp']['nanosec']): row
            for row in map(json.loads, path.read_text().splitlines())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--guard', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--trial', default='crossing_03')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('New result file required.')
    original, guard, candidate = map(load, (args.original, args.guard, args.candidate))
    if original.keys() != guard.keys() or guard.keys() != candidate.keys():
        raise ValueError('Replay timestamps differ; no nearest-frame substitutions allowed.')
    trial = next(item for item in json.loads(args.report.read_text())['trials'] if item['trial'] == args.trial)
    lo, hi = trial['candidate']['identity_evaluation_window_wall_s']
    keys = [key for key, row in original.items() if lo <= row['wall_s'] < hi]
    rejected = [key for key in keys if original[key]['label']=='tracked_vehicle'
                and original[key]['identity_confirmed'] and not guard[key]['identity_confirmed']]
    result = {'previously_correct_rejected_frames': len(rejected),
              'restored_correct_frames': sum(candidate[key]['identity_confirmed'] and
                                             candidate[key]['label']=='tracked_vehicle' for key in rejected),
              'window_wall_s': [lo, hi],
              'wrong_identity_in_task': {name: sum(data[key]['identity_confirmed'] and
                  data[key]['label'] in ('crossing_vehicle', 'parked_vehicle') for key in keys)
                  for name, data in [('original', original), ('guard', guard), ('candidate', candidate)]},
              'frames': [{'stamp': guard[key]['stamp'], 'guard_reason': guard[key]['reason'],
                          'candidate_reason': candidate[key]['reason'], 'candidate_label': candidate[key]['label'],
                          'restored': candidate[key]['identity_confirmed'] and candidate[key]['label']=='tracked_vehicle'}
                         for key in rejected],
              'input_sha256': {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in (args.original, args.guard, args.candidate, args.report)},
              'limitation': 'Frozen detections and independent projection labels; not new flight accuracy.'}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key not in ('frames', 'input_sha256')}))


if __name__ == '__main__':
    main()
