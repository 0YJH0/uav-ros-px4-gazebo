#!/usr/bin/env python3
"""Read-only stage timing and ULog safety audit of a completed vehicle study."""

import argparse
from pathlib import Path
import statistics

import numpy as np
from pyulog import ULog

from vehicle_experiment_study import digest, load_json, load_lines, percentile, write_json


def timing(values):
    return {'n': len(values), 'mean_s': statistics.mean(values) if values else None,
            'p95_s': percentile(values, 0.95), 'max_s': max(values, default=None)}


def analyze(study):
    summary = load_json(study / 'study_summary.json')
    result = {'study': str(study), 'trials': [], 'input_sha256': {}}
    result['input_sha256'][str(study / 'study_summary.json')] = digest(study / 'study_summary.json')
    for trial in summary['trials']:
        directory = Path(trial['directory'])
        for name in ('association.jsonl', 'samples.jsonl', 'flight.ulg'):
            path = directory / name
            result['input_sha256'][str(path)] = digest(path)
        samples = load_lines(directory / 'samples.jsonl')
        begin = next(row['wall_s'] for row in samples if row['state'] == 'APPROACH')
        end = next(row['wall_s'] for row in samples if row['wall_s'] > begin
                   and row['state'] in ('RETURN', 'LAND', 'DONE'))
        rows = [row for row in load_lines(directory / 'association.jsonl')
                if begin <= row['wall_s'] < end]
        stages = {key: timing([row[key] for row in rows if key in row]) for key in (
            'processing_s', 'target_publish_age_s', 'target_publish_s',
            'vehicles_publish_s', 'debug_render_publish_s', 'queue_wait_s')}
        for key in ('full_frame_yolo_s', 'gmc_s', 'bytetrack_s', 'roi_yolo_s', 'roi_merge_s'):
            stages[key] = timing([row['detector'][key] for row in rows
                                  if key in row.get('detector', {})])
        ulog = ULog(str(directory / 'flight.ulg'),
                    message_name_filter_list=['vehicle_status', 'failsafe_flags'])
        status = ulog.get_dataset('vehicle_status').data
        flags = ulog.get_dataset('failsafe_flags').data
        # Pair each flags observation with the last status at or before its timestamp.
        indices = np.searchsorted(status['timestamp'], flags['timestamp'], side='right') - 1
        valid = indices >= 0
        indices = np.maximum(indices, 0)
        armed = status['arming_state'] == 2
        offboard = valid & (status['nav_state'][indices] == 14) & armed[indices]
        landing = valid & (status['nav_state'][indices] == 18)
        lost = flags['offboard_control_signal_lost'] != 0
        safety = {'armed_status_observations': int(armed.sum()),
                  'armed_failsafe_observations': int(((status['failsafe'] != 0) & armed).sum()),
                  'armed_offboard_flags_observations': int(offboard.sum()),
                  'armed_offboard_lost_observations': int((offboard & lost).sum()),
                  'auto_land_lost_observations': int((landing & lost).sum()),
                  'dropout_events': len(ulog.dropouts)}
        result['trials'].append({'name': trial['name'], 'group': trial.get('group'),
                                 'window_wall_s': [begin, end], 'observations': len(rows),
                                 'timings': stages, 'ulog_safety': safety})
    result['limitations'] = [
        'Task window follows the study summary: sampled first APPROACH until first RETURN/LAND/DONE.',
        'processing_s excludes association JSON serialization/publication and terminal logging.',
        'target_publish_age_s starts at perception subscription receipt, not camera exposure; '
        'pre-subscription DDS delay and downstream controller receipt are not measured.',
        'Stage counts differ because ROI inference/merge are conditional; stage percentiles are not additive.',
        'ULog mode attribution uses latest preceding status; flags/status streams are sampled, not simultaneous.',
        'AUTO_LAND offboard-signal loss is separate from armed Offboard loss; no flag absence proves hardware safety.',
        'One observation per group cannot estimate repeatability or establish a causal coverage benefit.']
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    study = args.study.resolve()
    if args.output.exists() or args.output.resolve().is_relative_to(study):
        parser.error('--output must be a new external file; archived study evidence is read-only.')
    result = analyze(study)
    result['analysis_script_sha256'] = digest(Path(__file__))
    write_json(args.output, result)
    for trial in result['trials']:
        print(trial['name'], trial['ulog_safety'])


if __name__ == '__main__':
    main()
