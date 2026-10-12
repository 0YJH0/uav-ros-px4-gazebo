#!/usr/bin/env python3
"""Exact frozen-input checks for confirmation continuity, not a flight replay."""

import argparse
from collections import Counter
import hashlib
import inspect
import json
from pathlib import Path
import shutil
import sys

ROOT = Path('/home/yjh/ROS2_manmade')
sys.path[:0] = [str(Path(__file__).resolve().parent), str(ROOT / 'scripts'),
               str(ROOT / 'ros2_ws/src/uav_learning')]

from replay_lane_change_fix import (clean, clock, load_implementation, read_jsonl, run)
from replay_vehicle_identity import stamp_key
from vehicle_crossing_validation import evaluate_identity
from vehicle_offline_truth import extend_truth

RESULTS = ROOT / 'results/vehicle_tracking_validation'
GUI = RESULTS / 'overlap_scale_gui_20261011_01'
OLD = RESULTS / 'red_lane_change_gui_20261011_01'
LOCK = Path('ros2_ws/src/uav_learning/uav_learning/vehicle_target_lock.py')
DEPENDENCY = Path('ros2_ws/src/uav_learning/uav_learning/vehicle_recovery_competition.py')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gap_proxy(rows, report, ttl=.5, debounce=.5):
    begin = next(t['time_s'] for t in report['transitions'] if t['state'] == 'TRACK')
    end = next(t['time_s'] for t in report['transitions'] if t['state'] == 'RETURN')
    intervals = []
    for index, row in enumerate(rows):
        lo = max(begin, row['wall_s'])
        hi = min(end, rows[index + 1]['wall_s'] if index + 1 < len(rows) else end)
        if row['identity_confirmed']:
            lo = max(lo, row['wall_s'] + ttl)
        if hi <= lo:
            continue
        if intervals and abs(intervals[-1][1] - lo) < 1e-8:
            intervals[-1][1] = hi
        else:
            intervals.append([lo, hi])
    episodes = []
    for lo, hi in intervals:
        if hi - lo < debounce:
            continue
        episodes.append({'start_wall_s': lo, 'end_wall_s': hi, 'duration_s': hi-lo,
                         'intersects_planned_occlusion': any(
                             lo < o['end_wall_s'] and hi > o['start_wall_s']
                             for o in report.get('occlusions', []))})
    return {'definition': 'Unconfirmed intervals >= debounce, using frozen receipt times and positive TTL; not controller RECOVER states.',
            'positive_ttl_s': ttl, 'debounce_s': debounce, 'episode_count': len(episodes),
            'nonplanned_episode_count': sum(not e['intersects_planned_occlusion'] for e in episodes),
            'maximum_duration_s': max((e['duration_s'] for e in episodes), default=0.),
            'episodes': episodes}


def compare(rows, reference, bounds):
    if len(rows) != len(reference) or any(r['stamp'] != f['stamp'] for r,f in zip(rows,reference)):
        raise RuntimeError('Comparison rows are not aligned.')
    pairs = [(f,r) for f,r in zip(reference,rows) if bounds[0] <= r['wall_s'] <= bounds[1]]
    merged = lambda r: r['identity_confirmed'] and r['identity_reason'] in (
        'multiple_vehicle_support', 'contained_competitor_ambiguous')
    return {
        'new_correct_indices': [r['index'] for f,r in pairs if r['label']=='tracked_vehicle' and f['label']!='tracked_vehicle'],
        'lost_correct_indices': [r['index'] for f,r in pairs if r['label']!='tracked_vehicle' and f['label']=='tracked_vehicle'],
        'new_wrong_indices': [r['index'] for f,r in pairs if r['label'] in ('crossing_vehicle','parked_vehicle') and
                              f['label'] not in ('crossing_vehicle','parked_vehicle')],
        'new_merged_ambiguous_indices': [r['index'] for f,r in pairs if merged(r) and not merged(f)],
        'removed_merged_ambiguous_indices': [r['index'] for f,r in pairs if not merged(r) and merged(f)],
        'all_decision_disagreement_indices': [r['index'] for f,r in zip(reference,rows)
            if (r['identity_confirmed'],r['accepted_box'],r['locked_track_id']) !=
               (f['identity_confirmed'],f['accepted_box'],f['locked_track_id'])],
    }


def replay_trial(trial, current, flag):
    associations = read_jsonl(trial/'association.jsonl')
    truth = {stamp_key(r):r for r in read_jsonl(trial/'identity_observations.jsonl')}
    report = json.loads((trial/'report.json').read_text())
    params = json.loads((trial/'runtime_parameters.json').read_text())
    perception = params['perception_node']
    seed = next(i for i,r in enumerate(associations) if r['wall_s']>60
                and r['identity_confirmed'] and r.get('elapsed_since_confirmed_s') is None)
    selected = next(c['bbox'] for c in associations[seed]['candidates'] if c['accepted'])
    if evaluate_identity(selected, truth[stamp_key(associations[seed])]['projected_boxes'])['label'] != 'tracked_vehicle':
        raise RuntimeError('Frozen seed is not independently target-confirmed.')
    times = clock(associations, seed)
    truth, reconstruction = extend_truth(trial, truth, associations, ROOT)
    paths = {'executed': trial/'executed_sources'/LOCK,
             'previous': GUI/'executed_sources'/LOCK,
             'disabled': current, 'candidate': current}
    summaries, output_rows = {}, {}
    for arm,path in paths.items():
        implementation = load_implementation(path, trial.name+'_'+arm)
        settings = {k:perception[k] for k in ('overlap_candidate_recovery','bounded_scale_prediction')
                    if k in perception and k in inspect.signature(implementation).parameters}
        if arm != 'executed':
            settings.update(overlap_candidate_recovery=True, bounded_scale_prediction=True)
        if arm in ('disabled','candidate'):
            settings[flag] = arm=='candidate'
        summaries[arm], output_rows[arm] = run(implementation, associations, truth, perception,
                                              seed, times, report, settings)
        summaries[arm]['unconfirmed_gap_proxy'] = gap_proxy(output_rows[arm], report)
        summaries[arm]['phase_counts'] = {phase:dict(Counter(r['label'] for r in output_rows[arm]
                                                           if r['phase']==phase))
                                         for phase in ('pre','during','post')}
        post_count = summaries[arm]['phase_counts']['post'].get('tracked_vehicle',0)
        summaries[arm]['post_correct_evidence_frames'] = post_count
        summaries[arm]['post_ten_frame_evidence_requirement_met_on_frozen_trajectory'] = post_count >= 10
    if summaries['executed']['frozen_confirmation_disagreement_indices'] or summaries['executed']['frozen_selected_box_disagreement_indices']:
        raise RuntimeError(trial.name+': archived implementation does not reproduce original.')
    bounds = summaries['executed']['historical_follow_window_wall_s']
    disabled_comparison = compare(output_rows['disabled'], output_rows['previous'], bounds)
    if disabled_comparison['all_decision_disagreement_indices']:
        raise RuntimeError(trial.name+': disabled flag changes previous-version decisions.')
    comparisons = {arm:compare(output_rows[arm],output_rows['previous'],bounds) for arm in ('disabled','candidate')}
    return {'source_trial':str(trial),'seed_index':seed,'seed_wall_s':associations[seed]['wall_s'],
            'rows_per_arm':len(output_rows['executed']), 'truth_reconstruction':reconstruction,
            'implementation_sha256':{name:sha(path) for name,path in paths.items()},
            'input_sha256':{name:sha(trial/name) for name in ('association.jsonl','identity_observations.jsonl',
                'identity_poses.jsonl','runtime_parameters.json','report.json')},
            'summaries':summaries, 'comparisons_to_previous_two_fix_version':comparisons}, output_rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--flag', default='overlap_confirmation_continuity')
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError('Output must be a new directory.')
    current = ROOT/LOCK
    original_hash = sha(current)
    if args.flag not in inspect.signature(load_implementation(current,'current_signature')).parameters:
        raise RuntimeError('Continuity flag is not present in candidate implementation.')
    for trial in (GUI,OLD):
        if (trial/'executed_sources'/DEPENDENCY).read_bytes() != (ROOT/DEPENDENCY).read_bytes():
            raise RuntimeError('Executed recovery competition dependency differs.')
    trials, all_rows = {}, {}
    for trial in (GUI, OLD):
        trials[trial.name],all_rows[trial.name] = replay_trial(trial,current,args.flag)
    if original_hash != sha(current):
        raise RuntimeError('Candidate source changed during replay.')
    args.output.mkdir(parents=True)
    snapshot = args.output/'implementation_snapshot'
    snapshot.mkdir()
    for name,path in [('candidate_vehicle_target_lock.py',current),
                      ('previous_vehicle_target_lock.py',GUI/'executed_sources'/LOCK),
                      ('old_executed_vehicle_target_lock.py',OLD/'executed_sources'/LOCK),
                      (DEPENDENCY.name,ROOT/DEPENDENCY),
                      ('vehicle_crossing_validation.py',ROOT/'scripts/vehicle_crossing_validation.py'),
                      ('vehicle_offline_truth.py',ROOT/'scripts/vehicle_offline_truth.py')]:
        shutil.copy2(path,snapshot/name)
    shutil.copy2(__file__,args.output/Path(__file__).name)
    shutil.copy2(Path(__file__).parent/'replay_lane_change_fix.py',args.output/'replay_lane_change_fix.py')
    for trial,arms in all_rows.items():
        folder = args.output/trial
        folder.mkdir()
        for arm,values in arms.items():
            (folder/(arm+'.jsonl')).write_text(''.join(json.dumps(r,allow_nan=False)+'\n' for r in values))
    result = {'trials':trials,'continuity_flag':args.flag,'limitations':[
        'Frozen detections, tracker IDs, GMC, receipt times and aircraft trajectories; not another flight.',
        'Association clock exactly reconstructed from original elapsed_since_confirmed_s, unaffected by candidate confirmations.',
        'Original seed after airborne reset is supplied; acquisition is not retested.',
        'Histogram proxies preserve only original fixed-reference correlation; no template updates are permitted.',
        'Independent projected truth is only used for evaluation after association decisions.',
        'Gap episode proxy is not controller RECOVER count: it does not simulate 10 Hz control ticks or recovery confirmation.',
        'Confirmation time percentage is a fixed-trajectory proxy, not actual new coverage or safety evidence.',
    ]}
    (args.output/'report.json').write_text(json.dumps(clean(result),indent=2,allow_nan=False)+'\n')
    for name,trial in trials.items():
        print(name,json.dumps({arm:{'correct_frames':summary['correct_target_confirmed_frames'],
            'merged_ambiguous_frames':summary['accepted_merged_ambiguous_frames'],
            'confirmation_time_proxy':summary['confirmation_time_fraction_proxy'],
            'gap_episodes_proxy':summary['unconfirmed_gap_proxy']['episode_count']}
            for arm,summary in trial['summaries'].items()}))


if __name__=='__main__':
    main()
