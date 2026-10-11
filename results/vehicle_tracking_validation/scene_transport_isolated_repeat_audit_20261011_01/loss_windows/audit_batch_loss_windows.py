import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import sys

ROOT = Path('/home/yjh/ROS2_manmade')
sys.path.insert(0, str(ROOT / 'scripts'))
from vehicle_crossing_validation import classify_identity
from vehicle_experiment_study import digest, load_json, load_lines, write_json
from vehicle_offline_truth import extend_truth

parser = argparse.ArgumentParser()
parser.add_argument('--study', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
study, output = args.study.resolve(), args.output.resolve()
if output.exists() or output.is_relative_to(study):
    raise RuntimeError('Use a new external output directory.')
status = load_json(study / 'study_status.json')
if status['active_trial'] or not status['completed'] and not status['error']:
    raise RuntimeError('Wait for the batch to finish.')
output.mkdir(parents=True)
trials = []
for trial in load_json(study / 'study_summary.json')['trials']:
    directory = Path(trial['directory'])
    report = load_json(directory / 'report.json')
    if not report:
        trials.append({'name': trial['name'], 'missing_report': True})
        continue
    losses = [event for event in report['events'] if event['event'] == 'TRACK_TARGET_LOST'
              and not any(panel['start_wall_s'] <= event['time_s'] <= panel['end_wall_s']
                          for panel in report['occlusions'] if panel.get('end_wall_s') is not None)]
    associations = load_lines(directory / 'association.jsonl')
    truth = {(row['stamp']['sec'], row['stamp']['nanosec']): row
             for row in load_lines(directory / 'identity_observations.jsonl')}
    truth, calibration = extend_truth(directory, truth, associations, study / 'frozen_files')
    windows = []
    for loss in losses:
        start = loss['time_s']
        terminal = next((event for event in report['events'] if event['time_s'] > start
                         and event['event'] in ('TARGET_RECOVERED', 'TRACK_REACQUIRED', 'RECOVERY_TIMEOUT')), None)
        end = terminal['time_s'] if terminal else report['wall_duration_s']
        frames = [row for row in associations if start-1.2 <= row['wall_s'] <= end+.2]
        candidates = []
        for row in frames:
            stamp = row['stamp']['sec'], row['stamp']['nanosec']
            evidence = truth.get(stamp, {})
            boxes = evidence.get('projected_boxes', {})
            for candidate in row['candidates']:
                label, scores = classify_identity(candidate['bbox'], boxes) if boxes else ('unscorable', {})
                candidates.append({'wall_s': row['wall_s'], 'stamp': row['stamp'],
                    'within_loss': start <= row['wall_s'] < end,
                    'identity_confirmed': row['identity_confirmed'],
                    'independent_label': label, 'projection_ious': scores,
                    'pose_age_sim_s': evidence.get('pose_age_sim_s'), **candidate})
        rejected = [candidate for candidate in candidates if candidate['within_loss']
                    and candidate['independent_label'] == 'tracked_vehicle'
                    and not candidate['identity_confirmed'] and not candidate.get('accepted')]
        during = [row for row in frames if start <= row['wall_s'] < end]
        windows.append({'start_wall_s': start, 'end_wall_s': end,
            'duration_wall_s': end-start, 'terminal': terminal['event'] if terminal else None,
            'diagnostic_window_wall_s': [start-1.2, end+.2],
            'loss_frame_reason_counts': dict(Counter(row['reason'] for row in during)),
            'uniquely_matched_target_unconfirmed_candidates': len(rejected),
            'target_rejection_reasons': dict(Counter(reason for candidate in rejected
                                                   for reason in candidate.get('rejection_reasons', []))),
            'target_waiting_reasons': dict(Counter(candidate.get('reason') for candidate in rejected)),
            'max_association_interval_in_neighborhood_s': max(
                (b['wall_s']-a['wall_s'] for a, b in zip(frames, frames[1:])), default=None),
            'candidates': candidates})
    trials.append({'name': trial['name'], 'coverage': trial['visibility'],
                   'nonplanned_losses': windows, 'projection_calibration': calibration,
                   'input_sha256': {name: digest(directory / name) for name in (
                        'report.json', 'association.jsonl', 'identity_observations.jsonl',
                        'identity_poses.jsonl', 'identity_camera_info.json')}})
result = {'trials': trials, 'limitations': [
    'Recorded decisions are analyzed without rerunning detection, tracking or control.',
    'Projection matches use bounding volumes, not instance masks or proof of visibility.',
    'No Kalman state is reconstructed; gate reasons are the original recorded reasons.',
    'Diagnostic context extends 1.2 seconds before and 0.2 seconds after the loss.',
    'Rejected original-target counts only include frames within the loss interval.',
    'Reasons and processing latency describe evidence, not isolated causal attribution.']}
sources = [Path(__file__), ROOT / 'scripts/vehicle_crossing_validation.py',
           ROOT / 'scripts/vehicle_offline_truth.py']
result['source_sha256'] = {str(path): digest(path) for path in sources}
write_json(output / 'nonplanned_loss_audit.json', result)
for path in sources:
    shutil.copy2(path, output / path.name)
print(json.dumps([{'name': row['name'], 'losses': [{key: value for key, value in loss.items()
    if key != 'candidates'} for loss in row.get('nonplanned_losses', [])]} for row in trials], indent=2))
