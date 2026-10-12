from itertools import product
from types import SimpleNamespace

import numpy as np
import pytest

from uav_learning.vehicle_target_lock import VehicleTargetLock


APPEARANCE = np.array([[1.], [0.], [0.]], np.float32)
OTHER_APPEARANCE = np.array([[0.], [1.], [0.]], np.float32)
IDENTITY_WARP = np.eye(2, 3)


def vehicle(identity=6, left=40., right=60., confidence=.9):
    return (identity, (right - left) * 20., confidence, left, 40., right, 60.)


def observe(lock, candidates, now, warp=IDENTITY_WARP, histograms=None):
    appearances = [APPEARANCE] * len(candidates) if histograms is None else histograms
    return lock.select(candidates, appearances, 100, 100, now, camera_motion=warp)


def mature_overlap(**kwargs):
    lock = VehicleTargetLock(**kwargs)
    target, rival = vehicle(), vehicle(9, 55., 85.)
    assert observe(lock, [target], 0.) == target
    for index, now in enumerate((.1, .2, .3)):
        result = observe(lock, [target, rival], now)
        assert (result == target) == (index == 2)
    return lock, target, rival


@pytest.mark.parametrize('first,second', [
    ('partial_overlap', 'overlap_recovery'), ('overlap_recovery', 'partial_overlap')])
def test_same_assigned_candidate_accumulates_across_overlap_evidence_labels(first, second):
    lock = VehicleTargetLock()
    target = vehicle()
    measurement = lock.measurement(target, 100, 100)
    for index, evidence in enumerate((first, second, first, second)):
        confirmed = lock.confirm(target, measurement, .1 + index * .1, 3, evidence)
        assert confirmed == (index >= 2)
        assert lock.pending_count == min(index + 1, 3)
    assert lock.last_seen is None


def test_disabled_continuity_keeps_legacy_evidence_label_reset():
    lock = VehicleTargetLock(overlap_confirmation_continuity=False)
    target = vehicle()
    measurement = lock.measurement(target, 100, 100)
    for index, evidence in enumerate(('partial_overlap', 'overlap_recovery') * 3):
        assert not lock.confirm(target, measurement, .1 + index * .1, 3, evidence)
        assert lock.pending_count == 1


@pytest.mark.parametrize('previous,current', [(6, 19), (6, None), (None, 6), (None, None)])
def test_cross_label_continuity_requires_the_same_non_none_identity(previous, current):
    lock = VehicleTargetLock()
    old = vehicle(previous)
    measurement = lock.measurement(old, 100, 100)
    for now in (.1, .2, .3):
        lock.confirm(old, measurement, now, 3, 'partial_overlap')
    assert not lock.confirm(vehicle(current), measurement, .4, 3, 'overlap_recovery')
    assert lock.pending_count == 1


@pytest.mark.parametrize('discontinuity', ['gap', 'center', 'scale', 'evidence_family'])
def test_cross_label_continuity_does_not_bypass_temporal_or_geometry_checks(discontinuity):
    lock = VehicleTargetLock()
    target = vehicle()
    measurement = lock.measurement(target, 100, 100)
    for now in (.1, .2, .3):
        lock.confirm(target, measurement, now, 3, 'partial_overlap')
    changed = measurement.copy()
    if discontinuity == 'center':
        changed[0] += .06
    elif discontinuity == 'scale':
        changed[2] += .21
    evidence = 'weak_idless' if discontinuity == 'evidence_family' else 'overlap_recovery'
    now = .9 if discontinuity == 'gap' else .4
    assert not lock.confirm(target, changed, now, 3, evidence)
    assert lock.pending_count == 1 and lock.last_seen is None


@pytest.mark.parametrize('competition_enabled', [False, True])
def test_mature_identity_does_not_stutter_when_rival_appears_or_disappears(competition_enabled):
    lock, target, rival = mature_overlap(recovery_competition_enabled=competition_enabled)
    for index, rival_visible in enumerate((False, True, False, False, True, True, False, True)):
        now = .4 + index * .1
        candidates = [target, rival] if rival_visible else [target]
        assert observe(lock, candidates, now) == target
        assert lock.last_seen == lock.last_strong_seen == now
        assert lock.target_id == 6


def test_ordinary_confirmed_frames_refresh_continuity_clock_without_extending_missing_frames():
    lock, target, rival = mature_overlap()
    for now in (.4, .6, .8, 1., 1.2):
        assert observe(lock, [target], now) == target
    assert observe(lock, [target, rival], 1.3) == target
    assert observe(lock, [], 1.4) is None
    assert lock.last_seen == lock.last_strong_seen == 1.3
    for index, now in enumerate((1.5, 1.6, 1.7)):
        assert (observe(lock, [target, rival], now) == target) == (index == 2)


def test_legacy_mode_still_reconfirms_after_rival_disappears():
    lock, target, _ = mature_overlap(overlap_confirmation_continuity=False)
    assert observe(lock, [target], .4) is None
    assert lock.last_seen == .3


@pytest.mark.parametrize('interruption', ['missing', 'gap', 'identity', 'unassigned'])
def test_cross_mode_confirmation_revalidates_after_identity_or_observation_discontinuity(interruption):
    lock, target, rival = mature_overlap()
    assert observe(lock, [target], .4) == target
    if interruption == 'missing':
        assert observe(lock, [], .45) is None
    elif interruption == 'identity':
        target = vehicle(19)
    elif interruption == 'unassigned':
        target = vehicle(None)
    times = (1., 1.1, 1.2) if interruption == 'gap' else (.5, .6, .7)
    for index, now in enumerate(times):
        selected = observe(lock, [target, rival], now)
        assert (selected == target) == (index == 2)
        if index < 2:
            assert lock.last_seen == .4 and lock.target_id == 6


@pytest.mark.parametrize('failure', ['appearance', 'center', 'scale'])
def test_failed_candidate_gates_break_mature_confirmation_continuity(failure):
    lock, target, rival = mature_overlap()
    assert observe(lock, [target], .4) == target
    rejected = (vehicle(left=10., right=30.) if failure == 'center' else
                vehicle(left=47., right=53.) if failure == 'scale' else target)
    histogram = OTHER_APPEARANCE if failure == 'appearance' else APPEARANCE
    assert observe(lock, [rejected], .5, histograms=[histogram]) is None
    assert lock.last_seen == .4
    for index, now in enumerate((.6, .7, .8)):
        assert (observe(lock, [target, rival], now) == target) == (index == 2)


@pytest.mark.parametrize('warp', [None, IDENTITY_WARP])
def test_mature_continuity_cannot_bypass_unresolved_candidate_competition(warp):
    lock = VehicleTargetLock(recovery_competition_enabled=True)
    target, rival = vehicle(left=46., right=54.), vehicle(9, 51., 59.)
    assert observe(lock, [target], 0.) == target
    for index, now in enumerate((.1, .2, .3)):
        assert (observe(lock, [target, rival], now) == target) == (index == 2)
    ambiguous = [vehicle(6, 45., 53.), vehicle(19, 47., 55.)]
    assert observe(lock, ambiguous, .4, warp=warp) is None
    assert lock.last_seen == .3
    for index, now in enumerate((.5, .6, .7)):
        assert (observe(lock, [target, rival], now) == target) == (index == 2)


def test_mature_confirmation_cannot_refresh_ten_second_blind_anchor():
    lock, target, rival = mature_overlap()
    assert observe(lock, [target], .4) == target
    for now in (.5, 3., 6., 10.5):
        assert observe(lock, [], now) is None
        assert lock.last_seen == lock.last_strong_seen == .4
    assert lock.elapsed_since_seen > 10.
    for index, now in enumerate((20., 20.1, 20.2)):
        assert (observe(lock, [target, rival], now) == target) == (index == 2)


@pytest.mark.parametrize('candidate,scale,continuity', list(product((False, True), repeat=3)))
def test_airborne_identity_reset_preserves_all_three_association_flags(candidate, scale, continuity):
    from uav_learning.perception_node import PerceptionNode

    previous, _, _ = mature_overlap()
    node = SimpleNamespace(target_id=6, target_lock=previous, settings={
        'target_reacquire_timeout': 10., 'acquisition_center_gate': .35,
        'acquisition_confirm_frames': 3, 'confidence_threshold': .25,
        'weak_idless_confirm_frames': 3, 'weak_idless_max_age': 2.,
        'recovery_competition_enabled': False, 'predict_box_scale_velocity': True,
        'overlap_candidate_recovery': candidate, 'bounded_scale_prediction': scale,
        'overlap_confirmation_continuity': continuity,
    })
    PerceptionNode.reset_airborne_identity(node)
    assert node.target_id is None and node.target_lock is not previous
    assert node.target_lock.last_seen is None and node.target_lock.pending_count == 0
    assert node.target_lock.reference is None
    assert node.target_lock.overlap_candidate_recovery is candidate
    assert node.target_lock.bounded_scale_prediction is scale
    assert node.target_lock.overlap_confirmation_continuity is continuity
    assert node.target_lock.prediction_horizon == 10.
