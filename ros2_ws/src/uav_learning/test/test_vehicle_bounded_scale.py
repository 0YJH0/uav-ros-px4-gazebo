import math
from types import SimpleNamespace

import numpy as np
import pytest

from uav_learning.vehicle_target_lock import VehicleTargetLock


APPEARANCE = np.array([1., 0., 0.], np.float32)
WIDTH, HEIGHT = 960, 540


def box(width=80., height=56., track_id=16, confidence=.9):
    return (track_id, width * height, confidence,
            480. - width / 2, 270. - height / 2,
            480. + width / 2, 270. + height / 2)


def select(lock, item, now, warp=None, appearance=APPEARANCE):
    return lock.select([item], [appearance], WIDTH, HEIGHT, now,
                       camera_motion=warp)


def acquired(**kwargs):
    lock = VehicleTargetLock(recovery_competition_enabled=False, **kwargs)
    initial = box()
    assert select(lock, initial, 0.) == initial
    return lock, initial


@pytest.mark.parametrize('axis', [0, 1])
def test_valid_interior_single_axis_expansion_updates_measured_geometry(axis):
    lock, initial = acquired()
    sizes = [80., 56.]
    sizes[axis] *= 1.5
    changed = box(*sizes)
    assert select(lock, changed, .2) == changed
    assert not lock.diagnostics[0]['vertical_truncated']
    np.testing.assert_allclose(lock.last_measurement,
                               lock.measurement(changed, WIDTH, HEIGHT))
    assert lock.diagnostics[0]['geometry_update'] == 'full'
    assert not lock.diagnostics[0].get('protected_axes')
    assert lock.last_seen == lock.last_strong_seen == .2
    assert lock.target_id == initial[0]


@pytest.mark.parametrize('axis', [0, 1])
def test_unclipped_single_axis_contraction_can_correct_previous_large_anchor(axis):
    lock, _ = acquired()
    sizes = [80., 56.]
    sizes[axis] /= 1.5
    contracted = box(*sizes)
    assert select(lock, contracted, .2) == contracted
    np.testing.assert_allclose(lock.last_measurement,
                               lock.measurement(contracted, WIDTH, HEIGHT))
    assert lock.diagnostics[0]['geometry_update'] == 'full'
    assert not lock.diagnostics[0].get('protected_axes')


def test_recorded_merged_80px_anchor_updates_to_correct_57px_observation():
    lock = VehicleTargetLock(recovery_competition_enabled=False)
    # Recorded boxes at 180.787 s and 180.950 s: the first encloses both cars.
    merged = (16, 5904.302715301514, .7400277853012085,
              441.70269775390625, 299.97296142578125,
              515.0347290039062, 380.48760986328125)
    correct = (16, 4156.585800267756, .7769088745117188,
               442.30865478515625, 310.6517639160156,
               514.9821166992188, 367.8471374511719)
    assert select(lock, merged, 0.) == merged
    assert select(lock, correct, .163100313) == correct
    expected = lock.measurement(correct, WIDTH, HEIGHT)
    np.testing.assert_allclose(lock.last_measurement, expected)
    assert lock.diagnostics[0]['geometry_update'] == 'full'
    assert select(lock, correct, .326200626) == correct
    np.testing.assert_allclose(lock.last_measurement, expected)
    assert not lock.diagnostics[0].get('protected_axes')


def test_continuously_confirmed_tracking_retains_legacy_constant_velocity_model():
    bounded, _ = acquired()
    legacy, _ = acquired(bounded_scale_prediction=False)
    for now in np.arange(.2, 4.01, .2):
        observed = box(width=80. * math.exp(.1 * now), height=56. * math.exp(-.05 * now))
        assert select(bounded, observed, float(now)) == observed
        assert select(legacy, observed, float(now)) == observed
        np.testing.assert_allclose(bounded.last_measurement, legacy.last_measurement)
        np.testing.assert_allclose(bounded.filter.statePost, legacy.filter.statePost, atol=1e-12)


@pytest.mark.parametrize('now', [.2, .5, 1., 5., 9.9])
def test_unconfirmed_gap_bounds_both_scale_directions_without_refreshing_identity(now):
    lock, _ = acquired()
    anchor = lock.last_measurement.copy()
    state = lock.filter.statePost.copy()
    state[6:, 0] = [.3, -.3]
    lock.filter.statePost = state
    assert lock.select([], [], WIDTH, HEIGHT, now) is None
    change = lock.filter.statePost[2:4] - anchor[2:4]
    assert np.max(np.abs(change)) <= math.log(1.25) + 1e-12
    if now <= .5:
        np.testing.assert_allclose(change[:, 0], np.array([.3, -.3]) * now)
        np.testing.assert_allclose(lock.filter.statePost[6:8, 0], [.3, -.3])
    else:
        assert 0 <= lock.filter.statePost[6, 0] < .3
        assert -.3 < lock.filter.statePost[7, 0] <= 0
    assert lock.last_seen == lock.last_strong_seen == 0.
    assert lock.target_id == 16
    np.testing.assert_array_equal(lock.last_measurement, anchor)


def test_scale_decay_is_independent_of_missing_frame_call_frequency():
    sparse, _ = acquired()
    dense, _ = acquired()
    anchor = sparse.last_measurement.copy()
    velocity = np.array([.1, -.08])
    for lock in (sparse, dense):
        state = lock.filter.statePost.copy()
        state[6:, 0] = velocity
        lock.filter.statePost = state
    sparse.select([], [], WIDTH, HEIGHT, 2.)
    for now in np.linspace(.1, 2., 20):
        dense.select([], [], WIDTH, HEIGHT, float(now))
    np.testing.assert_allclose(sparse.filter.statePost[2:4],
                               dense.filter.statePost[2:4], atol=1e-10)
    np.testing.assert_allclose(sparse.filter.statePost[6:8],
                               dense.filter.statePost[6:8], atol=1e-10)
    np.testing.assert_allclose(sparse.filter.statePost[2:4, 0],
                               anchor[2:4, 0] + velocity * (.5 + 1. - math.exp(-1.5)))
    np.testing.assert_allclose(sparse.filter.statePost[6:8, 0],
                               velocity * math.exp(-1.5))


def test_camera_zoom_moves_trusted_scale_instead_of_hitting_old_scale_limit():
    lock, _ = acquired()
    initial = lock.last_measurement.copy()
    state = lock.filter.statePost.copy()
    state[6:] = .3
    lock.filter.statePost = state
    zoom = np.array([[1.05, 0., -24.], [0., 1.05, -13.5]])
    for index in range(1, 6):
        lock.select([], [], WIDTH, HEIGHT, index * .2, camera_motion=zoom)
    np.testing.assert_allclose(lock.last_measurement[2:4],
                               initial[2:4] + 5 * math.log(1.05))
    assert np.all(lock.last_measurement[2:4] > initial[2:4] + math.log(1.25))
    assert np.max(np.abs(lock.filter.statePost[2:4] - lock.last_measurement[2:4])) <= math.log(1.25) + 1e-12
    assert lock.last_seen == lock.last_strong_seen == 0.


def test_equal_axis_real_approach_updates_shape_without_anisotropic_freeze():
    lock, _ = acquired()
    grown = box(width=80. * 1.3, height=56. * 1.3)
    assert select(lock, grown, .2) == grown
    np.testing.assert_allclose(lock.last_measurement[2:4, 0],
                               np.log([104. / WIDTH, 72.8 / HEIGHT]))
    assert lock.diagnostics[0]['geometry_update'] == 'full'
    assert not lock.diagnostics[0].get('protected_axes')


def test_rejected_anomalous_shape_does_not_refresh_identity_or_anchor():
    lock, initial = acquired()
    before = lock.last_measurement.copy()
    wrong = np.array([0., 1., 0.], np.float32)
    assert select(lock, box(height=84.), .2, appearance=wrong) is None
    assert 'appearance_gate' in lock.diagnostics[0]['rejection_reasons']
    assert lock.last_seen == lock.last_strong_seen == 0.
    assert lock.target_id == initial[0]
    np.testing.assert_array_equal(lock.last_measurement, before)


def test_disabled_bound_preserves_legacy_unbounded_scale_for_ablation():
    lock, _ = acquired(bounded_scale_prediction=False)
    before = lock.last_measurement.copy()
    state = lock.filter.statePost.copy()
    state[6:, 0] = [.3, -.3]
    lock.filter.statePost = state
    lock.select([], [], WIDTH, HEIGHT, 5.)
    np.testing.assert_allclose(lock.filter.statePost[2:4, 0], before[2:4, 0] + [1.5, -1.5])
    np.testing.assert_allclose(lock.filter.statePost[6:8, 0], [.3, -.3])
    assert lock.last_seen == lock.last_strong_seen == 0.


def test_disabled_bound_preserves_legacy_interior_shape_update_for_ablation():
    lock, _ = acquired(bounded_scale_prediction=False)
    changed = box(height=84.)
    assert select(lock, changed, .2) == changed
    assert lock.diagnostics[0]['geometry_update'] == 'full'
    assert math.exp(lock.last_measurement[3, 0]) * HEIGHT == pytest.approx(84.)


@pytest.mark.parametrize('bounded', [False, True])
def test_edge_truncation_preserves_legacy_predicted_geometry_in_continuous_tracking(bounded):
    lock = VehicleTargetLock(bounded_scale_prediction=bounded)
    initial = (16, 6400., .9, 440., 450., 520., 530.)
    partial = (16, 5200., .9, 440., 475., 520., 540.)
    assert select(lock, initial, 0.) == initial
    before = lock.last_measurement.copy()
    state = lock.filter.statePost.copy()
    state[5, 0], state[7, 0] = .01, .1
    lock.filter.statePost = state
    assert select(lock, partial, .2) == partial
    expected = before[[1, 3], 0] + np.array([.01, .1]) * .2
    np.testing.assert_allclose(lock.last_measurement[[1, 3], 0], expected)
    np.testing.assert_allclose(lock.filter.statePost[[5, 7]], 0.)


def test_edge_clipping_does_not_mask_valid_horizontal_change():
    lock = VehicleTargetLock()
    initial = (16, 6400., .9, 440., 450., 520., 530.)
    changed = (16, 7800., .9, 420., 475., 540., 540.)
    assert select(lock, initial, 0.) == initial
    before = lock.last_measurement.copy()
    assert select(lock, changed, .2) == changed
    assert lock.diagnostics[0]['vertical_truncated']
    assert lock.diagnostics[0]['geometry_update'] == 'horizontal_only'
    assert set(lock.diagnostics[0]['protected_axes']) == {
        'center_y', 'log_height', 'velocity_y', 'velocity_log_height'}
    np.testing.assert_allclose(lock.last_measurement[[1, 3]], before[[1, 3]])
    assert math.exp(lock.last_measurement[2, 0]) * WIDTH == pytest.approx(120.)
    np.testing.assert_allclose(lock.filter.statePost[[5, 7]], 0.)


@pytest.mark.parametrize('bounded', [False, True])
@pytest.mark.parametrize('overlap', [False, True])
def test_airborne_identity_reset_preserves_recovery_ablation_flags(bounded, overlap):
    from uav_learning.perception_node import PerceptionNode

    node = SimpleNamespace(
        target_id=16, airborne_search_initialized=False,
        target_lock=VehicleTargetLock(),
        settings={'target_reacquire_timeout': 10.,
                  'acquisition_center_gate': 1., 'acquisition_confirm_frames': 1,
                  'confidence_threshold': .25, 'weak_idless_confirm_frames': 3,
                  'weak_idless_max_age': 2., 'recovery_competition_enabled': False,
                  'predict_box_scale_velocity': True,
                  'overlap_candidate_recovery': overlap,
                  'bounded_scale_prediction': bounded})
    ground_lock = node.target_lock
    PerceptionNode.state_callback(node, SimpleNamespace(data='SEARCH'))
    assert node.airborne_search_initialized
    assert node.target_lock is not ground_lock
    assert node.target_id is None
    assert node.target_lock.bounded_scale_prediction is bounded
    assert node.target_lock.overlap_candidate_recovery is overlap
    assert not node.target_lock.recovery_competition_enabled
    assert node.target_lock.predict_box_scale_velocity
