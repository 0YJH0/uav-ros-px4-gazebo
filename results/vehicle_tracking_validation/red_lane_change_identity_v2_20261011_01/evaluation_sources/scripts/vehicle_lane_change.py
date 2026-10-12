"""Deterministic overtaking trajectory and pose-only scenario verification."""

from collections import Counter
import math

import numpy as np
from scipy.spatial.transform import Rotation

START, LEFT_END, PASS_END, END = 25.0, 35.0, 47.0, 57.0
PHASES = ('rear_follow', 'change_left', 'left_pass', 'merge_center', 'ahead_follow')
LEFT_LANE_Y = 3.8
INITIAL_OFFSET, REAR_OFFSET, AHEAD_OFFSET = -28.0, -10.0, 10.0


def _smooth_segment(t, start, end, low, high):
    u = min(1.0, max(0.0, (t - start) / (end - start)))
    smooth = u ** 3 * (10.0 + u * (-15.0 + 6.0 * u))
    derivative = 30.0 * u ** 2 * (1.0 - u) ** 2 / (end - start)
    return low + (high - low) * smooth, (high - low) * derivative


def lane_change_phase(motion):
    if motion < START:
        return PHASES[0]
    if motion < LEFT_END:
        return PHASES[1]
    if motion < PASS_END:
        return PHASES[2]
    if motion < END:
        return PHASES[3]
    return PHASES[4]


def lane_change_pose(target, motion, vehicle_speed=.8):
    if not math.isfinite(motion) or not math.isfinite(vehicle_speed) or vehicle_speed <= 0:
        raise ValueError('motion must be finite and vehicle_speed positive and finite')
    motion = max(0.0, motion)
    phase = lane_change_phase(motion)
    y, lateral_speed = 0.0, 0.0
    if phase == 'rear_follow':
        offset, relative_speed = _smooth_segment(motion, 0.0, START, INITIAL_OFFSET, REAR_OFFSET)
    elif phase == 'change_left':
        offset, relative_speed = REAR_OFFSET, 0.0
        y, lateral_speed = _smooth_segment(motion, START, LEFT_END, 0.0, LEFT_LANE_Y)
    elif phase == 'left_pass':
        offset, relative_speed = _smooth_segment(motion, LEFT_END, PASS_END, REAR_OFFSET, AHEAD_OFFSET)
        y = LEFT_LANE_Y
    elif phase == 'merge_center':
        offset, relative_speed = AHEAD_OFFSET, 0.0
        y, lateral_speed = _smooth_segment(motion, PASS_END, END, LEFT_LANE_Y, 0.0)
    else:
        offset, relative_speed = AHEAD_OFFSET, 0.0
    yaw = math.atan2(lateral_speed, vehicle_speed + relative_speed)
    return float(target['x']) + offset, y, yaw


def lane_change_geometry(corners, target, other):
    """Return measured clearance from poses, not the commanded trajectory.

    A positive separating-axis gap lower-bounds horizontal body separation.
    Unlike lateral clearance, it stays meaningful while both cars share a lane.
    """
    target_rotation = Rotation.from_quat(target['q'])
    other_rotation = Rotation.from_quat(other['q'])
    target_world = target_rotation.apply(corners) + target['p']
    other_world = other_rotation.apply(corners) + other['p']
    axes = []
    for rotation in (target_rotation, other_rotation):
        for direction in rotation.apply(np.eye(3))[:2]:
            horizontal = direction[:2]
            norm = np.linalg.norm(horizontal)
            if norm > 1e-8:
                axes.append(horizontal / norm)
    gaps = []
    for axis in axes:
        target_projection, other_projection = target_world[:, :2] @ axis, other_world[:, :2] @ axis
        gaps.append(max(other_projection.min() - target_projection.max(),
                        target_projection.min() - other_projection.max()))
    return {
        'relative_longitudinal_m': float(other['p'][0] - target['p'][0]),
        'relative_lateral_m': float(other['p'][1] - target['p'][1]),
        'distractor_lane_y_m': float(other['p'][1]),
        'world_horizontal_clearance_m': float(max(gaps)),
        'world_lateral_clearance_m': float(max(
            other_world[:, 1].min() - target_world[:, 1].max(),
            target_world[:, 1].min() - other_world[:, 1].max())),
        'distractor_road_margin_m': float(5.675 - np.abs(other_world[:, 1]).max()),
    }


def lane_change_evidence(rows):
    required = ('relative_longitudinal_m', 'distractor_lane_y_m',
                'world_horizontal_clearance_m', 'distractor_road_margin_m')
    measured = [row for row in rows if row.get('maneuver_phase') in PHASES
                and all(key in row and math.isfinite(row[key]) for key in required)]
    groups = {phase: [row for row in measured if row['maneuver_phase'] == phase] for phase in PHASES}
    counts = Counter(row['maneuver_phase'] for row in measured)
    clearance = min((row['world_horizontal_clearance_m'] for row in measured), default=None)
    road_margin = min((row['distractor_road_margin_m'] for row in measured), default=None)

    def count(phase, predicate):
        return sum(predicate(row) for row in groups[phase])

    def lane_sweep(phase, rear):
        relevant = [row for row in groups[phase]
                    if (row['relative_longitudinal_m'] < -6.0 if rear
                        else row['relative_longitudinal_m'] > 6.0)]
        return bool(len(relevant) >= 5
                    and (relevant[0]['distractor_lane_y_m'] < .75
                         and relevant[-1]['distractor_lane_y_m'] > 3.25 if rear else
                         relevant[0]['distractor_lane_y_m'] > 3.25
                         and relevant[-1]['distractor_lane_y_m'] < .75))

    rear_follow = count('rear_follow', lambda row:
        row['relative_longitudinal_m'] < -6.0 and abs(row['distractor_lane_y_m']) <= .75) >= 5
    changed_left = lane_sweep('change_left', rear=True)
    left_rows = [row for row in groups['left_pass'] if abs(row['distractor_lane_y_m'] - LEFT_LANE_Y) <= .5]
    passed = bool(len(left_rows) >= 10 and min(row['relative_longitudinal_m'] for row in left_rows) < -6.0
                  and max(row['relative_longitudinal_m'] for row in left_rows) > 6.0)
    merged_center = lane_sweep('merge_center', rear=False)
    ahead_follow = count('ahead_follow', lambda row:
        row['relative_longitudinal_m'] > 6.0 and abs(row['distractor_lane_y_m']) <= .75) >= 5
    safe_geometry = bool(clearance is not None and clearance >= .5
                         and road_margin is not None and road_margin >= 0.0)
    checks = {
        'same_lane_rear_follow_observed': rear_follow,
        'left_lane_change_observed': changed_left,
        'left_lane_pass_observed': passed,
        'center_lane_return_observed': merged_center,
        'same_lane_ahead_follow_observed': ahead_follow,
        'vehicle_clearance_and_road_margin_verified': safe_geometry,
    }
    return {
        'maneuver_observed': all(checks.values()),
        'lane_change_scenario_observed': all(checks.values()),
        'lane_change_checks': checks,
        'maneuver_phase_counts': {phase: counts[phase] for phase in PHASES},
        'minimum_world_horizontal_clearance_m': clearance,
        'minimum_distractor_road_margin_m': road_margin,
    }
