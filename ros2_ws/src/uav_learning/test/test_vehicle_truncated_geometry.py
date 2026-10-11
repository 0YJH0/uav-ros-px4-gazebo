import math

import numpy as np
import pytest

from uav_learning.vehicle_target_lock import VehicleTargetLock


APPEARANCE = np.array([1., 0., 0.], np.float32)


def box(y1, y2, track_id=15, confidence=.9):
    return (track_id, 110 * (y2-y1), confidence, 400., y1, 510., y2)


def select(lock, item, now, warp=None):
    return lock.select([item], [APPEARANCE], 960, 540, now, camera_motion=warp)


@pytest.mark.parametrize('top', [False, True])
def test_censored_box_preserves_vertical_geometry_and_zeroes_vertical_velocity(top):
    lock = VehicleTargetLock(recovery_competition_enabled=False)
    initial = box(10, 90) if top else box(450, 530)
    partial = box(0, 65) if top else box(475, 540)
    assert select(lock, initial, 0) == initial
    vertical = lock.filter.statePost[[1, 3]].copy()
    for now in (.1, .2, .3):
        assert select(lock, partial, now) == partial
        np.testing.assert_allclose(lock.filter.statePost[[1, 3]], vertical)
        np.testing.assert_allclose(lock.last_measurement[[1, 3]], vertical)
        np.testing.assert_allclose(lock.filter.statePost[[5, 7]], 0)
        assert lock.diagnostics[0]['geometry_update'] == 'horizontal_only'
        np.testing.assert_array_equal(lock.filter.measurementMatrix, np.eye(4, 8))
    assert select(lock, initial, .4) == initial
    assert lock.diagnostics[0]['geometry_update'] == 'full'


def test_clipped_box_does_not_poison_the_last_full_view_after_prediction_timeout():
    lock = VehicleTargetLock()
    select(lock, box(450, 530), 0)
    full_height = lock.last_measurement[3, 0]
    select(lock, box(475, 540), .1)
    assert lock.last_measurement[3, 0] == full_height
    for now in (11., 11.1, 11.2):
        result = select(lock, box(450, 530, track_id=26), now)
    assert result is not None and lock.target_id == 26


def test_clipped_acquisition_and_stale_reacquisition_cannot_seed_full_geometry():
    lock = VehicleTargetLock()
    assert select(lock, box(475, 540), 0) is None
    assert lock.last_seen is None and lock.reference is None
    assert lock.diagnostics[0]['reason'] == 'truncated_acquisition_box'
    select(lock, box(450, 530), .1)
    seen = lock.last_seen
    assert select(lock, box(475, 540), 11) is None
    assert lock.last_seen == seen and lock.target_id == 15
    assert 'truncated_reacquisition_box' in lock.diagnostics[0]['rejection_reasons']


def test_camera_scaling_still_updates_full_height_without_learning_clipping():
    lock = VehicleTargetLock()
    select(lock, box(450, 530), 0)
    warp = np.array([[1.01, 0., -4.55], [0., 1.01, -4.9]])
    assert select(lock, box(475, 540), .1, warp) is not None
    assert math.exp(lock.filter.statePost[3, 0]) * 540 == pytest.approx(80 * 1.01)
    assert lock.filter.statePost[7, 0] == 0


def test_clipping_protection_does_not_relax_gates_or_allow_wrong_appearance():
    lock = VehicleTargetLock()
    select(lock, box(450, 530), 0)
    partial = box(475, 540)
    assert lock.select([partial], [np.array([0., 1., 0.], np.float32)], 960, 540, .1) is None
    assert 'appearance_gate' in lock.diagnostics[0]['rejection_reasons']
    tiny = box(532, 540)
    assert select(lock, tiny, .2) is None
    assert 'scale_gate' in lock.diagnostics[0]['rejection_reasons']
    assert lock.diagnostics[0]['log_scale_gate'] == pytest.approx(math.log(2))
    assert lock.diagnostics[0]['mahalanobis_gate'] == 18.5
