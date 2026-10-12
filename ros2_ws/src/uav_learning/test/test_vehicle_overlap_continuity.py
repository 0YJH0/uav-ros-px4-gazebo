import numpy as np
import pytest

from uav_learning.vehicle_target_lock import VehicleTargetLock


APPEARANCE = np.array([[1.], [0.], [0.]], np.float32)
OTHER_APPEARANCE = np.array([[0.], [1.], [0.]], np.float32)
IDENTITY_WARP = np.eye(2, 3)


def vehicle(identity, left=40., right=60., top=40., bottom=60., confidence=.9):
    return (identity, (right - left) * (bottom - top), confidence,
            left, top, right, bottom)


def observe(lock, candidates, now, warp=IDENTITY_WARP, histograms=None):
    return lock.select(candidates,
                       [APPEARANCE] * len(candidates) if histograms is None else histograms,
                       100, 100, now, camera_motion=warp)


def acquired(**kwargs):
    lock = VehicleTargetLock(**kwargs)
    target = vehicle(6)
    assert observe(lock, [target], 0.) == target
    return lock, target, vehicle(9, 55., 85.)


def mature_overlap(lock, target, rival):
    for index, now in enumerate((.1, .2, .3)):
        selected = observe(lock, [target, rival], now)
        assert (selected == target) == (index == 2)


@pytest.mark.parametrize('competition_enabled', [False, True])
def test_partial_overlap_confirms_three_frames_then_emits_every_frame(competition_enabled):
    lock, target, rival = acquired(recovery_competition_enabled=competition_enabled)
    anchor = lock.last_measurement.copy()
    assert observe(lock, [target, rival], .1) is None
    assert lock.last_seen == lock.last_strong_seen == 0.
    np.testing.assert_array_equal(lock.last_measurement, anchor)
    assert observe(lock, [target, rival], .2) is None
    for now in (.3, .4, .5, .6, .7):
        assert observe(lock, [target, rival], now) == target
        assert lock.target_id == 6 and lock.last_seen == now
        assert lock.diagnostics[0]['accepted']
        assert not lock.diagnostics[1]['accepted']


def test_ablation_retains_legacy_global_overlap_rejection():
    lock, target, rival = acquired(overlap_candidate_recovery=False)
    for now in (.1, .2, .3, .4, .5):
        assert observe(lock, [target, rival], now) is None
        assert all('similar_vehicle_overlap' in row['rejection_reasons']
                   for row in lock.diagnostics)
    assert lock.last_seen == 0. and lock.target_id == 6


@pytest.mark.parametrize('interruption', ['missing', 'gap', 'new_id'])
def test_mature_overlap_evidence_restarts_after_discontinuity(interruption):
    lock, target, rival = acquired()
    mature_overlap(lock, target, rival)
    if interruption == 'missing':
        assert observe(lock, [], .35) is None
    if interruption == 'new_id':
        target = vehicle(19)
    times = (.9, 1., 1.1) if interruption == 'gap' else (.4, .5, .6)
    for index, now in enumerate(times):
        selected = observe(lock, [target, rival], now)
        assert (selected == target) == (index == 2)
        if index < 2:
            assert lock.last_seen == .3 and lock.target_id == 6
    assert lock.target_id == target[0]


def test_unassigned_overlap_box_cannot_bridge_mature_evidence_to_another_id():
    lock, target, rival = acquired()
    mature_overlap(lock, target, rival)
    unassigned = vehicle(None)
    for index, now in enumerate((.4, .5, .6)):
        selected = observe(lock, [unassigned, rival], now)
        assert (selected == unassigned) == (index == 2)
        if index < 2:
            assert lock.last_seen == .3
    assert lock.target_id == 6
    new_identity = vehicle(19)
    for index, now in enumerate((.7, .8, .9)):
        selected = observe(lock, [new_identity, rival], now)
        assert (selected == new_identity) == (index == 2)
        if index < 2:
            assert lock.last_seen == .6 and lock.target_id == 6
    assert lock.target_id == 19


def test_merged_candidate_does_not_reject_a_separate_valid_target_candidate():
    lock, target, _ = acquired()
    assert observe(lock, [target, vehicle(9, 65., 95.)], .1) == target
    merged = vehicle(9, 30., 68.)
    for index, now in enumerate((.2, .3, .4)):
        selected = observe(lock, [target, merged], now)
        assert (selected == target) == (index == 2)
        assert not lock.diagnostics[1]['accepted']
        assert lock.diagnostics[1]['rejection_reasons']
        assert 9 not in lock.competition.histories
    assert lock.target_id == 6


@pytest.mark.parametrize('axis', ['horizontal', 'vertical'])
def test_single_merged_box_cannot_refresh_identity_even_with_original_id(axis):
    lock, target, _ = acquired()
    assert observe(lock, [target, vehicle(9, 65., 95.)], .1) == target
    merged = vehicle(6, 31., 69.) if axis == 'horizontal' else vehicle(6, top=31., bottom=69.)
    for now in (.2, .3, .4, .5):
        assert observe(lock, [merged], now) is None
        assert lock.diagnostics[0]['rejection_reasons']
    assert lock.last_seen == .1 and lock.target_id == 6


def test_mostly_overlapping_distinct_vehicles_never_force_identity_confirmation():
    lock, _, _ = acquired()
    candidates = [vehicle(6, 37., 57.), vehicle(9, 43., 63.)]
    for index in range(15):
        assert observe(lock, candidates, .1 + index * .1) is None
    assert lock.last_seen == 0. and lock.target_id == 6


def test_nested_distinct_ids_are_not_treated_as_roi_duplicates():
    lock, target, _ = acquired()
    nested = vehicle(9, top=40., bottom=80.)
    for now in (.1, .2, .3, .4):
        assert observe(lock, [target, nested], now) is None
    assert lock.last_seen == 0.


def test_low_confidence_unassigned_roi_duplicate_does_not_hide_valid_overlap_candidate():
    lock, target, rival = acquired()
    duplicate = vehicle(None, 40.1, 60.1, confidence=.15)
    for index, now in enumerate((.1, .2, .3, .4)):
        selected = observe(lock, [target, rival, duplicate], now)
        assert (selected == target) == (index >= 2)
        assert not lock.diagnostics[2]['accepted']


@pytest.mark.parametrize('failure', ['appearance', 'center', 'scale', 'confidence'])
def test_stable_id_and_mature_overlap_do_not_bypass_original_gates(failure):
    lock, target, rival = acquired()
    mature_overlap(lock, target, rival)
    histograms = [OTHER_APPEARANCE if failure == 'appearance' else APPEARANCE, APPEARANCE]
    if failure == 'center':
        target = vehicle(6, 10., 30.)
    elif failure == 'scale':
        target = vehicle(6, 46., 54., top=46., bottom=54.)
    elif failure == 'confidence':
        target = vehicle(6, confidence=.15)
    assert observe(lock, [target, rival], .4, histograms=histograms) is None
    assert lock.diagnostics[0]['rejection_reasons']
    assert lock.last_seen == .3 and lock.target_id == 6


@pytest.mark.parametrize('warp', [None, IDENTITY_WARP])
def test_equal_motion_candidates_remain_ambiguous_after_occlusion(warp):
    lock = VehicleTargetLock()
    target = vehicle(6, 46., 54.)
    assert observe(lock, [target], 0.) == target
    assert observe(lock, [target, vehicle(9, 51., 59.)], .1) is None
    for index in range(8):
        candidates = [vehicle(19, 41., 49.), vehicle(9, 56., 64.)]
        assert observe(lock, candidates, 20. + index * .2, warp=warp) is None
    assert lock.last_seen == 0. and lock.target_id == 6


def test_unconfirmed_overlap_does_not_extend_blind_anchor_and_can_recover_after_ten_seconds():
    lock, target, _ = acquired()
    ambiguous = [vehicle(6, 37., 57.), vehicle(9, 43., 63.)]
    for now in (.1, .2, .3, 5., 10.1):
        assert observe(lock, ambiguous, now) is None
    assert lock.last_seen == lock.last_strong_seen == 0.
    assert lock.elapsed_since_seen > 10.
    recovered = vehicle(19)
    for index, now in enumerate((20., 20.1, 20.2)):
        result = observe(lock, [recovered], now)
        assert (result == recovered) == (index == 2)
    assert lock.target_id == 19 and lock.last_seen == 20.2
