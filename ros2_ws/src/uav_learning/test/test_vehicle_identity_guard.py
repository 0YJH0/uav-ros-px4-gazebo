import math

import numpy as np
import pytest

from uav_learning.vehicle_target_lock import VehicleTargetLock


APPEARANCE = np.array([[1.0], [0.0], [0.0]], np.float32)


def vehicle(identity, left, right, confidence=0.9):
    return (identity, (right - left) * 20, confidence, left, 40, right, 60)


def acquired():
    lock = VehicleTargetLock()
    target = vehicle(6, 40, 60)
    assert lock.select([target], [APPEARANCE], 100, 100, 0.0) == target
    return lock, target


def test_identical_car_overlap_does_not_update_target_or_refresh_blind_anchor():
    lock, target = acquired()
    measurement = lock.last_measurement.copy()
    rival = vehicle(9, 55, 85)
    assert lock.select([target, rival], [APPEARANCE] * 2, 100, 100, 0.1) is None
    assert lock.overlap_guard_active and lock.overlap_guard_reason == 'similar_vehicle_overlap'
    assert lock.last_seen == lock.last_strong_seen == 0.0 and lock.target_id == 6
    np.testing.assert_array_equal(lock.last_measurement, measurement)
    assert lock.diagnostics[0]['reason'] == 'pending_confirmation'
    assert lock.diagnostics[0]['confirmation_count'] == 1
    assert lock.diagnostics[1]['rejection_reasons']


def test_single_merged_box_is_rejected_after_nearby_rival_disappears():
    lock, target = acquired()
    rival = vehicle(9, 65, 95)
    assert lock.select([target, rival], [APPEARANCE] * 2, 100, 100, 0.1) == target
    merged = vehicle(6, 40, 78)
    assert lock.select([merged], [APPEARANCE], 100, 100, 0.2) is None
    assert lock.overlap_guard_reason == 'merged_vehicle_box'
    assert lock.target_id == 6 and lock.last_seen == 0.1


def test_stale_frame_gap_does_not_erase_pre_crossing_rival_evidence():
    lock, target = acquired()
    lock.select([target, vehicle(9, 65, 95)], [APPEARANCE] * 2, 100, 100, 0.1)
    lock.select([], [], 100, 100, 2.5)
    merged = vehicle(9, 40, 78)
    assert lock.select([merged], [APPEARANCE], 100, 100, 3.0) is None
    assert lock.overlap_guard_reason == 'merged_vehicle_box'
    assert lock.diagnostics[0]['crossing_risk_evidence']['gap_retained']
    assert lock.last_seen == lock.last_strong_seen == 0.1


def test_continued_confirmation_expires_old_rival_evidence():
    lock, target = acquired()
    lock.select([target, vehicle(9, 65, 95)], [APPEARANCE] * 2, 100, 100, 0.1)
    for now in (0.5, 1.0, 1.5, 2.0, 2.5):
        assert lock.select([target], [APPEARANCE], 100, 100, now) == target
    lock.select([vehicle(9, 40, 78)], [APPEARANCE], 100, 100, 3.0)
    assert not lock.overlap_guard_active


def test_gap_retention_has_a_bounded_motion_horizon():
    lock, target = acquired()
    lock.select([target, vehicle(9, 65, 95)], [APPEARANCE] * 2, 100, 100, 0.1)
    lock.select([], [], 100, 100, 11.0)
    lock.select([vehicle(9, 40, 78)], [APPEARANCE], 100, 100, 11.1)
    assert not lock.overlap_guard_active
    assert not lock.crossing_risk_diagnostic['gap_retained']


def test_failed_crossing_geometry_blocks_wide_rival_after_stale_gap():
    lock = VehicleTargetLock(recovery_competition_enabled=False)
    target = (13, 1294., .69, 441.6, 257.7, 481.8, 289.9)
    rival = (14, 3231., .84, 480.5, 258.5, 566.2, 296.2)
    lock.select([target], [APPEARANCE], 960, 540, 0.)
    assert lock.select([target, rival], [APPEARANCE] * 2, 960, 540, .1) == target
    merged = (14, 4035., .76, 444.4, 372.1, 546.3, 411.7)
    warp = np.array([[1., 0., 2.6], [0., 1., 114.4]])
    assert lock.select([merged], [APPEARANCE], 960, 540, 2.92, camera_motion=warp) is None
    assert lock.target_id == 13 and lock.last_seen == .1
    assert lock.overlap_guard_reason == 'merged_vehicle_box'
    assert lock.competition_diagnostic['reason'] == 'inactive'


def test_scale_hold_does_not_extrapolate_growth_during_missing_frames():
    lock, target = acquired()
    lock.predict_box_scale_velocity = False
    state = lock.filter.statePost.copy()
    state[6:] = .2
    lock.filter.statePost = state
    before = lock.last_measurement.copy()
    lock.select([], [], 100, 100, 2.)
    np.testing.assert_allclose(lock.filter.statePost[2:4], before[2:4])
    assert lock.last_seen == 0. and lock.target_id == 6


def test_scale_hold_still_corrects_real_size_changes_and_camera_zoom():
    lock, target = acquired()
    lock.predict_box_scale_velocity = False
    grown = vehicle(6, 39, 61)
    assert lock.select([grown], [APPEARANCE], 100, 100, .1) == grown
    assert np.exp(lock.last_measurement[2, 0]) == .22
    np.testing.assert_allclose(lock.filter.statePost[6:], 0.)
    lock.compensate_camera_motion(np.array([[1.02, 0., 0.], [0., 1.02, 0.]]), 100, 100)
    assert np.isclose(np.exp(lock.last_measurement[2, 0]), .2244)


@pytest.mark.parametrize('continuity', [False, True])
def test_split_car_requires_three_valid_frames_without_double_counting_overlap(continuity):
    lock, target = acquired()
    lock.overlap_confirmation_continuity = continuity
    lock.select([target, vehicle(9, 55, 85)], [APPEARANCE] * 2, 100, 100, 0.1)
    required_after_split = 2 if continuity else 3
    for index in range(required_after_split):
        result = lock.select([target], [APPEARANCE], 100, 100, 0.2 + index * 0.1)
        assert (result is not None) == (index == required_after_split - 1)
        assert lock.diagnostics[0]['confirmation_required'] == 3
        if result is None:
            assert lock.last_seen == 0.
    assert not lock.overlap_guard_active and lock.target_id == 6


def test_guard_rejects_crossing_car_shape_even_if_id_and_color_match():
    lock, target = acquired()
    lock.select([target, vehicle(9, 55, 85)], [APPEARANCE] * 2, 100, 100, 0.1)
    wrong = vehicle(6, 35, 65)
    for now in (0.2, 0.3, 0.4):
        assert lock.select([wrong], [APPEARANCE], 100, 100, now) is None
        assert 'overlap_shape_gate' in lock.diagnostics[0]['rejection_reasons']
    assert lock.last_seen == 0.0


def test_guard_can_recover_after_ten_seconds_but_weak_frames_cannot_unlock_it():
    lock, target = acquired()
    lock.select([target, vehicle(9, 55, 85)], [APPEARANCE] * 2, 100, 100, 0.1)
    assert lock.select([vehicle(6, 40, 60, 0.15)], [APPEARANCE], 100, 100, 0.2) is None
    assert 'overlap_recovery_requires_strong' in lock.diagnostics[0]['rejection_reasons']
    for index in range(3):
        result = lock.select([vehicle(19, 40, 60)], [APPEARANCE], 100, 100, 20 + index * 0.1)
        assert (result is not None) == (index == 2)
    assert lock.target_id == 19 and not lock.overlap_guard_active


def test_camera_motion_registers_guard_shape_without_confirming_identity():
    lock, target = acquired()
    lock.select([target, vehicle(9, 55, 85)], [APPEARANCE] * 2, 100, 100, 0.1)
    warp = np.array([[1.02, 0, 0], [0, 1.02, 0]], dtype=float)
    lock.compensate_camera_motion(warp, 100, 100)
    assert lock.overlap_guard_active and lock.last_seen == 0.0
    assert math.isclose(np.exp(lock.last_measurement[2, 0]), 0.204)


def test_duplicate_roi_boxes_are_not_treated_as_two_crossing_cars():
    lock, target = acquired()
    duplicate = vehicle(None, 40.1, 60.1)
    lock.select([target, duplicate], [APPEARANCE] * 2, 100, 100, 0.1)
    assert not lock.overlap_guard_active


def test_missing_frame_restarts_split_confirmation_without_clearing_guard():
    lock, target = acquired()
    lock.select([target, vehicle(9, 55, 85)], [APPEARANCE] * 2, 100, 100, 0.1)
    lock.select([target], [APPEARANCE], 100, 100, 0.2)
    lock.select([], [], 100, 100, 0.3)
    assert lock.pending_count == 0 and lock.overlap_guard_active
    for index in range(3):
        result = lock.select([target], [APPEARANCE], 100, 100, 0.4 + index * 0.1)
        assert (result is not None) == (index == 2)


def test_different_appearance_distractor_does_not_start_identical_car_guard():
    lock, target = acquired()
    other = np.array([[0.0], [1.0], [0.0]], np.float32)
    assert lock.select([target, vehicle(9, 55, 85)], [APPEARANCE, other], 100, 100, 0.1) == target
    assert not lock.overlap_guard_active


def test_nested_unassigned_height_variant_is_not_a_second_vehicle():
    lock, target = acquired()
    duplicate = (None, 800, 0.35, 40, 40, 60, 80)
    assert lock.select([target, duplicate], [APPEARANCE] * 2, 100, 100, 0.1) == target
    assert not lock.overlap_guard_active and lock.last_similar_rival is None


def test_nested_boxes_with_distinct_confirmed_ids_remain_ambiguous():
    lock, target = acquired()
    rival = (9, 800, 0.9, 40, 40, 60, 80)
    assert lock.select([target, rival], [APPEARANCE] * 2, 100, 100, 0.1) is None
    assert lock.overlap_guard_active
