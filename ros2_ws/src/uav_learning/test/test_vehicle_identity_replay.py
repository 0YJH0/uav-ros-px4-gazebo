import importlib.util
import json
from pathlib import Path

import cv2
import pytest


@pytest.fixture
def replay(monkeypatch):
    scripts = Path(__file__).resolve().parents[4] / 'scripts'
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location('identity_replay', scripts / 'replay_vehicle_identity.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_proxy_preserves_logged_reference_correlation(replay):
    reference = replay.appearance_proxy(1.0)
    assert replay.appearance_proxy(None) is None
    for correlation in (-1.0, -0.5, 0.0, 0.75, 0.95, 1.0):
        assert abs(cv2.compareHist(reference, replay.appearance_proxy(correlation),
                                  cv2.HISTCMP_CORREL) - correlation) < 1e-6


def test_time_proxy_clips_window_and_confirmation_ttl(replay):
    rows = [{'wall_s': t, 'identity_confirmed': True, 'label': label}
            for t, label in [(0., 'tracked_vehicle'), (1.8, 'crossing_vehicle'), (3.9, 'tracked_vehicle')]]
    report = {'transitions': [{'state': 'TRACK', 'time_s': 1.}, {'state': 'RETURN', 'time_s': 4.}]}
    result = replay.time_proxy(rows, report)
    assert result['confirmed_wall_s_proxy'] == pytest.approx(.6)
    assert result['wrong_identity_wall_s_proxy'] == pytest.approx(.5)
    assert result['confirmation_time_fraction_proxy'] == pytest.approx(.2)
    assert replay.time_proxy(rows, {})['confirmation_time_fraction_proxy'] is None


def test_recovery_proxy_uses_first_correct_vehicle_after_last_during_overlap(replay):
    rows = [{'stamp': {'sec': sec, 'nanosec': 0}, 'wall_s': wall, 'phase': phase, 'label': label}
            for sec, wall, phase, label in [(1, 1., 'pre', 'tracked_vehicle'),
                (2, 2., 'during', 'overlap_unscorable'), (3, 4., 'during', 'overlap_unscorable'),
                (4, 6., 'during', 'crossing_vehicle'), (5, 8., 'post', 'tracked_vehicle')]]
    result = replay.recovery_proxy(rows)
    assert result['after_last_overlap_confirmation_sim_s_proxy'] == 2.
    assert result['after_last_overlap_confirmation_wall_s_proxy'] == 4.
    assert replay.recovery_proxy(rows[:3])['after_last_overlap_confirmation_sim_s_proxy'] is None


def test_replay_competition_uses_archived_switch_not_selector_default(replay):
    from uav_learning.vehicle_target_lock import VehicleTargetLock
    assert replay.competition_setting(VehicleTargetLock, {}, 'recorded') == {'recovery_competition_enabled': False}
    assert replay.competition_setting(VehicleTargetLock, {'recovery_competition_enabled': True}, 'recorded') == {
        'recovery_competition_enabled': True}
    assert replay.competition_setting(VehicleTargetLock, {}, 'enabled') == {'recovery_competition_enabled': True}
    assert replay.competition_setting(VehicleTargetLock, {}, 'implementation_default') == {}


def test_replay_cannot_silently_enable_unsupported_competition(replay):
    def legacy(recovery_timeout=10.):
        return None
    assert replay.competition_setting(legacy, {}, 'recorded') == {}
    with pytest.raises(ValueError, match='does not support'):
        replay.competition_setting(legacy, {}, 'enabled')


def test_replay_retains_unstarted_attempt_without_inventing_identity_seed(replay, tmp_path):
    (tmp_path / 'identity_observations.jsonl').write_text('')
    (tmp_path / 'association.jsonl').write_text('')
    result, rows = replay.replay_trial(tmp_path, None)
    assert not result['seed_available'] and result['observations'] == 0 and rows == []


def test_startup_failure_with_missing_streams_remains_in_replay_results(replay, tmp_path):
    result, rows = replay.replay_trial(tmp_path, None)
    assert not result['seed_available'] and rows == []
    assert set(result['missing_input_files']) == {'association.jsonl', 'identity_observations.jsonl'}


def test_replay_does_not_supply_ground_truth_to_association(replay, tmp_path):
    from uav_learning.vehicle_target_lock import VehicleTargetLock
    parameters = {'perception_node': {'target_reacquire_timeout': 10., 'confidence_threshold': .25,
        'weak_idless_confirm_frames': 3, 'weak_idless_max_age': 2., 'min_area_ratio': .0005}}
    stamp = {'sec': 1, 'nanosec': 0}
    candidate = {'bbox': [40, 40, 60, 60], 'track_id': 6, 'confidence': .9, 'accepted': True}
    association = {'stamp': stamp, 'wall_s': 1., 'candidates': [candidate], 'identity_confirmed': True}
    evidence = {'stamp': stamp, 'label': 'tracked_vehicle', 'phase': 'pre',
                'projected_boxes': {'tracked_vehicle': [80, 40, 100, 60],
                                    'crossing_vehicle': candidate['bbox']}}
    (tmp_path / 'runtime_parameters.json').write_text(json.dumps(parameters))
    (tmp_path / 'association.jsonl').write_text(json.dumps(association) + '\n')
    (tmp_path / 'identity_observations.jsonl').write_text(json.dumps(evidence) + '\n')
    result, rows = replay.replay_trial(tmp_path, VehicleTargetLock, width=100, height=100)
    assert result['wrong_identity_observations'] == 1
    assert rows[0]['accepted_box'] == candidate['bbox']
