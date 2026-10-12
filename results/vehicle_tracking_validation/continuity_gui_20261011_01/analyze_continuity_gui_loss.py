#!/usr/bin/env python3
"""Explain the completed flight's remaining loss without changing raw evidence."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path('/home/yjh/ROS2_manmade')
TRIAL = ROOT/'results/vehicle_tracking_validation/continuity_gui_20261011_01'
PREVIOUS = ROOT/'results/vehicle_tracking_validation/overlap_scale_gui_20261011_01'
sys.path.insert(0,str(ROOT/'scripts'))
from vehicle_crossing_validation import evaluate_identity


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def key(row):
    return row['stamp']['sec'],row['stamp']['nanosec']


def phase_summary(directory):
    associations = read_rows(directory/'association.jsonl')
    truth = {key(r):r for r in read_rows(directory/'identity_observations.jsonl')}
    result = {}
    for phase in ('during','post'):
        data = [r for r in associations if truth.get(key(r),{}).get('phase')==phase]
        result[phase] = {'matched_association_frames':len(data),
                         'association_reasons':dict(Counter(r['reason'] for r in data)),
                         'independent_labels':dict(Counter(truth[key(r)]['label'] for r in data))}
    return result


def main():
    if not (TRIAL/'supervisor.json').is_file():
        raise RuntimeError('Wait for complete supervisor shutdown.')
    destination = TRIAL/'loss_analysis.json'
    if destination.exists():
        raise RuntimeError('Do not overwrite prior analysis.')
    associations = read_rows(TRIAL/'association.jsonl')
    truth = {key(r):r for r in read_rows(TRIAL/'identity_observations.jsonl')}
    report = json.loads((TRIAL/'report.json').read_text())
    identity = json.loads((TRIAL/'identity_report.json').read_text())
    runtime = json.loads((TRIAL/'runtime_parameters.json').read_text())
    events = report['events']
    losses = [e for e in events if e['event']=='TRACK_TARGET_LOST' and not any(
        o['start_wall_s']<=e['time_s']<=o['end_wall_s'] for o in report['occlusions'])]
    if len(losses)!=1:
        raise RuntimeError('This narrow analysis requires exactly one nonplanned loss.')
    lost = losses[0]
    recovered = next(e for e in events if e['time_s']>lost['time_s'] and e['event']=='TARGET_RECOVERED')
    return_time = next(t['time_s'] for t in report['transitions'] if t['state']=='RETURN')
    follow_start = next(t['time_s'] for t in report['transitions'] if t['state']=='TRACK')
    preserved = []
    for row in associations:
        for candidate in row['candidates']:
            if not candidate.get('overlap_confirmation_preserved'):
                continue
            evidence = truth.get(key(row))
            evaluation = (evaluate_identity(candidate['bbox'],evidence['projected_boxes'])
                          if evidence and evidence.get('projected_boxes') else None)
            preserved.append({'wall_s':row['wall_s'],'stamp':row['stamp'],
                'accepted':candidate['accepted'],'track_id':candidate['track_id'],
                'label':evaluation['label'] if evaluation else 'missing_matched_identity_observation',
                'independent_evaluation':evaluation,
                'phase':evidence.get('phase') if evidence else None,
                'inside_follow_window':follow_start<=row['wall_s']<return_time})
    loss_rows = []
    for row in associations:
        if not 173.9<=row['wall_s']<=175.0:
            continue
        evidence = truth.get(key(row))
        boxes = evidence.get('projected_boxes',{}) if evidence else {}
        loss_rows.append({**{k:row.get(k) for k in ('wall_s','stamp','reason','identity_confirmed',
            'elapsed_since_confirmed_s','processing_s','queue_wait_s','target_publish_age_s','identity_guard')},
            'candidates':[{**c,'independent_evaluation':evaluate_identity(c['bbox'],boxes)
                          if boxes else None} for c in row['candidates']]})
    prior_gap_rows = []
    for row in associations:
        if 170.35<=row['wall_s']<=171.05:
            prior_gap_rows.append({**{k:row.get(k) for k in ('wall_s','stamp','reason','identity_confirmed',
                'elapsed_since_confirmed_s','processing_s','queue_wait_s','target_publish_age_s')},
                'accepted_preservation':[{k:c.get(k) for k in ('track_id','bbox','overlap_confirmation_preserved')}
                                         for c in row['candidates'] if c['accepted']]})
    controller = runtime['px4_offboard_controller']
    source_lock = TRIAL/'executed_sources/ros2_ws/src/uav_learning/uav_learning/vehicle_target_lock.py'
    result = {
        'source_trial':str(TRIAL), 'previous_trial':str(PREVIOUS),
        'loss_event':lost,'recovered_event':recovered,
        'recovery_wall_s':recovered['time_s']-lost['time_s'],
        'association_reasons_173_9_to_175':dict(Counter(r['reason'] for r in loss_rows)),
        'loss_window_rows':loss_rows,'earlier_confirmation_interval_gap_rows':prior_gap_rows,
        'preservation_summary':{
            'all_association_frames':len(preserved),
            'independent_labels':dict(Counter(r['label'] for r in preserved)),
            'follow_window_frames':sum(r['inside_follow_window'] for r in preserved),
            'follow_window_independent_labels':dict(Counter(r['label'] for r in preserved if r['inside_follow_window'])),
            'unmatched_rows':[r for r in preserved if r['label']=='missing_matched_identity_observation'],
        },
        'preserved_rows':preserved,
        'phase_comparison':{PREVIOUS.name:phase_summary(PREVIOUS),TRIAL.name:phase_summary(TRIAL)},
        'identity_report_summary':{k:identity[k] for k in ('identity_independently_verified',
            'wrong_identity_observations','identity_reason_counts','phase_counts','scorable_identity_switches')},
        'controller_parameters':{k:controller[k] for k in ('detection_stale_timeout',
            'observation_gap_timeout','recovery_confirm_frames','recovery_timeout')},
        'input_sha256':{str(directory.name+'/'+name):hashlib.sha256((directory/name).read_bytes()).hexdigest()
            for directory,names in ((TRIAL,('association.jsonl','identity_observations.jsonl','identity_report.json',
                'report.json','runtime_parameters.json')),(PREVIOUS,('association.jsonl','identity_observations.jsonl')))
            for name in names},
        'executed_lock_sha256':hashlib.sha256(source_lock.read_bytes()).hexdigest(),
        'limitations':[
            'Identity rows are joined by image stamp, never by independent logger wall clocks.',
            'The one preserved frame after RETURN has no matching archived identity observation and is not labelled correct.',
            'Independent projected boxes are not per-pixel instance masks.',
            'The second control-level confirmation is inferred from recorded positive arrivals and executed recovery_confirm_frames=3, not a recorded internal counter.',
            'Comparisons use separate complete phase intervals because wall time and trajectories differ; one run is not repeatability proof.',
            'No raw log, production source, threshold, safety limit or evaluation rule is changed.',
        ],
    }
    destination.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    shutil.copy2(__file__,TRIAL/'analyze_continuity_gui_loss.py')
    print(json.dumps({k:v for k,v in result.items() if k not in (
        'loss_window_rows','preserved_rows','earlier_confirmation_interval_gap_rows','input_sha256')},indent=2))


if __name__=='__main__':
    main()
