#!/usr/bin/env python3
"""Summarize recorded association evidence without inferring vehicle identity."""

import argparse
from collections import Counter
import json
from pathlib import Path


def percentile(values, quantile):
    ordered = sorted(values)
    return ordered[int((len(ordered) - 1) * quantile)] if ordered else None


def summarize(frames):
    rejected = Counter()
    locked_rejected = Counter()
    examples = {}
    for frame in frames:
        for candidate in frame.get('candidates', []):
            if candidate.get('accepted'):
                continue
            for reason in candidate.get('rejection_reasons', []):
                rejected[reason] += 1
                # Equality of tracker IDs is a diagnostic, not semantic identity.
                if (candidate.get('track_id') is not None and
                        candidate['track_id'] == frame.get('locked_track_id')):
                    locked_rejected[reason] += 1
                examples.setdefault(reason, {'wall_s': frame['wall_s'],
                                             'mode': frame.get('mode'),
                                             'candidate': candidate})
    processing = [frame['processing_s'] for frame in frames if 'processing_s' in frame]
    intervals = [b['wall_s'] - a['wall_s'] for a, b in zip(frames, frames[1:])]
    return {
        'frame_count': len(frames),
        'vehicle_visible_frames': sum(bool(frame['vehicle_detected']) for frame in frames),
        'identity_confirmed_frames': sum(bool(frame['identity_confirmed']) for frame in frames),
        'visible_but_unconfirmed_frames': sum(
            frame['vehicle_detected'] and not frame['identity_confirmed'] for frame in frames),
        'no_vehicle_frames': sum(not frame['vehicle_detected'] for frame in frames),
        'frame_reason_counts': dict(Counter(frame['reason'] for frame in frames)),
        'candidate_rejection_counts': dict(rejected),
        'locked_id_rejection_counts': dict(locked_rejected),
        'rejection_examples': examples,
        'low_confidence_confirmed_frames': sum(any(
            candidate.get('accepted') and candidate.get('low_confidence_continuation')
            for candidate in frame.get('candidates', [])) for frame in frames),
        'weak_idless_confirmed_frames': sum(any(
            candidate.get('accepted') and candidate.get('weak_idless_confirmed')
            for candidate in frame.get('candidates', [])) for frame in frames),
        'roi_reason_counts': dict(Counter(
            frame.get('detector', {}).get('roi_reason', 'not_recorded') for frame in frames)),
        'roi_confirmed_frames': sum(any(
            candidate.get('accepted') and candidate.get('detector_source') == 'target_roi'
            for candidate in frame.get('candidates', [])) for frame in frames),
        'roi_only_vehicle_frames': sum(
            frame.get('detector', {}).get('full_frame_count') == 0 and frame['vehicle_detected']
            for frame in frames),
        'camera_motion_counts': dict(Counter(
            frame.get('camera_motion', {}).get('reason', 'not_recorded') for frame in frames)),
        'bytetrack_camera_motion_counts': dict(Counter(
            frame.get('camera_motion', {}).get('bytetrack_reason', 'not_recorded') for frame in frames)),
        'long_loss_reacquisitions': [
            {'wall_s': frame['wall_s'], 'track_id': frame.get('locked_track_id'),
             'loss_s': frame.get('elapsed_since_confirmed_s')}
            for frame in frames if frame.get('mode') == 'reacquiring' and frame['identity_confirmed']],
        'processing_p95_s': percentile(processing, 0.95),
        'processing_max_s': max(processing) if processing else None,
        'frame_interval_p95_s': percentile(intervals, 0.95),
        'frame_interval_max_s': max(intervals) if intervals else None,
    }


def analyze(directory):
    directory = Path(directory)
    with (directory / 'association.jsonl').open() as stream:
        frames = [json.loads(line) for line in stream if line.strip()]
    with (directory / 'samples.jsonl').open() as stream:
        samples = [json.loads(line) for line in stream if line.strip()]
    begin = next((sample['wall_s'] for sample in samples if sample['state'] == 'APPROACH'), None)
    end = next((sample['wall_s'] for sample in samples
                if begin is not None and sample['wall_s'] > begin and
                sample['state'] in ('RETURN', 'LAND', 'DONE')), None)
    mission = [frame for frame in frames if begin is not None and frame['wall_s'] >= begin
               and (end is None or frame['wall_s'] < end)]
    report_path = directory / 'report.json'
    recorded = json.loads(report_path.read_text()) if report_path.exists() else {}
    audit = []
    for event in recorded.get('occlusions', []):
        start = event['start_wall_s']
        history = [frame for frame in frames if frame['wall_s'] <= start]
        recent = history[-3:]
        transitions = [item for item in recorded.get('transitions', []) if item['time_s'] <= start]
        state = transitions[-1]['state'] if transitions else None
        locked = bool(state == 'TRACK' and len(recent) == 3 and
                      all(frame['identity_confirmed'] for frame in recent) and
                      start - recent[-1]['wall_s'] <= 0.5 and
                      all(b['wall_s'] - a['wall_s'] <= 0.5 for a, b in zip(recent, recent[1:])))
        audit.append({'start_wall_s': start, 'state_at_start': state,
                      'entry_locked_from_recorded_evidence': locked,
                      'latest_association_wall_s': recent[-1]['wall_s'] if recent else None,
                      'original_occlusion_recovery_passed': recorded.get('occlusion_recovery_passed'),
                      'limitation': 'Offline topic timestamps approximate receipt ordering; '
                                    'this is not independent same-vehicle identity proof.'})
    return {
        'limitation': 'Frame counts are not time-weighted visibility or independent identity proof. '
                      'Candidate counts include distractors and may exceed frame counts. '
                      'Missing diagnostics cannot establish camera visibility.',
        'all_frames': summarize(frames),
        'occlusion_entry_audit': audit,
        'approach_follow_window': {'start_wall_s': begin, 'end_wall_s': end, **summarize(mission)},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory')
    parser.add_argument('--output')
    args = parser.parse_args()
    output = Path(args.output) if args.output else Path(args.directory) / 'association_summary.json'
    if output.exists():
        raise RuntimeError('Refusing to overwrite existing diagnostic evidence.')
    report = analyze(args.directory)
    output.write_text(json.dumps(report, indent=2) + '\n')
    summary = report['approach_follow_window']
    print(json.dumps({key: value for key, value in summary.items()
                      if key != 'rejection_examples'}, indent=2))


if __name__ == '__main__':
    main()
