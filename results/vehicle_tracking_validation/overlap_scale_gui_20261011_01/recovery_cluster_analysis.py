#!/usr/bin/env python3
"""Read-only replay instrumentation of the completed GUI run's recovery cluster."""

from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sys

ROOT = Path('/home/yjh/ROS2_manmade')
TRIAL = ROOT / 'results/vehicle_tracking_validation/overlap_scale_gui_20261011_01'
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'ros2_ws/src/uav_learning')]

import numpy as np
from replay_vehicle_identity import appearance_proxy, stamp_key
from vehicle_crossing_validation import evaluate_identity


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    if not (TRIAL / 'supervisor.json').exists():
        raise RuntimeError('Do not archive analysis before supervisor shutdown.')
    output = TRIAL / 'recovery_cluster_analysis.json'
    if output.exists():
        raise RuntimeError('Never overwrite an existing analysis.')
    associations = rows(TRIAL / 'association.jsonl')
    truth = {stamp_key(r): r for r in rows(TRIAL / 'identity_observations.jsonl')}
    report = json.loads((TRIAL / 'report.json').read_text())
    parameters = json.loads((TRIAL / 'runtime_parameters.json').read_text())['perception_node']
    module_path = TRIAL / 'executed_sources/ros2_ws/src/uav_learning/uav_learning/vehicle_target_lock.py'
    dependency = Path('ros2_ws/src/uav_learning/uav_learning/vehicle_recovery_competition.py')
    if (TRIAL / 'executed_sources' / dependency).read_bytes() != (ROOT / dependency).read_bytes():
        raise RuntimeError('Replay dependency differs from the executed version.')
    spec = importlib.util.spec_from_file_location('executed_gui_lock', module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    class Instrumented(module.VehicleTargetLock):
        def confirm(self, item, measurement, now, required, evidence='standard'):
            compatible_id = (self.pending_id == item[0] or self.pending_id is None or item[0] is None)
            if evidence == 'partial_overlap':
                compatible_id = self.pending_id == item[0]
            gap = None if self.pending_time is None else now - self.pending_time
            center = None if self.pending_measurement is None else float(np.linalg.norm(
                measurement[:2] - self.pending_measurement[:2]))
            shape = None if self.pending_measurement is None else float(np.max(np.abs(
                measurement[2:] - self.pending_measurement[2:])))
            causes = []
            if self.pending_count == 0:
                causes.append('no_pending_chain')
            else:
                if not compatible_id:
                    causes.append('candidate_id_changed')
                if self.pending_evidence != evidence:
                    causes.append('confirmation_evidence_changed')
                if gap > .5:
                    causes.append('confirmation_frame_interval_exceeded_0.5s')
                if center >= .05:
                    causes.append('confirmation_center_motion')
                if shape >= .2:
                    causes.append('confirmation_scale_change')
            entry = {'candidate_id': item[0], 'previous_id': self.pending_id,
                     'previous_count': self.pending_count, 'previous_evidence': self.pending_evidence,
                     'evidence': evidence, 'interval_s': gap, 'center_delta_norm': center,
                     'log_scale_delta': shape, 'restart_causes': causes, 'required': required}
            accepted = super().confirm(item, measurement, now, required, evidence)
            entry.update(count_after=self.pending_count, confirmation_complete=accepted)
            self.replay_confirmation_calls.append(entry)
            return accepted

    seed = next(i for i, r in enumerate(associations) if r['wall_s'] > 60
                and r['identity_confirmed'] and r.get('elapsed_since_confirmed_s') is None)
    settings = {k: parameters[k] for k in ('acquisition_center_gate', 'confidence_threshold',
        'weak_idless_confirm_frames', 'weak_idless_max_age', 'recovery_competition_enabled',
        'predict_box_scale_velocity', 'overlap_candidate_recovery', 'bounded_scale_prediction')}
    settings.update(recovery_timeout=parameters['target_reacquire_timeout'], acquisition_confirm_frames=1)
    lock = Instrumented(**settings)
    last_original_seen = associations[seed]['wall_s']
    mismatches, selected_rows = [], []
    for index in range(seed, len(associations)):
        row = associations[index]
        now = (last_original_seen if index == seed else
               last_original_seen + row['elapsed_since_confirmed_s'])
        if row['identity_confirmed']:
            last_original_seen = now
        height, width = row['image_shape']
        candidates, histograms = [], []
        for candidate in row['candidates']:
            if row['reason'] == 'stale_inference_result':
                continue
            box, confidence = candidate['bbox'], candidate['confidence']
            if confidence is None or any(x is None or not math.isfinite(x) for x in box):
                continue
            area = max(0., box[2] - box[0]) * max(0., box[3] - box[1])
            if area / (width * height) < parameters['min_area_ratio']:
                continue
            if index == seed and not candidate['accepted']:
                continue
            candidates.append((candidate['track_id'], area, confidence, *box))
            histograms.append(appearance_proxy(1. if index == seed else candidate.get('appearance_similarity')))
        lock.replay_confirmation_calls = []
        chosen = lock.select(candidates, histograms, width, height, now,
                             camera_motion=row.get('camera_motion', {}).get('warp_px'))
        accepted = None if chosen is None else list(chosen[3:])
        original = next((c['bbox'] for c in row['candidates'] if c['accepted']), None)
        if accepted != original or (chosen is not None) != row['identity_confirmed']:
            mismatches.append(index)
        boxes = truth.get(stamp_key(row), {}).get('projected_boxes', {})
        if 160 <= row['wall_s'] <= 180:
            candidates_evaluated = [{**c, 'independent_identity': evaluate_identity(c['bbox'], boxes)}
                                    for c in row['candidates']] if boxes else []
            selected_rows.append({
                'index': index, 'wall_s': row['wall_s'], 'stamp': row['stamp'],
                'original_reason': row['reason'], 'identity_confirmed': row['identity_confirmed'],
                'locked_track_id': row['locked_track_id'], 'identity_guard': row.get('identity_guard'),
                'processing_s': row.get('processing_s'), 'target_publish_age_s': row.get('target_publish_age_s'),
                'confirmation_calls': lock.replay_confirmation_calls,
                'independent_identity': evaluate_identity(accepted, boxes) if boxes else None,
                'candidates': candidates_evaluated,
            })
    if mismatches:
        raise RuntimeError(f'Instrumentation does not reproduce source decisions: {mismatches}')
    cluster = [r for r in selected_rows if 162 <= r['wall_s'] <= 178]
    pending_correct = [r for r in cluster if not r['identity_confirmed'] and any(
        c['independent_identity']['label'] == 'tracked_vehicle' for c in r['candidates'])]
    partial = [(r, c) for r in cluster for c in r['candidates'] if c.get('overlap_continuation')]
    rejected = Counter(reason for r in pending_correct for c in r['candidates']
                       if c['independent_identity']['label'] == 'tracked_vehicle'
                       for reason in (c.get('rejection_reasons') or [c['reason']]))
    restart = Counter(reason for r in pending_correct for call in r['confirmation_calls']
                      for reason in call['restart_causes'])
    cluster_events = [e for e in report['events'] if 162 <= e['time_s'] <= 178]
    lost = []
    for i, event in enumerate(cluster_events):
        if event['event'] == 'TRACK_TARGET_LOST':
            recovered = next(e for e in cluster_events[i + 1:] if e['event'] == 'TARGET_RECOVERED')
            lost.append({'lost_wall_s': event['time_s'], 'recovered_wall_s': recovered['time_s'],
                         'recovery_s': recovered['time_s'] - event['time_s']})
    sizes = [c['predicted_size_px'] for r in cluster for c in r['candidates'] if 'predicted_size_px' in c]
    summary = {
        'source_trial': str(TRIAL), 'cluster_wall_s': [162., 178.],
        'completed_follow_coverage': report['follow_time_visible_fraction'],
        'instrumented_replay_seed_index': seed,
        'instrumented_replay_frames': len(associations) - seed,
        'instrumented_replay_decision_mismatch_indices': mismatches,
        'cluster_frames': len(cluster),
        'cluster_row_reasons': dict(Counter(r['original_reason'] for r in cluster)),
        'correct_candidate_unconfirmed_frames': len(pending_correct),
        'correct_candidate_rejection_reasons': dict(rejected),
        'confirmation_restart_causes_on_correct_unconfirmed': dict(restart),
        'overlap_continuation_frames': len(partial),
        'overlap_continuation_independent_labels': dict(Counter(c['independent_identity']['label'] for r,c in partial)),
        'predicted_height_px_range': [min(s[1] for s in sizes), max(s[1] for s in sizes)],
        'cluster_target_publish_age_p50_p95_max_s': np.percentile(
            [r['target_publish_age_s'] for r in cluster], [50,95,100]).tolist(),
        'cluster_processing_p50_p95_max_s': np.percentile(
            [r['processing_s'] for r in cluster], [50,95,100]).tolist(),
        'cluster_recoveries': lost,
        'recovery_timeout_events': sum(e['event']=='RECOVERY_TIMEOUT' for e in report['events']),
        'source_sha256': {name:hashlib.sha256((TRIAL/name).read_bytes()).hexdigest() for name in
                          ('association.jsonl','identity_observations.jsonl','report.json','runtime_parameters.json')},
        'executed_lock_sha256': hashlib.sha256(module_path.read_bytes()).hexdigest(),
        'limitations': [
            'Only confirmations and selected boxes are exactly replay-checked; histogram pixels are not recorded.',
            'Restart conditions are instrumented from the executed source with reconstructed original association time.',
            'Projected boxes are independent geometric evidence, not pixel instance masks.',
            'One newly restarted closed-loop run cannot establish repeatability or causality of all flight differences.',
            'No runtime, perception, controller or safety parameter was modified for this analysis.',
        ],
        'cluster_evidence_rows': selected_rows,
    }
    output.write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    shutil.copy2(__file__, TRIAL/'recovery_cluster_analysis.py')
    print(json.dumps({k:v for k,v in summary.items() if k!='cluster_evidence_rows'},indent=2))


if __name__ == '__main__':
    main()
