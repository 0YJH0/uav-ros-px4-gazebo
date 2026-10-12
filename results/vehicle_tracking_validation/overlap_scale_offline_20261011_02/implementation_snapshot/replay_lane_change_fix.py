#!/usr/bin/env python3
"""Read-only, frozen-candidate comparison; never a closed-loop coverage result."""

import argparse
from collections import Counter
import hashlib
import importlib.util
import inspect
import json
import math
from pathlib import Path
import shutil
import sys

ROOT = Path('/home/yjh/ROS2_manmade')
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'ros2_ws/src/uav_learning')]

import numpy as np
from replay_vehicle_identity import appearance_proxy, stamp_key, time_proxy
from vehicle_crossing_validation import evaluate_identity, IDENTITY_EVALUATION_VERSION
from vehicle_offline_truth import extend_truth

TRIAL = ROOT / 'results/vehicle_tracking_validation/red_lane_change_gui_20261011_01'
MODULE = Path('ros2_ws/src/uav_learning/uav_learning/vehicle_target_lock.py')
DEPENDENCY = Path('ros2_ws/src/uav_learning/uav_learning/vehicle_recovery_competition.py')


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def clean(value):
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, (np.integer, np.floating)):
        return clean(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def load_implementation(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class InstrumentedLock(module.VehicleTargetLock):
        def crossing_risk(self, *args, **kwargs):
            self.replay_prediction = np.asarray(args[2]).copy()
            return super().crossing_risk(*args, **kwargs)

    return InstrumentedLock


def clock(associations, seed):
    """Rebuild the original select clock, not this replay's last-seen clock."""
    last_original_confirmed = float(associations[seed]['wall_s'])
    times = [None] * len(associations)
    times[seed] = last_original_confirmed
    for index in range(seed + 1, len(associations)):
        row = associations[index]
        elapsed = row.get('elapsed_since_confirmed_s')
        if elapsed is None:
            raise RuntimeError(f'Unmodelled reset or early processing error at {index}.')
        times[index] = last_original_confirmed + float(elapsed)
        if times[index] < times[index - 1]:
            raise RuntimeError('Original association clock became nonmonotonic.')
        if row['identity_confirmed']:
            last_original_confirmed = times[index]
    return times


def unplanned_windows(report):
    result = []
    events = report['events']
    for index, event in enumerate(events):
        if event['event'] != 'TRACK_TARGET_LOST':
            continue
        if any(o['start_wall_s'] <= event['time_s'] <= o['end_wall_s']
               for o in report['occlusions']):
            continue
        gap = next((e['time_s'] for e in reversed(events[:index])
                    if e['event'] == 'TRACK_OBSERVATION_GAP'), event['time_s'])
        end = next(e['time_s'] for e in events[index + 1:]
                   if e['event'] in ('TARGET_RECOVERED', 'TRACK_REACQUIRED'))
        result.append({'gap_start_wall_s': gap, 'loss_wall_s': event['time_s'],
                       'original_recovered_wall_s': end})
    return result


def window_summary(rows, start, end):
    selected = [row for row in rows if start <= row['wall_s'] <= end]
    predicted_heights = [r['predicted_box'][3] - r['predicted_box'][1] for r in selected
                         if r.get('predicted_box') is not None]
    correct = [r for r in selected if r['label'] == 'tracked_vehicle']
    strong_correct = [r for r in selected if r['strong_correct_candidate_count'] > 0]
    correct_rejections = Counter(reason for r in selected for d in r['candidates']
                                 if d['independent_identity']['label'] == 'tracked_vehicle'
                                 and not d.get('accepted') for reason in d.get('rejection_reasons', []))
    accepted_merged = [r for r in selected if r['identity_confirmed']
                       and r['identity_reason'] in ('multiple_vehicle_support',
                                                    'contained_competitor_ambiguous')]
    errors = [r['predicted_log_scale_error_to_best_correct'] for r in selected
              if r.get('predicted_log_scale_error_to_best_correct') is not None]
    return {
        'observations': len(selected),
        'confirmed_frames': sum(r['identity_confirmed'] for r in selected),
        'independent_labels': dict(Counter(r['label'] for r in selected)),
        'strong_correct_candidate_frames': len(strong_correct),
        'correct_target_confirmed_frames': len(correct),
        'first_correct_confirmation_wall_s': correct[0]['wall_s'] if correct else None,
        'first_correct_confirmation_delay_from_window_start_s': correct[0]['wall_s'] - start if correct else None,
        'accepted_merged_ambiguous_frames': len(accepted_merged),
        'correct_candidate_rejection_reasons': dict(correct_rejections),
        'predicted_height_px_range': [min(predicted_heights), max(predicted_heights)] if predicted_heights else None,
        'predicted_log_scale_error_to_correct_median': float(np.median(errors)) if errors else None,
        'predicted_log_scale_error_to_correct_max': max(errors) if errors else None,
    }


def run(implementation, associations, truth, params, seed, times, report, overrides=None):
    setting_names = ('acquisition_center_gate', 'confidence_threshold',
                     'weak_idless_confirm_frames', 'weak_idless_max_age',
                     'recovery_competition_enabled', 'predict_box_scale_velocity')
    signature = inspect.signature(implementation)
    settings = {k: params[k] for k in setting_names if k in params and k in signature.parameters}
    settings.update(recovery_timeout=params['target_reacquire_timeout'], acquisition_confirm_frames=1)
    settings.update(overrides or {})
    lock = implementation(**settings)
    result = []
    seeded_reference = None
    for index in range(seed, len(associations)):
        data = associations[index]
        height, width = data['image_shape']
        candidates, histograms, original = [], [], []
        for entry in data['candidates']:
            if data['reason'] == 'stale_inference_result':
                continue
            box, confidence = entry['bbox'], entry['confidence']
            if confidence is None or len(box) != 4 or any(x is None or not math.isfinite(x) for x in box):
                continue
            area = max(0., box[2] - box[0]) * max(0., box[3] - box[1])
            if area / (width * height) < params['min_area_ratio']:
                continue
            if index == seed and not entry['accepted']:
                continue
            candidates.append((entry['track_id'], area, confidence, *box))
            histograms.append(appearance_proxy(1. if index == seed else entry.get('appearance_similarity')))
            original.append(entry)
        lock.replay_prediction = None
        previous_measurement = None if lock.last_measurement is None else lock.last_measurement.copy()
        state_before = lock.filter.statePost.copy()
        selected = lock.select(candidates, histograms, width, height, times[index],
                               camera_motion=data.get('camera_motion', {}).get('warp_px'))
        if index == seed:
            seeded_reference = None if lock.reference is None else lock.reference.copy()
        if seeded_reference is not None and not np.array_equal(lock.reference, seeded_reference):
            raise RuntimeError('Implementation updates appearance template; logged fixed-reference proxies are insufficient.')
        accepted = None if selected is None else list(selected[3:])
        evidence = truth.get(stamp_key(data))
        boxes = evidence.get('projected_boxes', {}) if evidence else {}
        evaluation = evaluate_identity(accepted, boxes) if boxes else {
            'label': 'missing_matched_truth' if not evidence else evidence['label'],
            'reason': 'no_projected_boxes', 'scores': {}}
        diagnostics = []
        scale_errors = []
        for position, (candidate, diagnostic) in enumerate(zip(candidates, lock.diagnostics)):
            candidate_eval = evaluate_identity(list(candidate[3:]), boxes) if boxes else {
                'label': 'missing_matched_truth', 'reason': 'no_projected_boxes'}
            diagnostics.append({**diagnostic, 'independent_identity': candidate_eval,
                                'original_accepted': original[position]['accepted'],
                                'original_rejection_reasons': original[position].get('rejection_reasons', [])})
            if candidate_eval['label'] == 'tracked_vehicle' and lock.replay_prediction is not None:
                scale_errors.append(float(np.max(np.abs(
                    lock.measurement(candidate, width, height)[2:] - lock.replay_prediction[2:]))))
        predicted = lock.replay_prediction
        row = {
            'index': index, 'stamp': data['stamp'], 'wall_s': data['wall_s'],
            'association_clock_s': times[index], 'phase': evidence.get('phase') if evidence else None,
            'identity_confirmed': selected is not None,
            'frozen_identity_confirmed': data['identity_confirmed'],
            'frozen_accepted_box': next((e['bbox'] for e in data['candidates'] if e['accepted']), None),
            'locked_track_id': lock.target_id, 'accepted_box': accepted,
            'reason': lock.reason, 'label': evaluation['label'],
            'identity_reason': evaluation['reason'], 'independent_identity': evaluation,
            'candidate_count': len(candidates),
            'strong_correct_candidate_count': sum(d['independent_identity']['label'] == 'tracked_vehicle'
                                                  and d['confidence'] >= params['confidence_threshold']
                                                  for d in diagnostics),
            'candidates': diagnostics,
            'predicted_box': None if predicted is None else lock.view_box(predicted, width, height),
            'predicted_log_scale_error_to_best_correct': min(scale_errors) if scale_errors else None,
            'last_measurement_before': previous_measurement,
            'state_before': state_before,
            'state_after': lock.filter.statePost.copy(),
            'elapsed_since_seen_s': lock.elapsed_since_seen,
            'guard_active': lock.overlap_guard_active,
            'guard_reason': lock.overlap_guard_reason,
            'crossing_risk_evidence': lock.crossing_risk_diagnostic,
            'competition': lock.competition_diagnostic,
        }
        result.append(clean(row))
    begin = next(x['time_s'] for x in report['transitions'] if x['state'] == 'TRACK')
    end = next(x['time_s'] for x in report['transitions'] if x['state'] == 'RETURN')
    mismatch = [r['index'] for r in result if r['identity_confirmed'] != r['frozen_identity_confirmed']]
    selected_mismatch = [r['index'] for r in result if r['accepted_box'] != r['frozen_accepted_box']]
    windows = [{**window, **window_summary(result, window['gap_start_wall_s'],
                                           window['original_recovered_wall_s'])}
               for window in unplanned_windows(report)]
    summary = {
        'implementation_settings': settings,
        'frozen_confirmation_disagreement_indices': mismatch,
        'frozen_selected_box_disagreement_indices': selected_mismatch,
        'historical_follow_window_wall_s': [begin, end],
        'fixed_reference_unchanged': True,
        'all_frame_labels': dict(Counter(r['label'] for r in result)),
        **window_summary(result, begin, end), **time_proxy(result, report),
        'unplanned_loss_windows': windows,
    }
    return summary, result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--baseline-only', action='store_true')
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError('Output must be a new directory.')
    associations = read_jsonl(TRIAL / 'association.jsonl')
    original_truth = {stamp_key(row): row for row in read_jsonl(TRIAL / 'identity_observations.jsonl')}
    report = json.loads((TRIAL / 'report.json').read_text())
    params = json.loads((TRIAL / 'runtime_parameters.json').read_text())['perception_node']
    seed = next(i for i, row in enumerate(associations)
                if row['wall_s'] > 60 and row['identity_confirmed']
                and row.get('elapsed_since_confirmed_s') is None)
    original_seed = next(e for e in associations[seed]['candidates'] if e['accepted'])
    seed_truth = original_truth.get(stamp_key(associations[seed]), {})
    if evaluate_identity(original_seed['bbox'], seed_truth.get('projected_boxes', {}))['label'] != 'tracked_vehicle':
        raise RuntimeError('Post-airborne-reset frozen seed is not independently correct.')
    times = clock(associations, seed)
    truth, reconstruction = extend_truth(TRIAL, original_truth, associations, ROOT)
    frozen = TRIAL / 'executed_sources' / MODULE
    if (TRIAL / 'executed_sources' / DEPENDENCY).read_bytes() != (ROOT / DEPENDENCY).read_bytes():
        raise RuntimeError('Recovery competition dependency changed; isolate imports before replay.')
    paths = {'frozen': frozen}
    arm_overrides = {'frozen': {}}
    if not args.baseline_only:
        for name, overlap, scale in [('current_disabled', False, False), ('overlap_only', True, False),
                                      ('scale_only', False, True), ('both', True, True)]:
            paths[name] = ROOT / MODULE
            arm_overrides[name] = {'overlap_candidate_recovery': overlap, 'bounded_scale_prediction': scale}
    source_hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    summaries, all_rows = {}, {}
    for name, path in paths.items():
        summaries[name], all_rows[name] = run(load_implementation(path, name + '_lock'), associations,
                                             truth, params, seed, times, report, arm_overrides[name])
    baseline = summaries['frozen']
    if baseline['frozen_confirmation_disagreement_indices'] or baseline['frozen_selected_box_disagreement_indices']:
        raise RuntimeError('Frozen replay does not reproduce source selections: ' + json.dumps({
            k: baseline[k] for k in ('frozen_confirmation_disagreement_indices',
                                    'frozen_selected_box_disagreement_indices')}))
    if 'current_disabled' in summaries and (
            summaries['current_disabled']['frozen_confirmation_disagreement_indices'] or
            summaries['current_disabled']['frozen_selected_box_disagreement_indices']):
        raise RuntimeError('Disabled-feature implementation changed original selections.')
    if source_hashes != {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}:
        raise RuntimeError('Implementation changed during replay; discard this run.')
    args.output.mkdir(parents=True)
    snapshot = args.output / 'implementation_snapshot'
    snapshot.mkdir()
    for name, path in paths.items():
        shutil.copy2(path, snapshot / (name + '_vehicle_target_lock.py'))
    for path in (Path(__file__), ROOT / DEPENDENCY,
                 ROOT / 'scripts/vehicle_crossing_validation.py', ROOT / 'scripts/vehicle_offline_truth.py'):
        shutil.copy2(path, snapshot / path.name)
    for name, rows in all_rows.items():
        (args.output / (name + '.jsonl')).write_text(''.join(json.dumps(r, allow_nan=False) + '\n' for r in rows))
    output = {
        'source_trial': str(TRIAL), 'seed_index': seed,
        'seed_stamp': associations[seed]['stamp'], 'seed_wall_s': associations[seed]['wall_s'],
        'identity_evaluation_version': IDENTITY_EVALUATION_VERSION,
        'truth_reconstruction': reconstruction, 'summaries': summaries,
        'input_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                         (TRIAL / 'association.jsonl', TRIAL / 'identity_observations.jsonl',
                          TRIAL / 'identity_poses.jsonl', TRIAL / 'runtime_parameters.json',
                          TRIAL / 'report.json')},
        'implementation_sha256': {name: hashlib.sha256(p.read_bytes()).hexdigest() for name, p in paths.items()},
        'limitations': [
            'Replay uses frozen YOLO candidates, ByteTrack IDs, GMC transforms and the original aircraft trajectory.',
            'Perception association time is reconstructed from original elapsed-since-confirmed values, never replay decisions or logger receipt jitter.',
            'Only logged correlation to the frozen appearance reference is reconstructed; pixel appearance and new detector/ROI outputs are not rerun.',
            'The exact frozen confirmed seed after airborne reset is supplied, so acquisition is not tested.',
            'Independent projected bounding boxes are used only after decisions, never passed to the target lock.',
            'The confirmation-time fraction uses the historical TRACK-to-RETURN window and 0.5 s receipt TTL; it is a fixed-trajectory proxy, not actual flight coverage.',
            'Exclusive-projection v2 still does not prove instance-mask identity on every overlap frame.',
            'No claims about new closed-loop recovery, safety, or scene service transport follow from this offline replay.',
        ],
    }
    for name in paths:
        if name == 'frozen':
            continue
        begin, end = baseline['historical_follow_window_wall_s']
        pairs = [(frozen, candidate) for frozen, candidate in zip(all_rows['frozen'], all_rows[name])
                 if begin <= frozen['wall_s'] <= end]
        output.setdefault('comparison_in_historical_follow_window', {})[name] = {
            'new_correct_confirmed_indices': [c['index'] for f, c in pairs
                                             if c['label'] == 'tracked_vehicle' and f['label'] != 'tracked_vehicle'],
            'lost_correct_confirmed_indices': [c['index'] for f, c in pairs
                                              if c['label'] != 'tracked_vehicle' and f['label'] == 'tracked_vehicle'],
            'new_wrong_indices': [c['index'] for f, c in pairs
                                  if c['label'] in ('crossing_vehicle', 'parked_vehicle')
                                  and f['label'] not in ('crossing_vehicle', 'parked_vehicle')],
            'new_merged_ambiguous_accepted_indices': [c['index'] for f, c in pairs
                if c['identity_confirmed'] and c['identity_reason'] in
                ('multiple_vehicle_support', 'contained_competitor_ambiguous')
                and not (f['identity_confirmed'] and f['identity_reason'] in
                         ('multiple_vehicle_support', 'contained_competitor_ambiguous'))],
        }
    (args.output / 'report.json').write_text(json.dumps(clean(output), indent=2, allow_nan=False) + '\n')
    print(json.dumps(clean(output), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
