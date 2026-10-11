#!/usr/bin/env python3
"""Compare association versions on frozen detections; this is not a flight replay."""

import argparse
from collections import Counter
import hashlib
import importlib.util
import inspect
import json
import math
from pathlib import Path
import shutil

import numpy as np

from vehicle_crossing_validation import classify_identity

ROOT = Path(__file__).resolve().parents[1]


def load_lock(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.VehicleTargetLock


def appearance_proxy(similarity):
    if similarity is None:
        return None
    value = float(np.clip(similarity, -1.0, 1.0))
    reference = np.array([1., -1., 0.]) / math.sqrt(2)
    orthogonal = np.array([1., 1., -2.]) / math.sqrt(6)
    return (2 + value * reference + math.sqrt(max(0., 1 - value**2)) * orthogonal).astype(np.float32)


def stamp_key(row):
    return row['stamp']['sec'], row['stamp']['nanosec']


def time_proxy(rows, report):
    transitions = report.get('transitions', [])
    begin = next((row['time_s'] for row in transitions if row['state'] == 'TRACK'), None)
    end = next((row['time_s'] for row in transitions if begin is not None
                and row['time_s'] > begin and row['state'] in ('RETURN', 'LAND', 'DONE')), None)
    if begin is None or end is None:
        return {'confirmation_time_fraction_proxy': None}
    positive, wrong = 0., 0.
    for index, row in enumerate(rows):
        lo = max(begin, row['wall_s'])
        hi = min(end, rows[index + 1]['wall_s'] if index + 1 < len(rows) else end)
        if hi <= lo or not row['identity_confirmed']:
            continue
        seconds = max(0., min(hi, row['wall_s'] + 0.5) - lo)
        positive += seconds
        if row['label'] in ('crossing_vehicle', 'parked_vehicle'):
            wrong += seconds
    return {'window_wall_s': end - begin, 'confirmed_wall_s_proxy': positive,
            'wrong_identity_wall_s_proxy': wrong,
            'confirmation_time_fraction_proxy': positive / (end - begin)}


def recovery_proxy(rows):
    overlapping = [row for row in rows if row['phase'] == 'during'
                   and row['label'] == 'overlap_unscorable']
    anchor = overlapping[-1] if overlapping else None
    recovered = next((row for row in rows if anchor and stamp_key(row) > stamp_key(anchor)
                      and row['label'] == 'tracked_vehicle'), None)
    simulation = lambda row: row['stamp']['sec'] + row['stamp']['nanosec'] / 1e9
    return {'after_last_overlap_confirmation_sim_s_proxy':
            simulation(recovered) - simulation(anchor) if recovered else None,
            'after_last_overlap_confirmation_wall_s_proxy':
            recovered['wall_s'] - anchor['wall_s'] if recovered else None}


def competition_setting(implementation, parameters, mode):
    if mode == 'implementation_default':
        return {}
    enabled = (bool(parameters.get('recovery_competition_enabled', False))
               if mode == 'recorded' else mode == 'enabled')
    if 'recovery_competition_enabled' not in inspect.signature(implementation).parameters:
        if enabled:
            raise ValueError('Implementation does not support enabling competition.')
        return {}
    return {'recovery_competition_enabled': enabled}


def replay_trial(directory, implementation, width=960, height=540, truth_assets=None,
                 competition_mode='recorded', hold_box_scale=False):
    missing = [name for name in ('identity_observations.jsonl', 'association.jsonl')
               if not (directory / name).is_file()]
    if missing:
        return {'trial': directory.name, 'seed_available': False, 'observations': 0,
                'missing_input_files': missing}, []
    truth = {stamp_key(row): row for row in map(json.loads,
             (directory / 'identity_observations.jsonl').read_text().splitlines())}
    associations = list(map(json.loads, (directory / 'association.jsonl').read_text().splitlines()))
    seed = next((index for index, row in enumerate(associations)
                 if truth.get(stamp_key(row), {}).get('label') == 'tracked_vehicle' and
                 any(candidate.get('accepted') for candidate in row['candidates'])), None)
    if seed is None:
        return {'trial': directory.name, 'seed_available': False, 'observations': 0}, []
    if not (directory / 'runtime_parameters.json').is_file():
        return {'trial': directory.name, 'seed_available': False, 'observations': 0,
                'missing_input_files': ['runtime_parameters.json']}, []
    reconstruction = {}
    if truth_assets is not None:
        from vehicle_offline_truth import extend_truth
        truth, reconstruction = extend_truth(directory, truth, associations, truth_assets)
    parameters = json.loads((directory / 'runtime_parameters.json').read_text())['perception_node']
    settings = competition_setting(implementation, parameters, competition_mode)
    if hold_box_scale and 'predict_box_scale_velocity' in inspect.signature(implementation).parameters:
        settings['predict_box_scale_velocity'] = False
    lock = implementation(recovery_timeout=parameters['target_reacquire_timeout'],
                          acquisition_confirm_frames=1,
                          confidence_threshold=parameters['confidence_threshold'],
                          weak_idless_confirm_frames=parameters['weak_idless_confirm_frames'],
                          weak_idless_max_age=parameters['weak_idless_max_age'], **settings)
    rows, phases, reasons = [], {}, Counter()
    seed_candidate = next(candidate for candidate in associations[seed]['candidates'] if candidate.get('accepted'))
    for index, data in enumerate(associations[seed:], start=seed):
        candidates, histograms = [], []
        for candidate in data['candidates']:
            if data.get('reason') in ('stale_inference_result', 'stale_queued_frame', 'out_of_order_frame'):
                continue
            box, confidence = candidate['bbox'], candidate['confidence']
            if confidence is None or len(box) != 4 or any(value is None or not math.isfinite(value) for value in box):
                continue
            x1, y1, x2, y2 = box
            area = max(0., x2-x1) * max(0., y2-y1)
            if area / (width * height) < parameters['min_area_ratio']:
                continue
            if index == seed and candidate is not seed_candidate:
                continue
            candidates.append((candidate['track_id'], area, confidence, *box))
            histograms.append(appearance_proxy(1.0 if index == seed else candidate.get('appearance_similarity')))
        selected = lock.select(candidates, histograms, width, height, data['wall_s'],
                               camera_motion=data.get('camera_motion', {}).get('warp_px'))
        accepted = None if selected is None else list(selected[3:])
        evidence = truth.get(stamp_key(data))
        label = 'missing_frozen_truth'
        scores = {}
        if evidence:
            if evidence.get('projected_boxes'):
                label, scores = classify_identity(accepted, evidence['projected_boxes'])
            else:
                label = evidence['label']
            phases.setdefault(evidence['phase'], Counter())[label] += 1
        rejected = [reason for candidate in lock.diagnostics for reason in candidate.get('rejection_reasons', [])]
        reasons.update(rejected)
        rows.append({'stamp': data['stamp'], 'wall_s': data['wall_s'], 'label': label,
                     'phase': evidence.get('phase') if evidence else None,
                     'accepted_box': accepted, 'scores': scores, 'locked_track_id': lock.target_id,
                     'reason': lock.reason, 'guard_active': getattr(lock, 'overlap_guard_active', False),
                     'crossing_risk_evidence': getattr(lock, 'crossing_risk_diagnostic', {}),
                     'competition': getattr(lock, 'competition_diagnostic', {}),
                     'rejection_reasons': rejected,
                     'frozen_identity_confirmed': data['identity_confirmed'],
                     'identity_confirmed': selected is not None})
    matched = [row for row in rows if row['phase'] is not None]
    wrong = sum(row['label'] in ('crossing_vehicle', 'parked_vehicle') for row in matched)
    disagreement = sum(row['identity_confirmed'] != row['frozen_identity_confirmed'] for row in rows[20:])
    report_path = directory / 'report.json'
    report = json.loads(report_path.read_text()) if report_path.is_file() else {}
    timing = time_proxy(rows, report)
    begin = next((row['time_s'] for row in report.get('transitions', [])
                  if row['state'] in ('APPROACH', 'TRACK')), None)
    end = next((row['time_s'] for row in report.get('transitions', []) if begin is not None
                and row['time_s'] > begin and row['state'] in ('RETURN', 'LAND', 'DONE')), None)
    in_task = [row for row in matched if begin is not None and end is not None
               and begin <= row['wall_s'] < end]
    in_task_wrong = sum(row['label'] in ('crossing_vehicle', 'parked_vehicle') for row in in_task)
    return {'trial': directory.name, 'seed_available': True, 'observations': len(rows), **timing,
            **recovery_proxy(in_task),
            'recovery_competition_enabled': getattr(lock, 'recovery_competition_enabled', False),
            'predict_box_scale_velocity': getattr(lock, 'predict_box_scale_velocity', True),
            'truth_reconstruction': reconstruction,
            'matched_truth_observations': len(matched), 'wrong_identity_observations': wrong,
            'in_task_wrong_identity_observations': in_task_wrong if begin is not None and end is not None else None,
            'identity_evaluation_window_wall_s': [begin, end],
            'phase_counts': {phase: dict(counts) for phase, counts in phases.items()},
            'confirmation_disagreements_after_20_frame_warmup': disagreement,
            'rejection_reason_counts': dict(reasons)}, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('study', type=Path)
    parser.add_argument('--baseline-module', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--truth-assets', type=Path,
                        help='Read-only model root for independently reconstructing missing truth from archived poses.')
    parser.add_argument('--competition-mode', choices=('recorded', 'enabled', 'disabled', 'implementation_default'),
                        default='recorded', help='Default: use each trial\'s archived runtime switch.')
    parser.add_argument('--hold-box-scale', action='store_true', help='Candidate only: do not extrapolate box scale velocity.')
    args = parser.parse_args()
    current = ROOT / 'ros2_ws/src/uav_learning/uav_learning/vehicle_target_lock.py'
    dependency = current.parent / 'vehicle_recovery_competition.py'
    frozen_dependency = args.baseline_module.parent / dependency.name
    if frozen_dependency.is_file() and frozen_dependency.read_bytes() != dependency.read_bytes():
        raise RuntimeError('Frozen competition dependency differs; shared-import replay is not a valid baseline.')
    implementations = {'frozen': load_lock(args.baseline_module, 'frozen_lock'),
                       'candidate': load_lock(current, 'candidate_lock')}
    if args.output.exists():
        raise RuntimeError('Replay output must be a new directory; original evidence is never overwritten.')
    args.output.mkdir(parents=True)
    snapshot = args.output / 'implementation_snapshot'
    snapshot.mkdir()
    for name, path in [('frozen_lock.py', args.baseline_module), ('candidate_lock.py', current),
                       (dependency.name, dependency), ('replay_vehicle_identity.py', Path(__file__)),
                       ('vehicle_offline_truth.py', ROOT / 'scripts/vehicle_offline_truth.py'),
                       ('vehicle_crossing_validation.py', ROOT / 'scripts/vehicle_crossing_validation.py')]:
        shutil.copy2(path, snapshot / name)
    results = []
    for directory in sorted(args.study.glob('crossing_*')):
        if not directory.is_dir():
            continue
        item = {'trial': directory.name}
        item['input_sha256'] = {name: hashlib.sha256((directory / name).read_bytes()).hexdigest()
                                for name in ('association.jsonl', 'identity_observations.jsonl', 'runtime_parameters.json', 'report.json',
                                             'identity_poses.jsonl', 'identity_camera_info.json')
                                if (directory / name).is_file()}
        for name, implementation in implementations.items():
            summary, rows = replay_trial(directory, implementation, truth_assets=args.truth_assets,
                                         competition_mode=args.competition_mode,
                                         hold_box_scale=args.hold_box_scale and name == 'candidate')
            item[name] = summary
            with (args.output / f'{directory.name}_{name}.jsonl').open('w') as stream:
                for row in rows:
                    stream.write(json.dumps(row, allow_nan=False) + '\n')
        results.append(item)
    report = {'source_study': str(args.study.resolve()), 'trials': results,
              'competition_mode': args.competition_mode,
              'candidate_hold_box_scale': args.hold_box_scale,
              'truth_assets': str(args.truth_assets.resolve()) if args.truth_assets else None,
              'truth_asset_sha256': {str(path.relative_to(args.truth_assets)): hashlib.sha256(path.read_bytes()).hexdigest()
                                    for folder in ('PX4-Autopilot/Tools/simulation/gz/models/uav_rgb_camera',
                                                   'ros2_ws/src/uav_learning/config/models/tracking_car')
                                    for path in (args.truth_assets / folder).rglob('*') if path.is_file()} if args.truth_assets else {},
              'truth_helper_sha256': hashlib.sha256((ROOT / 'scripts/vehicle_offline_truth.py').read_bytes()).hexdigest(),
              'replay_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'implementation_sha256': {name: hashlib.sha256(path.read_bytes()).hexdigest()
                                        for name, path in [('frozen', args.baseline_module), ('candidate', current)]},
              'candidate_dependency_sha256': {'vehicle_recovery_competition.py': hashlib.sha256(
                  dependency.read_bytes()).hexdigest()},
              'baseline_dependency_sha256': {dependency.name: hashlib.sha256(frozen_dependency.read_bytes()).hexdigest()}
                  if frozen_dependency.is_file() else {},
              'limitations': [
                  'Frozen detections, ByteTrack IDs, camera warps and receipt times are inputs; YOLO/ByteTrack are not rerun.',
                  'Synthetic histograms preserve only logged correlation to the frozen reference, not image appearance.',
                  'The lock is seeded at the first independently confirmed target; acquisition and prior covariance are not replayed.',
                  'Truth selects the known-correct frozen seed frame; projections are otherwise used only after decisions, never passed to the lock.',
                  'SEARCH intervals without frozen truth remain unscorable.',
                  'Confirmation time uses the historical TRACK-to-return window and a 0.5 s receipt TTL; it is a fixed-trajectory proxy, not flight coverage.',
                  'in_task_wrong_identity_observations covers first APPROACH/TRACK to first RETURN; all-frame counts also include inactive return/landing detections.',
                  'The aircraft trajectory is unchanged; these are diagnostic comparisons, not new closed-loop passes.']}
    (args.output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    for item in results:
        print(item['trial'], json.dumps({name: {key: value for key, value in item[name].items()
              if key in ('wrong_identity_observations', 'phase_counts', 'seed_available')}
              for name in implementations}))


if __name__ == '__main__':
    main()
