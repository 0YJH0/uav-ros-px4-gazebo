import importlib.util
import math
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

spec = importlib.util.spec_from_file_location(
    'crossing', Path(__file__).resolve().parents[4] / 'scripts/vehicle_crossing_validation.py')
crossing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crossing)


def test_gazebo_camera_axes_and_relative_link_translation():
    corners = np.array([[10, -1, -1], [10, 1, 1]], dtype=float)
    identity = {'p': [0, 0, 0], 'q': [0, 0, 0, 1]}
    camera = {'p': [0, 0, 1], 'q': [0, 0, 0, 1]}
    box = crossing.project_box(corners, identity, identity, camera,
                               [100, 0, 50, 0, 100, 50, 0, 0, 1], 100, 100)
    np.testing.assert_allclose(box, [40, 50, 60, 70])


def test_mesh_vertices_scaled_to_actual_car_dimensions():
    corners = crossing.mesh_corners(crossing.ROOT / 'ros2_ws/src/uav_learning/config/models/tracking_car/model.sdf')
    extent = corners.max(0)-corners.min(0)
    assert 3 < extent[0] < 6 and 1 < extent[1] < 3 and 1 < extent[2] < 3


def test_overlapping_models_are_unscorable_even_with_perfect_detector_box():
    box = [10, 10, 30, 30]
    label, _ = crossing.classify_identity(box, {'tracked_vehicle': box, 'crossing_vehicle': box})
    assert label == 'overlap_unscorable'


def test_separated_wrong_car_has_independent_identity_label():
    target, other = [10, 10, 30, 30], [60, 10, 80, 30]
    boxes = {'tracked_vehicle': target, 'crossing_vehicle': other}
    assert crossing.classify_identity(target, boxes)[0] == 'tracked_vehicle'
    assert crossing.classify_identity(other, boxes)[0] == 'crossing_vehicle'
    assert crossing.classify_identity(None, boxes)[0] == 'unconfirmed'


def test_identity_requires_before_after_and_real_overlap_not_only_task_completion():
    rows = [{'phase': 'pre', 'label': 'tracked_vehicle', 'sim_s': 30} for _ in range(10)]
    rows += [{'phase': 'during', 'label': 'overlap_unscorable', 'sim_s': 35} for _ in range(3)]
    rows += [{'phase': 'post', 'label': 'tracked_vehicle', 'sim_s': 41} for _ in range(10)]
    events = [{'event': 'crossing_started', 'sim_s': 32}, {'event': 'crossing_completed', 'sim_s': 40}]
    assert crossing.identity_summary(rows, events, [])['identity_independently_verified']
    assert not crossing.identity_summary(rows, [], [])['identity_independently_verified']
    rows.append({'phase': 'post', 'label': 'crossing_vehicle', 'sim_s': 42})
    assert not crossing.identity_summary(rows, events, [])['identity_independently_verified']


def test_wrong_identity_images_bypass_periodic_throttle_and_crossing_window():
    for label in ('crossing_vehicle', 'parked_vehicle'):
        row = {'label': label, 'sim_s': 112.152, 'motion_time': 70.}
        assert crossing.image_capture_reason(row, 112.1) == 'wrong_identity'


def test_normal_crossing_images_remain_rate_limited():
    row = {'label': 'tracked_vehicle', 'sim_s': 112.152, 'motion_time': 36.}
    assert crossing.image_capture_reason(row, 112.1) is None
    assert crossing.image_capture_reason(row, 110.) == 'periodic_crossing'
    row['motion_time'] = 70.
    assert crossing.image_capture_reason(row, 110.) is None


def test_overtaking_is_continuous_and_keeps_body_clearance_and_road_margin():
    corners = crossing.mesh_corners(crossing.ROOT / 'ros2_ws/src/uav_learning/config/models/tracking_car/model.sdf')
    for motion in np.linspace(0, 95, 951):
        target = {'x': 16 + .8 * motion, 'y': .4 * math.sin(motion * .05)}
        x, y, yaw = crossing.overtaking_pose(target, motion)
        car = {'p': [x, y, .05], 'q': Rotation.from_euler('z', yaw).as_quat()}
        target_pose = {'p': [target['x'], target['y'], .05], 'q': Rotation.from_euler(
            'z', math.atan2(.02 * math.cos(motion * .05), .8)).as_quat()}
        assert crossing.lateral_clearance(corners, target_pose, car) > 1.3
        world = Rotation.from_quat(car['q']).apply(corners) + car['p']
        assert world[:, 1].max() < 5.675  # Inner edge of roadside barriers.
        assert world[:, 0].min() > -30 and world[:, 0].max() < 250
    for boundary in (crossing.START, crossing.START + crossing.DURATION):
        a = crossing.overtaking_pose({'x': 40}, boundary - 1e-6)[0]
        b = crossing.overtaking_pose({'x': 40}, boundary + 1e-6)[0]
        assert abs(a-b) < 1e-5
    assert crossing.overtaking_pose({'x': 40}, crossing.START)[0] == 32
    assert crossing.overtaking_pose({'x': 40}, crossing.START + crossing.DURATION)[0] == 48


def test_overtaking_requires_measured_pass_and_clearance_not_projected_overlap():
    rows = [{'phase': 'pre', 'label': 'tracked_vehicle', 'sim_s': 30} for _ in range(10)]
    rows += [{'phase': 'during', 'label': 'tracked_vehicle', 'sim_s': 35+i*.5,
              'relative_longitudinal_m': -8+i, 'world_lateral_clearance_m': 1.4} for i in range(16)]
    rows += [{'phase': 'post', 'label': 'tracked_vehicle', 'sim_s': 44+i,
              'relative_longitudinal_m': 8+i, 'world_lateral_clearance_m': 1.4} for i in range(10)]
    events = [{'event': 'overtaking_started', 'sim_s': 35}, {'event': 'overtaking_completed', 'sim_s': 43}]
    result = crossing.identity_summary(rows, events, [], 'overtaking')
    assert result['identity_independently_verified'] and result['overtaking_observed']
    assert result['overlap_observations'] == 0 and not result['crossing_completed']
    assert not crossing.identity_summary(rows, events, [])['identity_independently_verified']
    assert not crossing.identity_summary(rows, [], [], 'overtaking')['identity_independently_verified']
    rows[-1]['world_lateral_clearance_m'] = -.1
    assert not crossing.identity_summary(rows, events, [], 'overtaking')['identity_independently_verified']


def test_overtaking_wrong_identity_still_fails():
    rows = [{'phase': 'post', 'label': 'crossing_vehicle', 'sim_s': 50}]
    result = crossing.identity_summary(rows, [], [], 'overtaking')
    assert result['wrong_identity_observations'] == 1
    assert not result['identity_independently_verified']
