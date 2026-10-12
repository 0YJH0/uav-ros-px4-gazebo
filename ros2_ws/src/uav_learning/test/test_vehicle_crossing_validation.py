import importlib.util
import math
from pathlib import Path
import sys

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts'))

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


@pytest.mark.parametrize('selected,label', [
    ([0, 0, 100, 100], 'tracked_vehicle'),
    ([70, 0, 170, 100], 'crossing_vehicle'),
])
def test_partial_overlap_scores_distinct_original_and_wrong_vehicle_symmetrically(selected, label):
    boxes = {'tracked_vehicle': [0, 0, 100, 100], 'crossing_vehicle': [70, 0, 170, 100]}
    assert crossing.iou(*boxes.values()) > .1
    for ordered in (boxes, dict(reversed(list(boxes.items())))):
        result = crossing.evaluate_identity(selected, ordered)
        assert result['label'] == label
        assert result['reason'] == 'unique_projection_support'
        assert result['exclusive_evidence'][label]['fraction_of_projected_box'] == pytest.approx(.7)
        assert result['identity_evaluation_version'] == crossing.IDENTITY_EVALUATION_VERSION


def test_merged_two_vehicle_box_is_unscorable_despite_strong_iou_margin():
    boxes = {'tracked_vehicle': [0, 0, 100, 100], 'crossing_vehicle': [80, 0, 130, 50]}
    selected = [0, 0, 130, 100]
    assert crossing.iou(selected, boxes['tracked_vehicle']) > .4
    assert crossing.iou(selected, boxes['tracked_vehicle']) - crossing.iou(selected, boxes['crossing_vehicle']) > .2
    result = crossing.evaluate_identity(selected, boxes)
    assert result['label'] == 'overlap_unscorable'
    assert result['reason'] == 'multiple_vehicle_support'


@pytest.mark.parametrize('selected,reason', [
    ([0, 0, 100, 100], 'contained_competitor_ambiguous'),
    ([20, 20, 40, 40], 'insufficient_exclusive_projection'),
])
def test_contained_boxes_do_not_claim_identity_from_area_advantage(selected, reason):
    result = crossing.evaluate_identity(selected, {
        'tracked_vehicle': [0, 0, 100, 100], 'crossing_vehicle': [20, 20, 40, 40]})
    assert result['label'] == 'overlap_unscorable'
    assert result['reason'] == reason


def test_exclusive_area_subtracts_union_once_and_supports_detection_clip():
    box = [0, 0, 100, 100]
    others = [[0, 0, 40, 100], [20, 0, 60, 100]]
    assert crossing.exclusive_area(box, others) == 4000
    assert crossing.exclusive_area(box, others, [50, 0, 80, 100]) == 2000
    assert crossing.exclusive_area(box, others, [110, 0, 120, 100]) == 0


def test_three_vehicle_union_can_remove_majority_even_when_each_overlap_is_small():
    result = crossing.evaluate_identity([0, 0, 100, 100], {
        'tracked_vehicle': [0, 0, 100, 100],
        'crossing_vehicle': [0, 0, 40, 100], 'parked_vehicle': [60, 0, 100, 100]})
    assert result['label'] == 'overlap_unscorable'
    assert result['reason'] == 'insufficient_exclusive_projection'


def test_unrelated_overlapping_background_does_not_hide_clear_selected_vehicle():
    boxes = {'tracked_vehicle': [200, 0, 300, 100],
             'crossing_vehicle': [0, 0, 100, 100], 'parked_vehicle': [0, 0, 100, 100]}
    assert crossing.classify_identity(boxes['tracked_vehicle'], boxes)[0] == 'tracked_vehicle'


@pytest.mark.parametrize('selected,boxes,reason', [
    ([0, 0, 100, 100], {'tracked_vehicle': [0, 0, 100, 100],
                       'crossing_vehicle': [50, 0, 150, 100]}, 'insufficient_exclusive_projection'),
    ([0, 0, 50, 100], {'tracked_vehicle': [0, 0, 100, 100]}, 'insufficient_exclusive_support'),
    ([0, 0, 125, 100], {'tracked_vehicle': [0, 0, 100, 100],
                       'crossing_vehicle': [80, 0, 150, 100]}, 'multiple_vehicle_support'),
])
def test_exact_half_is_not_unique_majority(selected, boxes, reason):
    result = crossing.evaluate_identity(selected, boxes)
    assert result['label'] in ('overlap_unscorable', 'projection_unscorable')
    assert result['reason'] == reason


def test_no_accepted_box_is_unconfirmed_even_during_overlap():
    box = [0, 0, 100, 100]
    boxes = {'tracked_vehicle': box, 'crossing_vehicle': box}
    result = crossing.evaluate_identity(None, boxes)
    assert result['label'] == 'unconfirmed'
    assert result['reason'] == 'no_accepted_box'
    assert result['target_projection_overlap_iou'] == 1


@pytest.mark.parametrize('box', [[0, 0, 0, 1], [1, 0, 0, 1], [0, 0, float('nan'), 1]])
def test_invalid_boxes_cannot_certify_identity(box):
    valid = [0, 0, 100, 100]
    for selected, boxes in ((box, {'tracked_vehicle': valid}),
                            (valid, {'tracked_vehicle': valid, 'crossing_vehicle': box})):
        result = crossing.evaluate_identity(selected, boxes)
        assert result['label'] == 'projection_unscorable'
        assert result['reason'] == 'invalid_box_geometry'


def test_weak_match_is_still_rejected():
    result = crossing.evaluate_identity([0, 0, 30, 100], {'tracked_vehicle': [0, 0, 100, 100]})
    assert result['label'] == 'projection_unscorable'
    assert result['reason'] == 'insufficient_match_iou'


@pytest.mark.parametrize('width', [40, 45, 50])
def test_small_single_vehicle_box_needs_majority_support_despite_minimum_iou(width):
    result = crossing.evaluate_identity([0, 0, width, 100], {'tracked_vehicle': [0, 0, 100, 100]})
    assert result['scores']['tracked_vehicle'] >= .4
    assert result['label'] == 'projection_unscorable'
    assert result['reason'] == 'insufficient_exclusive_support'


def test_offscreen_truth_does_not_certify_target_and_does_not_hide_wrong_vehicle():
    accepted = [0, 0, 100, 100]
    assert crossing.evaluate_identity(accepted, {'tracked_vehicle': None})['label'] == 'projection_unscorable'
    result = crossing.evaluate_identity(accepted, {'tracked_vehicle': None, 'crossing_vehicle': accepted})
    assert result['label'] == 'crossing_vehicle'


def test_contained_background_is_irrelevant_when_detection_avoids_it():
    boxes = {'tracked_vehicle': [0, 0, 100, 100],
             'crossing_vehicle': [70, 0, 100, 50], 'parked_vehicle': [80, 10, 90, 20]}
    result = crossing.evaluate_identity([0, 0, 70, 100], boxes)
    assert result['label'] == 'tracked_vehicle'
    assert result['exclusive_evidence']['crossing_vehicle']['area_px2'] == 0


def test_overlap_scenario_evidence_is_separate_from_confirmation_label():
    boxes = {'tracked_vehicle': [0, 0, 100, 100], 'crossing_vehicle': [70, 0, 170, 100]}
    rows = [{'phase': 'pre', 'label': 'tracked_vehicle', 'sim_s': 30} for _ in range(10)]
    rows += [{'phase': 'during', 'projected_boxes': boxes, 'sim_s': 35 + i,
              **crossing.evaluate_identity(boxes['tracked_vehicle'] if i else None, boxes)} for i in range(3)]
    rows += [{'phase': 'post', 'label': 'tracked_vehicle', 'sim_s': 41} for _ in range(10)]
    events = [{'event': 'crossing_started', 'sim_s': 32}, {'event': 'crossing_completed', 'sim_s': 40}]
    result = crossing.identity_summary(rows, events, [])
    assert result['overlap_observations'] == 3
    assert result['phase_counts']['during'] == {'unconfirmed': 1, 'tracked_vehicle': 2}
    assert result['identity_independently_verified']
    assert result['identity_criteria']['minimum_match_iou'] == .4
    assert result['identity_criteria']['minimum_match_margin'] == .2
    assert result['after_last_overlap_confirmation_sim_s'] == 4


def test_wrong_identity_during_partial_overlap_remains_a_failure():
    boxes = {'tracked_vehicle': [0, 0, 100, 100], 'crossing_vehicle': [70, 0, 170, 100]}
    rows = [{'phase': phase, 'label': 'tracked_vehicle', 'sim_s': stamp}
            for phase, stamp in [('pre', 30), ('post', 41)] for _ in range(10)]
    rows += [{'phase': 'during', 'projected_boxes': boxes, 'sim_s': 35 + i,
              **crossing.evaluate_identity(boxes['crossing_vehicle'], boxes)} for i in range(3)]
    events = [{'event': 'crossing_started', 'sim_s': 32}, {'event': 'crossing_completed', 'sim_s': 40}]
    result = crossing.identity_summary(rows, events, [])
    assert result['wrong_identity_observations'] == 3
    assert not result['identity_independently_verified']


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


def test_curbside_parked_vehicle_clears_barriers_and_target_lane():
    corners = crossing.mesh_corners(crossing.ROOT / 'ros2_ws/src/uav_learning/config/models/tracking_car/model.sdf')
    parked_min, parked_max = corners[:, 1].min() - 4.4, corners[:, 1].max() - 4.4
    assert 0 < parked_min + 6.0 < .6
    assert parked_min - (-5.675) > .2
    target_lane_min = -.4 + corners[:, 1].min()
    assert target_lane_min - parked_max > 1.5


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


@pytest.mark.parametrize('scenario,color,expected', [
    ('crossing', 'auto', 'red'),
    ('overtaking', 'auto', 'blue'),
    ('crossing', 'red', 'red'),
    ('overtaking', 'red', 'red'),
    ('crossing', 'blue', 'blue'),
    ('overtaking', 'blue', 'blue'),
])
def test_identity_summary_records_effective_model_colors(scenario, color, expected):
    result = crossing.identity_summary([], [], [], scenario, color)
    assert result['distractor_color'] == expected
    assert result['target_color'] == 'red'


def test_overtaking_color_does_not_relax_independent_identity_checks():
    rows = [{'phase': 'pre', 'label': 'tracked_vehicle', 'sim_s': 30} for _ in range(10)]
    rows += [{'phase': 'during', 'label': 'tracked_vehicle', 'sim_s': 35+i*.5,
              'relative_longitudinal_m': -8+i, 'world_lateral_clearance_m': 1.4} for i in range(16)]
    rows += [{'phase': 'post', 'label': 'tracked_vehicle', 'sim_s': 44+i,
              'relative_longitudinal_m': 8+i, 'world_lateral_clearance_m': 1.4} for i in range(10)]
    events = [{'event': 'overtaking_started', 'sim_s': 35},
              {'event': 'overtaking_completed', 'sim_s': 43}]
    results = [crossing.identity_summary(rows, events, [], 'overtaking', color)
               for color in ('red', 'blue')]
    for result in results:
        assert result['identity_independently_verified']
        assert result['overtaking_observed']
        assert result['wrong_identity_observations'] == 0
        assert result['minimum_world_lateral_clearance_m'] == 1.4
    assert results[0]['phase_counts'] == results[1]['phase_counts']
    assert results[0]['scorable_observations'] == results[1]['scorable_observations']
    for color in ('red', 'blue'):
        assert not crossing.identity_summary(rows, [], [], 'overtaking', color)[
            'identity_independently_verified']
    rows[-1]['world_lateral_clearance_m'] = -.1
    for color in ('red', 'blue'):
        assert not crossing.identity_summary(rows, events, [], 'overtaking', color)[
            'identity_independently_verified']
    rows[-1]['world_lateral_clearance_m'] = 1.4
    rows.append({'phase': 'post', 'label': 'crossing_vehicle', 'sim_s': 60})
    for color in ('red', 'blue'):
        result = crossing.identity_summary(rows, events, [], 'overtaking', color)
        assert result['wrong_identity_observations'] == 1
        assert not result['identity_independently_verified']


def test_identity_limitations_distinguish_red_overtaking_from_blue_baseline():
    red = crossing.identity_summary([], [], [], 'overtaking', 'red')
    blue = crossing.identity_summary([], [], [], 'overtaking', 'blue')
    same_crossing = crossing.identity_summary([], [], [], 'crossing', 'red')
    assert any('Different-color overtaking' in text for text in blue['limitations'])
    assert all('Different-color overtaking' not in text for text in red['limitations'])
    assert all('Different-color overtaking' not in text for text in same_crossing['limitations'])
    assert any('overtaking' in text.lower() and 'crossing' in text.lower()
               for text in red['limitations'])
