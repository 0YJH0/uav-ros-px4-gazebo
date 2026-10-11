from types import SimpleNamespace

import numpy as np
import pytest
import torch
from ultralytics.engine.results import Boxes

from uav_learning.perception_node import PerceptionNode
from uav_learning.vehicle_roi_detector import target_view, choose_crop, needs_zoom, merge_boxes
from uav_learning.vehicle_target_lock import VehicleTargetLock


def boxes(rows, shape=(540, 960)):
    return Boxes(np.asarray(rows, np.float32).reshape(-1, 6), shape)


def locked():
    lock = VehicleTargetLock()
    item = (7, 10000, 0.9, 390, 310, 490, 410)
    histogram = np.array([[1.0], [0.0], [0.0]], np.float32)
    lock.select([item], [histogram], 960, 540, 100.0)
    return lock, histogram


def test_crop_is_bounded_and_camera_compensation_does_not_mutate_identity():
    lock, _ = locked()
    previous = lock.last_measurement.copy()
    view = target_view(lock, 960, 540, np.array([[1, 0, 20], [0, 1, -10]]))
    np.testing.assert_allclose(view[:2] * [960, 540], [460, 350])
    assert choose_crop(view, 960, 540) == (300, 190, 620, 510)
    np.testing.assert_array_equal(lock.last_measurement, previous)
    assert lock.last_seen == 100.0
    view[:2] = [0.99, 0.99]
    assert choose_crop(view, 960, 540) == (640, 220, 960, 540)
    view[0] = 1.1
    assert choose_crop(view, 960, 540) is None
    assert target_view(None, 960, 540, None) is None


def test_weak_or_distractor_boxes_do_not_prevent_target_zoom():
    lock, _ = locked()
    view = target_view(lock, 960, 540, None)
    assert needs_zoom(boxes([]), view, 960, 540, 0.25)
    assert needs_zoom(boxes([[390, 310, 490, 410, 0.15, 2]]), view, 960, 540, 0.25)
    assert needs_zoom(boxes([[800, 310, 900, 410, 0.9, 2]]), view, 960, 540, 0.25)
    assert not needs_zoom(boxes([[390, 310, 490, 410, 0.3, 2]]), view, 960, 540, 0.25)


def test_roi_previews_motion_and_warp_without_advancing_identity():
    lock, _ = locked()
    state = lock.filter.statePost.copy()
    state[4, 0], state[5, 0] = 0.1, -0.02
    lock.filter.statePost = state.copy()
    measurement = lock.last_measurement.copy()
    covariance = lock.filter.errorCovPost.copy()
    view = target_view(lock, 960, 540, np.array([[1., 0, 20], [0, 1, -10]]), now=101.0)
    np.testing.assert_allclose(view[:2] * [960, 540], [556, 339.2])
    assert choose_crop(view, 960, 540) == (396, 179, 716, 499)
    np.testing.assert_array_equal(lock.filter.statePost, state)
    np.testing.assert_array_equal(lock.filter.errorCovPost, covariance)
    np.testing.assert_array_equal(lock.last_measurement, measurement)
    assert lock.last_seen == lock.last_predict == 100.0 and lock.pending_count == 0


def test_roi_uses_accumulated_prediction_during_occlusion_not_last_box():
    lock, _ = locked()
    state = lock.filter.statePost.copy()
    state[4, 0] = 0.1
    lock.filter.statePost = state
    lock.select([], [], 960, 540, 102.0)
    view = target_view(lock, 960, 540, None, now=103.0)
    np.testing.assert_allclose(view[0] * 960, 728.)
    assert choose_crop(view, 960, 540)[0] == 568
    old_crop = choose_crop(target_view(lock, 960, 540, None), 960, 540)
    assert old_crop[2] < view[0] * 960
    assert lock.last_seen == 100.0 and lock.last_predict == 102.0


@pytest.mark.parametrize('now', [99., 111., float('nan')])
def test_roi_never_extrapolates_expired_or_invalid_motion(now):
    lock, _ = locked()
    state = lock.filter.statePost.copy()
    state[4, 0] = 0.15
    lock.filter.statePost = state
    np.testing.assert_array_equal(target_view(lock, 960, 540, None, now=now),
                                  lock.last_measurement.reshape(4))


@pytest.mark.parametrize('use_tensor', [False, True])
def test_nms_maps_roi_boxes_to_full_frame_without_dropping_distractors(use_tensor):
    full = boxes([[390, 310, 490, 410, 0.15, 2], [800, 310, 900, 410, 0.9, 2]])
    crop = boxes([[110, 110, 210, 210, 0.3, 2]], (320, 320))
    if use_tensor:
        full, crop = Boxes(torch.as_tensor(full.data), full.orig_shape), Boxes(torch.as_tensor(crop.data), crop.orig_shape)
    merged, sources = merge_boxes(full, crop, (280, 200, 600, 520), (540, 960))
    assert len(merged) == 2 and sources == ['full_frame', 'target_roi']
    np.testing.assert_allclose(merged.xyxy[1].cpu(), [390, 310, 490, 410])
    assert abs(float(merged.conf[1]) - 0.3) < 1e-6


def roi_node():
    calls, updates = [], []
    lock, _ = locked()

    def predict(**kwargs):
        calls.append(kwargs)
        result = boxes([]) if len(calls) % 2 else boxes([[110, 110, 210, 210, 0.3, 2]], (320, 320))
        return [SimpleNamespace(boxes=result)]

    def update(observations, image, camera_motion=None):
        updates.append(observations)
        return np.empty((0, 8), np.float32)

    node = SimpleNamespace(model=SimpleNamespace(predict=predict), class_ids=[2],
                           target_lock=lock, motion_estimator=None,
                           tracker=SimpleNamespace(update=update), settings={
                               'tracking_confidence_threshold': 0.1, 'confidence_threshold': 0.25,
                               'image_size': 960, 'device': 'cpu', 'target_roi_enabled': True,
                               'target_roi_image_size': 640, 'target_roi_full_frame_budget_s': 0.25})
    return node, calls, updates


def test_fallback_updates_tracker_once_and_keeps_unassigned_raw_box():
    node, calls, updates = roi_node()
    result, ids = PerceptionNode.infer_vehicles(node, np.zeros((540, 960, 3), np.uint8))
    assert len(calls) == 2 and len(updates) == 1
    assert calls[1]['source'].shape == (320, 320, 3)
    assert calls[1]['conf'] == 0.1 and node.candidate_sources == ['target_roi']
    assert ids == [None] and len(result) == 1
    np.testing.assert_allclose(result.xyxy[0].cpu(), [390, 310, 490, 410])
    assert node.target_lock.last_seen == 100.0


def test_motion_prediction_centers_zoom_and_masks_missed_target(monkeypatch):
    node, calls, _ = roi_node()
    state = node.target_lock.filter.statePost.copy()
    state[4, 0] = 0.1
    node.target_lock.filter.statePost = state
    masks = []

    def motion(image, exclusions, anchor=None):
        masks.append((exclusions.copy(), anchor.copy()))
        return np.array([[1., 0, 20], [0, 1, -10]])

    node.motion_estimator = SimpleNamespace(apply=motion)
    monkeypatch.setattr('uav_learning.perception_node.time.monotonic', lambda: 101.)
    PerceptionNode.infer_vehicles(node, np.zeros((540, 960, 3), np.uint8))
    np.testing.assert_allclose(masks[0][0], [[486, 310, 586, 410]])
    np.testing.assert_allclose(masks[0][1], [536, 360])
    assert node.detector_diagnostic['roi_bounds'] == [396, 190, 716, 510]
    assert node.detector_diagnostic['predicted_foreground_mask']
    assert len(calls) == 2 and node.target_lock.last_seen == 100.


def test_optional_roi_failure_preserves_full_frame_boxes():
    node, _, updates = roi_node()
    calls = []

    def predict(**kwargs):
        calls.append(kwargs)
        if len(calls) > 1:
            raise RuntimeError('ROI failed')
        return [SimpleNamespace(boxes=boxes([[800, 310, 900, 410, 0.9, 2]]))]

    node.model.predict = predict
    result, _ = PerceptionNode.infer_vehicles(node, np.zeros((540, 960, 3), np.uint8))
    assert len(result) == 1 and len(updates) == 1
    assert node.detector_diagnostic['roi_reason'] == 'inference_error'
    assert node.candidate_sources == ['full_frame']


def test_tracker_ids_follow_merged_detection_indices_not_source_order():
    node, _, _ = roi_node()
    predictions = iter([boxes([[800, 310, 900, 410, 0.9, 2]]),
                        boxes([[110, 110, 210, 210, 0.3, 2]], (320, 320))])
    node.model.predict = lambda **kwargs: [SimpleNamespace(boxes=next(predictions))]
    node.tracker.update = lambda *args, **kwargs: np.array(
        [[390, 310, 490, 410, 19, 0.3, 2, 1]], np.float32)
    _, identities = PerceptionNode.infer_vehicles(node, np.zeros((540, 960, 3), np.uint8))
    assert identities == [None, 19]
    assert node.candidate_sources == ['full_frame', 'target_roi']


def test_roi_cannot_silently_clip_coords_outside_the_original_image():
    merged, sources = merge_boxes(boxes([]), boxes([[-20, -10, 400, 400, 0.3, 2]], (320, 320)),
                                   (640, 220, 960, 540), (540, 960))
    np.testing.assert_allclose(merged.xyxy[0].cpu(), [620, 210, 960, 540])
    assert sources == ['target_roi']


def test_slow_full_frame_pass_skips_roi(monkeypatch):
    node, calls, updates = roi_node()
    clock = [100.0]
    original = node.model.predict

    def predict(**kwargs):
        clock[0] += 0.3
        return original(**kwargs)

    node.model.predict = predict
    monkeypatch.setattr('uav_learning.perception_node.time.monotonic', lambda: clock[0])
    PerceptionNode.infer_vehicles(node, np.zeros((540, 960, 3), np.uint8))
    assert len(calls) == len(updates) == 1
    assert node.detector_diagnostic['roi_reason'] == 'full_frame_budget_exceeded'
    assert abs(node.detector_diagnostic['full_frame_yolo_s'] - 0.3) < 1e-9
    assert node.detector_diagnostic['gmc_s'] == node.detector_diagnostic['bytetrack_s'] == 0


def test_zoom_evidence_requires_three_frames_after_long_occlusion():
    node, _, _ = roi_node()
    _, histogram = locked()
    image = np.zeros((540, 960, 3), np.uint8)
    for count in range(3):
        result, ids = PerceptionNode.infer_vehicles(node, image)
        coords = result.xyxy[0].cpu().tolist()
        item = (ids[0], 10000, float(result.conf[0]), *coords)
        selected = node.target_lock.select([item], [histogram], 960, 540, 120.0 + count * 0.1)
        assert (selected is not None) == (count == 2)
        if count < 2:
            assert node.target_lock.last_seen == 100.0
    assert node.target_lock.target_id == 7


def test_roi_budget_includes_queue_time_and_observed_roi_latency(monkeypatch):
    node, calls, updates = roi_node()
    node.frame_received_at = 99.8
    node.roi_latency_estimate_s = 0.32
    monkeypatch.setattr('uav_learning.perception_node.time.monotonic', lambda: 100.)
    PerceptionNode.infer_vehicles(node, np.zeros((540, 960, 3), np.uint8))
    assert len(calls) == len(updates) == 1
    assert node.detector_diagnostic['roi_reason'] == 'frame_deadline_budget'


def test_temporary_roi_cost_spike_does_not_permanently_disable_zoom(monkeypatch):
    node, _, updates = roi_node()
    node.roi_latency_estimate_s = 0.8
    node.model.predict = lambda **kwargs: [SimpleNamespace(boxes=boxes([]))]
    monkeypatch.setattr('uav_learning.perception_node.time.monotonic', lambda: 100.)
    for _ in range(40):
        PerceptionNode.infer_vehicles(node, np.zeros((540, 960, 3), np.uint8))
    assert len(updates) == 40
    assert node.detector_diagnostic['roi_reason'] == 'completed'
