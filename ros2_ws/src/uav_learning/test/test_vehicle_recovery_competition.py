import numpy as np
import pytest

from uav_learning.vehicle_recovery_competition import RecoveryCompetition
from uav_learning.vehicle_target_lock import VehicleTargetLock


HISTOGRAM = np.array([[1.], [0.], [0.]], np.float32)
IDENTITY_WARP = np.eye(2, 3)


def car(identity, center, width=0.08):
    return (identity, width * 1000, 0.9,
            (center - width / 2) * 100, 40, (center + width / 2) * 100, 60)


def guarded(enabled=True):
    lock = VehicleTargetLock(recovery_competition_enabled=enabled)
    lock.select([car(6, 0.5)], [HISTOGRAM], 100, 100, 0.)
    lock.select([car(6, 0.5), car(9, 0.55)], [HISTOGRAM] * 2,
                100, 100, 0.1, IDENTITY_WARP)
    assert lock.overlap_guard_active and lock.last_seen == 0.
    return lock


def test_competition_reuses_three_real_frames_without_duplicate_confirmation():
    lock = guarded()
    for tick in range(3):
        now = 20. + tick * 0.2
        target = car(19, 0.45)
        selected = lock.select([target, car(9, 0.6 + tick * 0.01)], [HISTOGRAM] * 2,
                               100, 100, now, IDENTITY_WARP)
        assert (selected is not None) == (tick == 2)
        if tick < 2:
            assert lock.target_id == 6 and lock.last_seen == 0.
        if tick >= 2:
            assert lock.diagnostics[0]['competition_resolved_ambiguity']
    assert selected == target and lock.target_id == 19


@pytest.mark.parametrize('enabled,warp', [(False, IDENTITY_WARP), (True, None)])
def test_disabled_or_unregistered_motion_cannot_resolve_identity(enabled, warp):
    lock = guarded(enabled)
    for tick in range(5):
        assert lock.select([car(19, 0.45), car(9, 0.6 + tick * 0.01)], [HISTOGRAM] * 2,
                           100, 100, 20. + tick * 0.2, warp) is None
    assert lock.last_seen == 0. and lock.target_id == 6


def test_equal_motion_identical_cars_never_force_a_winner():
    lock = guarded()
    for tick in range(10):
        assert lock.select([car(19, 0.45), car(9, 0.6)], [HISTOGRAM] * 2,
                           100, 100, 20. + tick * 0.2, IDENTITY_WARP) is None
    assert lock.competition.diagnostic['reason'] == 'motion_evidence_ambiguous'
    assert lock.target_id == 6 and lock.last_seen == 0.


def evidence(now, first=0.45, second=0.6, identities=(19, 9)):
    candidates = [car(identities[0], first), car(identities[1], second)]
    matches = [(0.1, 0, VehicleTargetLock.measurement(candidates[0], 100, 100)),
               (0.12, 1, VehicleTargetLock.measurement(candidates[1], 100, 100))]
    return matches, candidates, now, True


def test_camera_compensation_moves_history_without_adding_observations():
    competition = RecoveryCompetition()
    competition.start([0., 0.])
    competition.choose(*evidence(0.))
    competition.compensate(np.eye(2), np.array([[0.02], [0.01]]))
    sample = competition.histories[19][0]
    np.testing.assert_allclose(sample['center'], [0.47, 0.51])
    assert sample['time'] == 0. and len(competition.histories[19]) == 1


@pytest.mark.parametrize('kind', ['gap', 'missing', 'new_id', 'unassigned', 'new_rival'])
def test_missing_or_immature_evidence_cannot_select_a_winner(kind):
    competition = RecoveryCompetition()
    competition.start([0., 0.])
    competition.choose(*evidence(0.))
    competition.choose(*evidence(0.2, second=0.61))
    if kind == 'missing':
        competition.choose([], [], 0.3, True)
    args = evidence(1. if kind == 'gap' else 0.4, second=0.62,
                    identities=(20 if kind == 'new_id' else None if kind == 'unassigned' else 19,
                                10 if kind == 'new_rival' else 9))
    assert competition.choose(*args) is None


def test_rejected_geometry_never_enters_competition():
    lock = guarded()
    for tick in range(5):
        guarded_before = lock.overlap_guard_active
        lock.select([car(19, 0.45, width=0.15), car(9, 0.6 + tick * 0.01)],
                    [HISTOGRAM] * 2, 100, 100, 20. + tick * 0.2, IDENTITY_WARP)
        reasons = set(lock.diagnostics[0]['rejection_reasons'])
        assert reasons and not lock.diagnostics[0]['accepted']
        if guarded_before:
            assert reasons & {'overlap_shape_gate', 'merged_vehicle_box'}
        assert 19 not in lock.competition.histories


def test_competition_memory_is_bounded():
    competition = RecoveryCompetition()
    competition.start([0., 0.])
    for tick in range(100):
        competition.choose(*evidence(tick * 0.1, second=0.6))
    assert len(competition.histories) == 2
    assert all(len(samples) == 5 for samples in competition.histories.values())
