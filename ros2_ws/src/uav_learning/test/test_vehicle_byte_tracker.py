from types import SimpleNamespace

import numpy as np
import pytest
from ultralytics.engine.results import Boxes

from uav_learning.perception_node import PerceptionNode


def boxes(cx, confidence=0.9):
    return Boxes(np.array([[cx - 20, 80, cx + 20, 120, confidence, 2]],
                          np.float32), (200, 400)).numpy()


@pytest.mark.parametrize('confidence', [0.9, 0.15])
def test_camera_translation_preserves_identity_in_both_matching_stages(confidence):
    image = np.zeros((200, 400, 3), np.uint8)
    tracker = PerceptionNode.create_tracker(0.25)
    identity = tracker.update(boxes(80), image)[0, 4]
    result = tracker.update(boxes(140, confidence), image,
                            camera_motion=np.array([[1, 0, 60], [0, 1, 0]]))
    assert len(result) == 1 and result[0, 4] == identity
    assert tracker.camera_motion_reason == 'applied'
    uncompensated = PerceptionNode.create_tracker(0.25)
    uncompensated.update(boxes(80), image)
    assert len(uncompensated.update(boxes(140, confidence), image)) == 0


def test_camera_translation_registers_lost_and_unconfirmed_tracks():
    image = np.zeros((200, 400, 3), np.uint8)
    warp = np.array([[1, 0, 60], [0, 1, 0]])
    tracker = PerceptionNode.create_tracker(0.25)
    identity = tracker.update(boxes(80), image)[0, 4]
    tracker.update(Boxes(np.empty((0, 6), np.float32), (200, 400)).numpy(), image)
    assert tracker.update(boxes(140), image, camera_motion=warp)[0, 4] == identity
    tentative = PerceptionNode.create_tracker(0.25)
    tentative.update(boxes(80), image)
    assert len(tentative.update(boxes(180), image)) == 0
    pending_id = next(t.track_id for t in tentative.tracked_stracks if not t.is_activated)
    assert tentative.update(boxes(240), image, camera_motion=warp)[0, 4] == pending_id


def test_xyah_compensation_transforms_covariance_without_rotating_aspect_ratio():
    tracker = PerceptionNode.create_tracker(0.25)
    angle, scale = 0.1, 1.05
    linear = scale * np.array([[np.cos(angle), -np.sin(angle)],
                               [np.sin(angle), np.cos(angle)]])
    tracker.camera_motion = np.column_stack((linear, [12, -4]))
    original = np.array([80, 100, 1.5, 40, 2, -3, 0.02, 0.4])
    active = SimpleNamespace(mean=original.copy(), covariance=np.diag(np.arange(1, 9)))
    tentative = SimpleNamespace(mean=original.copy(), covariance=active.covariance.copy())
    tracker._pre_first_associate([active], [tentative], None, None)
    transform = np.eye(8)
    transform[:2, :2] = transform[4:6, 4:6] = linear
    transform[3, 3] = transform[7, 7] = scale
    expected = transform @ original
    expected[:2] += [12, -4]
    for track in (active, tentative):
        assert np.allclose(track.mean, expected)
        assert np.allclose(track.covariance, transform @ np.diag(np.arange(1, 9)) @ transform.T)
        assert track.mean[2] == original[2] and track.mean[6] == original[6]


def test_invalid_camera_motion_is_ignored_without_refreshing_previous_warp():
    image = np.zeros((200, 400, 3), np.uint8)
    tracker = PerceptionNode.create_tracker(0.25)
    identity = tracker.update(boxes(80), image)[0, 4]
    assert tracker.update(boxes(90), image,
                          camera_motion=np.array([[1, 0, 10], [0, 1, 0]]))[0, 4] == identity
    assert tracker.update(boxes(90), image, camera_motion=np.full((2, 3), np.nan))[0, 4] == identity
    assert tracker.camera_motion is None and tracker.camera_motion_reason == 'invalid_warp'
