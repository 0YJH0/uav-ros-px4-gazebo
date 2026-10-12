import importlib.util
import math
from pathlib import Path
import sys

import numpy as np
import pytest
from scipy.spatial.transform import Rotation


ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts'))


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lane = load_script('vehicle_lane_change')
crossing = load_script('vehicle_crossing_validation')
CORNERS = crossing.mesh_corners(ROOT / 'ros2_ws/src/uav_learning/config/models/tracking_car/model.sdf')


def measured_row(motion):
    target = {'x': 16.0 + .8 * motion, 'y': .4 * math.sin(.05 * motion)}
    x, y, yaw = lane.lane_change_pose(target, motion)
    car = {'p': [x, y, .05], 'q': Rotation.from_euler('z', yaw).as_quat()}
    target_pose = {'p': [target['x'], target['y'], .05],
                   'q': Rotation.from_euler('z', math.atan2(.02 * math.cos(.05 * motion), .8)).as_quat()}
    return {'maneuver_phase': lane.lane_change_phase(motion),
            **lane.lane_change_geometry(CORNERS, target_pose, car)}


def test_same_lane_start_and_finish_do_not_start_between_uav_and_target():
    assert lane.lane_change_pose({'x': 16}, 0) == (-12.0, 0.0, 0.0)
    assert lane.lane_change_pose({'x': 16}, lane.END) == (26.0, 0.0, 0.0)
    assert lane.lane_change_phase(0) == 'rear_follow'
    assert lane.lane_change_phase(lane.END) == 'ahead_follow'


def test_dense_trajectory_maintains_body_clearance_and_rotated_road_margin():
    rows = [measured_row(float(motion)) for motion in np.linspace(0, 90, 9001)]
    result = lane.lane_change_evidence(rows)
    assert result['lane_change_scenario_observed'], result
    assert result['minimum_world_horizontal_clearance_m'] > 1.2
    assert result['minimum_distractor_road_margin_m'] > .2
    assert min(row['world_lateral_clearance_m'] for row in rows) < 0


@pytest.mark.parametrize('boundary', [0.0, lane.START, lane.LEFT_END, lane.PASS_END, lane.END])
def test_position_velocity_and_yaw_continuity(boundary):
    delta = 1e-4

    def pose(t):
        return np.array(lane.lane_change_pose({'x': 16 + .8 * t}, t))

    before, at, after = pose(boundary - delta), pose(boundary), pose(boundary + delta)
    np.testing.assert_allclose(before, after, atol=.001)
    np.testing.assert_allclose((at[:2] - before[:2]) / delta,
                               (after[:2] - at[:2]) / delta, atol=.001)


@pytest.mark.parametrize('motion,speed', [(float('nan'), .8), (float('inf'), .8), (1, 0), (1, -1)])
def test_invalid_timing_and_speed_rejected(motion, speed):
    with pytest.raises(ValueError):
        lane.lane_change_pose({'x': 16}, motion, speed)


def test_heading_matches_actual_position_velocity():
    dt = 1e-4
    for motion in np.linspace(.1, lane.END - .1, 100):
        before = lane.lane_change_pose({'x': 16 + .8 * (motion - dt)}, motion - dt)
        after = lane.lane_change_pose({'x': 16 + .8 * (motion + dt)}, motion + dt)
        yaw = lane.lane_change_pose({'x': 16 + .8 * motion}, motion)[2]
        assert abs(yaw - math.atan2(after[1] - before[1], after[0] - before[0])) < 1e-5


def test_verification_requires_all_measured_stages_and_safe_geometry():
    rows = [measured_row(float(motion)) for motion in np.arange(0, 70, .2)]
    assert lane.lane_change_evidence(rows)['lane_change_scenario_observed']
    for phase in lane.PHASES:
        missing = [row for row in rows if row['maneuver_phase'] != phase]
        assert not lane.lane_change_evidence(missing)['lane_change_scenario_observed']
    unsafe = [dict(row) for row in rows]
    unsafe[40]['world_horizontal_clearance_m'] = -.1
    assert not lane.lane_change_evidence(unsafe)['lane_change_scenario_observed']
    outside_road = [dict(row) for row in rows]
    outside_road[40]['distractor_road_margin_m'] = -.1
    assert not lane.lane_change_evidence(outside_road)['lane_change_scenario_observed']
    assert not lane.lane_change_evidence([])['lane_change_scenario_observed']


def test_command_labels_cannot_replace_measured_lane_change():
    rows = [measured_row(float(motion)) for motion in np.arange(0, 70, .2)]
    for row in rows:
        row['distractor_lane_y_m'] = 4.0
    assert not lane.lane_change_evidence(rows)['lane_change_scenario_observed']


def test_clearance_detects_same_lane_overlap_and_lateral_separation():
    target = {'p': [0.0, 0.0, .05], 'q': [0.0, 0.0, 0.0, 1.0]}
    assert lane.lane_change_geometry(CORNERS, target, target)['world_horizontal_clearance_m'] < 0
    beside = {'p': [0.0, 4.0, .05], 'q': [0.0, 0.0, 0.0, 1.0]}
    assert lane.lane_change_geometry(CORNERS, target, beside)['world_horizontal_clearance_m'] > 1.8
    ahead = {'p': [10.0, 0.0, .05], 'q': [0.0, 0.0, 0.0, 1.0]}
    assert lane.lane_change_geometry(CORNERS, target, ahead)['world_horizontal_clearance_m'] > 5.9


def test_full_identity_summary_requires_lane_return_and_no_wrong_car():
    rows = []
    for motion in np.arange(0, 70, .2):
        phase = 'pre' if motion < lane.START else 'during' if motion < lane.END else 'post'
        rows.append({'sim_s': float(motion), 'phase': phase, 'label': 'tracked_vehicle',
                     **measured_row(float(motion))})
    events = [{'event': 'lane_change_overtaking_started', 'sim_s': lane.START},
              {'event': 'lane_change_overtaking_completed', 'sim_s': lane.END}]

    def summary(observations, scenario_events=events):
        return crossing.identity_summary(observations, scenario_events, [],
                                         scenario='lane_change_overtaking', distractor_color='red')

    result = summary(rows)
    assert result['identity_independently_verified']
    assert result['lane_change']['maneuver_observed']
    assert result['distractor_color'] == 'red'
    assert not summary(rows, [])['identity_independently_verified']
    missing_return = [row for row in rows if row['maneuver_phase'] != 'merge_center']
    assert not summary(missing_return)['identity_independently_verified']
    wrong = [dict(row) for row in rows]
    wrong[-1]['label'] = 'crossing_vehicle'
    assert not summary(wrong)['identity_independently_verified']
    assert summary(wrong)['wrong_identity_observations'] == 1
