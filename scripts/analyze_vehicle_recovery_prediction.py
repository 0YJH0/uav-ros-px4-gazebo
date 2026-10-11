#!/usr/bin/env python3
"""Reconstruct recorded Kalman decisions without changing detections or flight."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import shutil
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ros2_ws/src/uav_learning'))
from uav_learning.vehicle_target_lock import VehicleTargetLock
from vehicle_crossing_validation import classify_identity, iou
from vehicle_experiment_study import digest, load_json, load_lines, write_json
from vehicle_offline_truth import extend_truth


def measurement(candidate, width, height):
    box = candidate['bbox']
    return VehicleTargetLock.measurement((candidate['track_id'], 0., candidate['confidence'], *box), width, height)


def predict(lock, now):
    if now - lock.last_seen > lock.prediction_horizon:
        return lock.last_measurement.copy(), None
    dt = max(0., now - lock.last_predict)
    lock.last_predict = now
    transition = np.eye(8)
    transition[:4, 4:] = np.eye(4) * dt
    lock.filter.transitionMatrix = transition
    noise = np.zeros((8, 8))
    for axis, variance in enumerate([0.03**2] * 2 + [0.15**2] * 2):
        noise[axis, axis] = variance * dt**4 / 4
        noise[axis, axis + 4] = noise[axis + 4, axis] = variance * dt**3 / 2
        noise[axis + 4, axis + 4] = variance * dt**2
    lock.filter.processNoiseCov = noise
    predicted = lock.filter.predict()[:4].copy()
    covariance = lock.filter.errorCovPre[:4, :4] + lock.filter.measurementNoiseCov
    return predicted, covariance


def reconstruct(directory):
    associations = load_lines(directory / 'association.jsonl')
    truth = {(row['stamp']['sec'], row['stamp']['nanosec']): row
             for row in load_lines(directory / 'identity_observations.jsonl')}
    truth, calibration = extend_truth(directory, truth, associations, ROOT)
    settings = load_json(directory / 'runtime_parameters.json')['perception_node']
    module = 'ros2_ws/src/uav_learning/uav_learning/vehicle_target_lock.py'
    snapshot = load_json(directory / 'implementation_snapshot.json')
    if digest(ROOT / module) != snapshot['source_sha256'][module]:
        raise RuntimeError('Current Kalman implementation differs from the executed trial.')
    if not settings['predict_box_scale_velocity']:
        raise ValueError('This audit reconstructs the recorded scale-velocity-enabled configuration.')
    search = next(row['time_s'] for row in load_json(directory / 'report.json')['transitions']
                  if row['state'] == 'SEARCH')
    seed = next(index for index, row in enumerate(associations)
                if row['wall_s'] >= search and row['mode'] == 'acquiring'
                and row['identity_confirmed'])
    width, height = associations[seed]['image_shape'][::-1]
    lock = VehicleTargetLock(recovery_timeout=settings['target_reacquire_timeout'])
    rows, discrepancies, errors = [], [], {'center': [], 'log_scale': [], 'mahalanobis': []}
    for index, row in enumerate(associations[seed:], start=seed):
        selected = next((candidate for candidate in row['candidates'] if candidate.get('accepted')), None)
        predicted, covariance = None, None
        if index == seed:
            now = 0.
        else:
            # Logged elapsed time uses the actual association clock, avoiding DDS/observer jitter.
            now = lock.last_seen + row['elapsed_since_confirmed_s']
            lock.compensate_camera_motion(row.get('camera_motion', {}).get('warp_px'), width, height)
            if row['reason'] not in ('stale_queued_frame', 'out_of_order_frame', 'processing_error'):
                predicted, covariance = predict(lock, now)
        reconstructed = []
        evidence = truth.get((row['stamp']['sec'], row['stamp']['nanosec']), {})
        boxes = evidence.get('projected_boxes', {})
        for candidate in row['candidates']:
            entry = dict(candidate)
            label, scores = classify_identity(candidate['bbox'], boxes) if boxes else ('unscorable', {})
            entry.update(independent_label=label, projection_ious=scores)
            if predicted is not None and 'center_error' in candidate:
                observed = measurement(candidate, width, height)
                residual = observed - predicted
                center = float(np.linalg.norm(residual[:2]))
                scale = float(np.max(np.abs(residual[2:])))
                errors['center'].append(abs(center - candidate['center_error']))
                errors['log_scale'].append(abs(scale - candidate['log_scale_error']))
                if abs(scale - candidate['log_scale_error']) > 1e-5:
                    discrepancies.append({'wall_s': row['wall_s'], 'candidate_index': candidate['index'],
                                          'scale': scale, 'logged_scale': candidate['log_scale_error'],
                                          'center': center, 'logged_center': candidate['center_error']})
                if covariance is not None:
                    distance = float((residual.T @ np.linalg.solve(covariance, residual)).item())
                    errors['mahalanobis'].append(abs(distance - candidate['mahalanobis_distance']))
                entry.update(center_residual_px=(residual[:2, 0] * [width, height]).tolist(),
                             size_ratio_observed_to_predicted=np.exp(residual[2:, 0]).tolist())
            reconstructed.append(entry)
        rows.append({'wall_s': row['wall_s'], 'stamp': row['stamp'], 'reason': row['reason'],
                     'identity_confirmed': row['identity_confirmed'],
                     'elapsed_since_confirmed_s': row['elapsed_since_confirmed_s'],
                     'mode': row['mode'], 'identity_guard': row.get('identity_guard'),
                     'predicted_box': None if predicted is None else lock.view_box(predicted, width, height).tolist(),
                     'projected_boxes': boxes, 'truth_label': evidence.get('label'),
                     'pose_age_sim_s': evidence.get('pose_age_sim_s'),
                     'candidates': reconstructed})
        if selected is not None:
            observed = measurement(selected, width, height)
            if index == seed or now - lock.last_seen > lock.prediction_horizon:
                lock.reset_prediction(observed, now)
            else:
                lock.filter.correct(observed)
                state = lock.filter.statePost.copy()
                state[4:6] = np.clip(state[4:6], -0.15, 0.15)
                state[6:] = np.clip(state[6:], -0.3, 0.3)
                lock.filter.statePost = state
            lock.last_measurement = observed.copy()
            lock.last_seen = now
        rows[-1]['posterior_velocity'] = lock.filter.statePost[4:, 0].tolist()
    validation = {key: {'n': len(values), 'max_abs_error': max(values, default=None)}
                  for key, values in errors.items()}
    if any(max(values, default=0.) > 1e-5 for values in errors.values()):
        raise RuntimeError('Reconstructed predictions disagree with recorded residuals: '
                           + str(validation) + '; first discrepancies=' + str(discrepancies[:8]))
    return rows, {'seed_stamp': associations[seed]['stamp'], 'seed_wall_s': associations[seed]['wall_s'],
                  'projection_calibration': calibration, 'residual_validation': validation}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.output.resolve().is_relative_to(args.trial.resolve()):
        parser.error('Use a new external analysis directory; trial evidence stays read-only.')
    rows, validation = reconstruct(args.trial)
    report = load_json(args.trial / 'report.json')
    losses = []
    for event in report['events']:
        if event['event'] != 'TRACK_TARGET_LOST':
            continue
        start = event['time_s']
        end = next(item['time_s'] for item in report['events']
                   if item['time_s'] > start and item['event'] in ('TARGET_RECOVERED', 'TRACK_REACQUIRED'))
        frames = [row for row in rows if start - 2 <= row['wall_s'] < end]
        rejected = [candidate for row in frames if not row['identity_confirmed']
                    for candidate in row['candidates'] if candidate['independent_label'] == 'tracked_vehicle']
        losses.append({'start_wall_s': start, 'end_wall_s': end, 'duration_wall_s': end - start,
                       'diagnostic_window_wall_s': [start - 2, end],
                       'uniquely_matched_target_unconfirmed_candidates': len(rejected),
                       'uniquely_matched_target_gate_rejected_candidates': sum(
                           bool(candidate.get('rejection_reasons')) for candidate in rejected),
                       'uniquely_matched_target_pending_candidates': sum(
                           candidate.get('reason') == 'pending_confirmation' for candidate in rejected),
                       'target_rejection_reasons': dict(Counter(reason for candidate in rejected
                            for reason in candidate.get('rejection_reasons', []))),
                       'frames': len(frames)})
    args.output.mkdir(parents=True)
    source_paths = [Path(__file__), ROOT / 'scripts/vehicle_offline_truth.py',
                    ROOT / 'scripts/vehicle_crossing_validation.py',
                    ROOT / 'ros2_ws/src/uav_learning/uav_learning/vehicle_target_lock.py']
    inputs = [args.trial / name for name in ('association.jsonl', 'identity_observations.jsonl',
              'identity_poses.jsonl', 'identity_camera_info.json', 'runtime_parameters.json',
              'implementation_snapshot.json', 'report.json')]
    for source in source_paths:
        shutil.copy2(source, args.output / source.name)
    with (args.output / 'prediction_frames.jsonl').open('w') as stream:
        for row in rows:
            stream.write(json.dumps(row, allow_nan=False) + '\n')
    result = {'trial': str(args.trial.resolve()), **validation, 'losses': losses,
              'source_sha256': {str(path): digest(path) for path in source_paths},
              'input_sha256': {str(path): digest(path) for path in inputs},
              'limitations': [
                  'Recorded acceptance is forced for state reconstruction, not a candidate algorithm replay.',
                  'Relative association times are recovered from logged elapsed-since-confirmed, not observer wall intervals.',
                  'Projection labels are independent bounding-volume matches; overlap/panel/missing truth is unscorable.',
                  'Projection in frame does not establish visibility; saved raw images need visual inspection.',
                  'No detector/tracker rerun, no changed trajectory, no new flight or coverage claim.',
                  'Loss diagnostic windows include two seconds before the controller loss event.']}
    write_json(args.output / 'report.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
