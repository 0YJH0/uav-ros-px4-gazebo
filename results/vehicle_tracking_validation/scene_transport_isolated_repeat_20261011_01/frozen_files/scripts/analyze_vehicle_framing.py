#!/usr/bin/env python3
"""Read-only audit of camera framing and body pitch near observation gaps."""

import argparse
from bisect import bisect_left
import json
from pathlib import Path
import statistics

from scipy.spatial.transform import Rotation

from vehicle_experiment_study import digest, load_json, load_lines, percentile


def distribution(values):
    return {'n': len(values), 'mean': statistics.mean(values) if values else None,
            'p95': percentile(values, .95), 'max': max(values, default=None)}


def matched_pose(poses, times, stamp):
    sim = stamp['sec'] + stamp['nanosec'] / 1e9
    index = bisect_left(times, sim)
    nearby = poses[max(0, index-1):index+1]
    if not nearby:
        return None
    sample = min(nearby, key=lambda row: abs(row['sim_s']-sim))
    return sample if abs(sample['sim_s']-sim) <= .15 else None


def analyze(directory):
    report = load_json(directory / 'report.json')
    transitions = report['transitions']
    begin = next(row['time_s'] for row in transitions if row['state'] == 'APPROACH')
    end = next(row['time_s'] for row in transitions if row['time_s'] > begin
               and row['state'] in ('RETURN', 'LAND', 'DONE'))
    gaps = [event['time_s'] for event in report['events'] if event['event'].endswith('OBSERVATION_GAP')]
    poses = sorted(load_lines(directory / 'identity_poses.jsonl'), key=lambda row: row['sim_s'])
    times = [row['sim_s'] for row in poses]
    rows = []
    for association in load_lines(directory / 'association.jsonl'):
        if not begin <= association['wall_s'] < end:
            continue
        accepted = next((item for item in association['candidates'] if item.get('accepted')), None)
        sample = matched_pose(poses, times, association['stamp'])
        drone = sample['poses'].get('x500_perception_0') if sample else None
        pitch = float(Rotation.from_quat(drone['q']).as_euler('xyz', degrees=True)[1]) if drone else None
        row = {'wall_s': association['wall_s'], 'stamp': association['stamp'],
               'near_observation_gap': any(abs(association['wall_s']-gap) <= 1.5 for gap in gaps),
               'body_pitch_deg': pitch, 'identity_confirmed': accepted is not None,
               'processing_s': association.get('processing_s'),
               'target_publish_age_s': association.get('target_publish_age_s')}
        if accepted:
            height = association['image_shape'][0]
            bbox = accepted['bbox']
            row.update(center_v_norm=(bbox[1]+bbox[3])/height-1,
                       vertical_truncated=bool(bbox[1] <= .5 or bbox[3] >= height-.5),
                       geometry_update=accepted.get('geometry_update', 'legacy_full'),
                       protected_axes=accepted.get('protected_axes', []))
        rows.append(row)
    confirmed = [row for row in rows if row['identity_confirmed']]
    gap_rows = [row for row in rows if row['near_observation_gap']]
    partial = [row for row in confirmed if row['vertical_truncated']]
    summary = {'directory': str(directory), 'window_wall_s': [begin, end],
               'coverage_fraction': report['follow_time_visible_fraction'],
               'observation_gaps': len(gaps), 'accepted_frames': len(confirmed),
               'accepted_vertical_truncated_frames': len(partial),
               'accepted_truncated_geometry_protected': sum(row['geometry_update'] == 'horizontal_only' for row in partial),
               'matched_pitch_frames': sum(row['body_pitch_deg'] is not None for row in rows),
               'abs_body_pitch_deg': distribution([abs(row['body_pitch_deg']) for row in rows if row['body_pitch_deg'] is not None]),
               'near_gap_abs_body_pitch_deg': distribution([abs(row['body_pitch_deg']) for row in gap_rows if row['body_pitch_deg'] is not None]),
               'accepted_abs_vertical_reference_error': distribution([abs(row['center_v_norm']-.4) for row in confirmed]),
               'target_publish_age_s': distribution([row['target_publish_age_s'] for row in rows if row['target_publish_age_s'] is not None]),
               'input_sha256': {name: digest(directory / name) for name in (
                   'report.json', 'association.jsonl', 'identity_poses.jsonl')},
               'limitations': ['Pitch uses matched Gazebo body poses, not a gimbal angle or continuous ULog attitude.',
                              'Gap windows are +/-1.5 wall seconds; counts depend on observed gaps and frame cadence.',
                              'Accepted-box metrics include only confirmed detections, not invisible full-body truth.',
                              'Cross-trial statistics do not isolate individual fixes or prove repeatability.']}
    return summary, rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial', action='append', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or any(args.output.resolve().is_relative_to(path.resolve()) for path in args.trial):
        parser.error('Use a new external directory; original flight evidence stays read-only.')
    args.output.mkdir(parents=True)
    summaries = []
    for directory in args.trial:
        summary, rows = analyze(directory.resolve())
        summaries.append(summary)
        (args.output / (directory.name + '_frames.jsonl')).write_text(
            ''.join(json.dumps(row, allow_nan=False)+'\n' for row in rows))
    (args.output / 'report.json').write_text(json.dumps(
        {'trials': summaries, 'analysis_script_sha256': digest(Path(__file__))}, indent=2)+'\n')
    for summary in summaries:
        print(json.dumps({key: value for key, value in summary.items() if key not in ('input_sha256', 'limitations')}))


if __name__ == '__main__':
    main()
