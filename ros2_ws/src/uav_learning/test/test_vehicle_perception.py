from types import SimpleNamespace
import json

import numpy as np
import pytest
from cv_bridge import CvBridge

from uav_learning.perception_node import PerceptionNode
from uav_learning.vehicle_target_lock import VehicleTargetLock
from uav_learning.px4_offboard_controller import MissionState, PX4OffboardController
from uav_learning.vehicle_scene import (
    VehicleScene, car_sdf, distractor_model_file, street_sdf, occluder_sdf,
)
import xml.etree.ElementTree as ET


class Tensor:
    def __init__(self, values):
        self.values = values

    def cpu(self):
        return self

    def tolist(self):
        return self.values


def detector():
    published = []
    vehicles, associations = [], []
    boxes = SimpleNamespace(
        xyxy=Tensor([[10, 20, 50, 60]]), conf=Tensor([0.9]), id=Tensor([7]))
    node = SimpleNamespace(
        bridge=CvBridge(), target_id=None, target_lock=VehicleTargetLock(),
        motion_estimator=None,
        camera_motion=None,
        appearance=PerceptionNode.appearance,
        last_seen=0.0, last_log=0.0,
        settings={'confidence_threshold': 0.35, 'image_size': 640,
                  'tracking_confidence_threshold': 0.1,
                  'device': 'cpu', 'min_area_ratio': 0.001,
                  'target_reacquire_timeout': 3.0},
        class_ids=[2], model=SimpleNamespace(
            predict=lambda **kwargs: [SimpleNamespace(boxes=boxes)]),
        target_pub=SimpleNamespace(publish=published.append),
        vehicles_pub=SimpleNamespace(publish=vehicles.append),
        association_pub=SimpleNamespace(publish=associations.append),
        vehicle_messages=vehicles, association_messages=associations,
        debug_pub=SimpleNamespace(publish=lambda msg: None),
        get_logger=lambda: SimpleNamespace(error=lambda msg: None,
                                           info=lambda msg: None))
    def infer(image):
        result = node.model.predict(source=image)[0].boxes
        ids = result.id.cpu().tolist() if result.id is not None else [None] * len(result.conf.tolist())
        return result, ids
    node.infer_vehicles = infer
    return node, boxes, published


def test_cpu_thread_setting_is_explicit_and_zero_preserves_default(monkeypatch):
    import sys
    calls = []
    monkeypatch.setitem(sys.modules, 'torch', SimpleNamespace(set_num_threads=calls.append, get_num_threads=lambda: 8))
    node = SimpleNamespace(settings={'device': 'cpu', 'cpu_inference_threads': 4})
    PerceptionNode.configure_cpu_threads(node)
    assert calls == [4] and node.inference_threads_actual == 8
    node.settings['cpu_inference_threads'] = 0
    PerceptionNode.configure_cpu_threads(node)
    assert calls == [4]


def test_callback_reports_debug_and_actual_target_publication_age():
    node, _, published = detector()
    message = node.bridge.cv2_to_imgmsg(np.zeros((100, 100, 3), np.uint8), 'bgr8')
    PerceptionNode.image_callback(node, message)
    row = json.loads(node.association_messages[-1].data)
    assert published and row['target_publish_age_s'] >= row['target_publish_s'] >= 0.
    assert row['debug_render_publish_s'] >= 0.


def test_control_target_is_published_before_debug_and_survives_debug_failure():
    node, _, published = detector()
    def debug_failure(message):
        assert len(published) == 1 and published[0].detected
        raise RuntimeError('debug transport failed')
    node.debug_pub.publish = debug_failure
    message = node.bridge.cv2_to_imgmsg(np.zeros((100, 100, 3), np.uint8), 'bgr8')
    PerceptionNode.image_callback(node, message)
    row = json.loads(node.association_messages[-1].data)
    assert row['identity_confirmed'] and row['debug_publish_error'] == 'debug transport failed'


def test_vehicle_observation_is_separate_from_target_identity():
    node, boxes, published = detector()
    image = node.bridge.cv2_to_imgmsg(np.zeros((100, 100, 3), np.uint8), 'bgr8')
    PerceptionNode.image_callback(node, image)
    boxes.id, boxes.xyxy = Tensor([8]), Tensor([[60, 60, 95, 95]])
    PerceptionNode.image_callback(node, image)
    vehicles = node.vehicle_messages[-1]
    association = json.loads(node.association_messages[-1].data)
    assert len(vehicles.vehicles) == 1 and vehicles.vehicles[0].detection.detected
    assert not published[-1].detected
    assert association['vehicle_detected'] and not association['identity_confirmed']
    assert association['candidates'][0]['rejection_reasons']


def test_late_result_keeps_vehicle_evidence_but_does_not_refresh_identity(monkeypatch):
    import time
    node, _, published = detector()
    image = node.bridge.cv2_to_imgmsg(np.zeros((100, 100, 3), np.uint8), 'bgr8')
    PerceptionNode.image_callback(node, image)
    last_seen = node.target_lock.last_seen
    received_at = time.monotonic() - 0.49
    original = node.infer_vehicles

    def delayed(frame):
        time.sleep(0.03)
        return original(frame)

    node.infer_vehicles = delayed
    PerceptionNode.image_callback(node, image, received_at)
    diagnostic = json.loads(node.association_messages[-1].data)
    assert diagnostic['vehicle_detected'] and not published[-1].detected
    assert diagnostic['reason'] == 'stale_inference_result'
    assert diagnostic['candidates'][0]['reason'] == 'stale_inference_result'
    assert node.target_lock.last_seen == last_seen


def test_duplicate_stamped_frame_and_old_queue_are_not_inferred():
    import time
    node, _, published = detector()
    image = node.bridge.cv2_to_imgmsg(np.zeros((100, 100, 3), np.uint8), 'bgr8')
    image.header.stamp.sec = 1
    PerceptionNode.image_callback(node, image)
    seen = node.target_lock.last_seen
    node.infer_vehicles = lambda image: (_ for _ in ()).throw(AssertionError('must not infer'))
    PerceptionNode.image_callback(node, image)
    assert json.loads(node.association_messages[-1].data)['reason'] == 'out_of_order_frame'
    image.header.stamp.sec = 2
    PerceptionNode.image_callback(node, image, time.monotonic() - 0.6)
    assert json.loads(node.association_messages[-1].data)['reason'] == 'stale_queued_frame'
    assert not published[-1].detected and node.target_lock.last_seen == seen


def test_small_vehicle_is_visible_even_if_below_association_area_gate():
    node, boxes, published = detector()
    boxes.xyxy = Tensor([[10, 10, 12, 12]])
    image = node.bridge.cv2_to_imgmsg(np.zeros((100, 100, 3), np.uint8), 'bgr8')
    PerceptionNode.image_callback(node, image)
    status = json.loads(node.association_messages[-1].data)
    assert status['vehicle_detected'] and not published[-1].detected
    assert status['candidates'][0]['reason'] == 'min_area_gate'


def test_invalid_box_is_recorded_without_becoming_a_vehicle_observation():
    node, boxes, published = detector()
    boxes.xyxy = Tensor([[float('nan'), 10, 20, 20]])
    image = node.bridge.cv2_to_imgmsg(np.zeros((100, 100, 3), np.uint8), 'bgr8')
    PerceptionNode.image_callback(node, image)
    status = json.loads(node.association_messages[-1].data)
    assert not status['vehicle_detected'] and not published[-1].detected
    assert status['candidates'][0]['reason'] == 'invalid_box'


def test_box_conversion_and_identity_lock():
    node, boxes, published = detector()
    image = node.bridge.cv2_to_imgmsg(np.zeros((100, 100, 3), np.uint8), 'bgr8')
    PerceptionNode.image_callback(node, image)
    result = published[-1]
    assert result.detected and node.target_id == 7
    assert abs(result.area_ratio - 0.16) < 1e-6
    assert abs(result.center_u_norm + 0.4) < 1e-6
    # A larger distractor must not replace the locked vehicle.
    boxes.xyxy = Tensor([[10, 20, 50, 60], [0, 0, 90, 90]])
    boxes.conf, boxes.id = Tensor([0.9, 0.95]), Tensor([7, 8])
    PerceptionNode.image_callback(node, image)
    assert node.target_id == 7
    boxes.id = Tensor([8])
    boxes.xyxy, boxes.conf = Tensor([[0, 0, 90, 90]]), Tensor([0.95])
    PerceptionNode.image_callback(node, image)
    assert not published[-1].detected


def test_inference_error_publishes_negative():
    node, _, published = detector()

    def fail(**kwargs):
        raise RuntimeError('inference failed')

    node.model.predict = fail
    image = node.bridge.cv2_to_imgmsg(np.zeros((100, 100, 3), np.uint8), 'bgr8')
    PerceptionNode.image_callback(node, image)
    assert not published[-1].detected
    status = json.loads(node.association_messages[-1].data)
    assert not status['vehicle_detected'] and not status['identity_confirmed']
    assert status['reason'] == 'processing_error'


def test_reassociation_after_ten_seconds_still_keeps_raw_and_confirmed_separate(monkeypatch):
    node, boxes, published = detector()
    pixels = np.zeros((100, 100, 3), np.uint8)
    pixels[20:60, 10:50, 2] = 255
    image = node.bridge.cv2_to_imgmsg(pixels, 'bgr8')
    clock = [100.0]
    monkeypatch.setattr('uav_learning.perception_node.time.monotonic', lambda: clock[0])
    PerceptionNode.image_callback(node, image)
    boxes.id = Tensor([19])
    for count in range(3):
        clock[0] = 120.0 + count * 0.1
        PerceptionNode.image_callback(node, image)
        status = json.loads(node.association_messages[-1].data)
        assert status['vehicle_detected']
        assert status['identity_confirmed'] == (count == 2)
    assert published[-1].detected and node.target_id == 19


def test_weak_idless_publishes_raw_vehicle_before_confirmed_target(monkeypatch):
    node, boxes, published = detector()
    pixels = np.zeros((100, 100, 3), np.uint8)
    pixels[20:60, 10:50, 2] = 255
    image = node.bridge.cv2_to_imgmsg(pixels, 'bgr8')
    clock = [100.0]
    monkeypatch.setattr('uav_learning.perception_node.time.monotonic', lambda: clock[0])
    PerceptionNode.image_callback(node, image)
    boxes.id, boxes.conf = None, Tensor([0.15])
    for index in range(4):
        clock[0] += 0.1
        PerceptionNode.image_callback(node, image)
        status = json.loads(node.association_messages[-1].data)
        assert status['vehicle_detected'] and status['tracked_vehicle_count'] == 0
        assert status['identity_confirmed'] == (index >= 2)
        assert published[-1].detected == (index >= 2)
        assert status['candidates'][0]['confirmation_required'] == 3
    assert node.target_id == 7


def test_camera_motion_is_estimated_once_and_shared_with_bytetrack():
    from ultralytics.engine.results import Boxes
    image = np.zeros((100, 100, 3), np.uint8)
    calls = []
    warp = np.array([[1, 0, 5], [0, 1, 0]])
    def estimate(frame, detections=None, anchor=None):
        calls.append(frame)
        return warp
    node = SimpleNamespace(
        model=SimpleNamespace(predict=lambda **kwargs: [SimpleNamespace(
            boxes=Boxes(np.array([[30, 30, 70, 70, 0.9, 2]], np.float32), (100, 100)))]),
        tracker=PerceptionNode.create_tracker(0.25), class_ids=[2],
        settings={'tracking_confidence_threshold': 0.1, 'image_size': 640, 'device': 'cpu'},
        motion_estimator=SimpleNamespace(apply=estimate))
    PerceptionNode.infer_vehicles(node, image)
    assert len(calls) == 1 and node.camera_motion is warp
    assert np.array_equal(node.tracker.camera_motion, warp)


def test_overlapping_reassigned_id_is_recovered():
    node, boxes, published = detector()
    image = node.bridge.cv2_to_imgmsg(np.zeros((100, 100, 3), np.uint8), 'bgr8')
    PerceptionNode.image_callback(node, image)
    boxes.id = Tensor([9])
    boxes.xyxy = Tensor([[11, 20, 51, 60]])
    PerceptionNode.image_callback(node, image)
    assert node.target_id == 9 and published[-1].detected


def test_long_loss_does_not_acquire_another_vehicle():
    node, boxes, published = detector()
    image = node.bridge.cv2_to_imgmsg(np.zeros((100, 100, 3), np.uint8), 'bgr8')
    PerceptionNode.image_callback(node, image)
    node.target_lock.last_seen = 0.0
    boxes.id = Tensor([8])
    boxes.xyxy = Tensor([[60, 60, 95, 95]])
    PerceptionNode.image_callback(node, image)
    assert node.target_id == 7 and not published[-1].detected


def test_vehicle_keeps_moving_during_search():
    node = SimpleNamespace(moving=False)
    VehicleScene.state_callback(node, SimpleNamespace(data='TAKEOFF'))
    assert not node.moving
    VehicleScene.state_callback(node, SimpleNamespace(data='TRACK'))
    VehicleScene.state_callback(node, SimpleNamespace(data='SEARCH'))
    assert node.moving


def test_occluder_is_rendered_without_collision():
    root = ET.fromstring(occluder_sdf())
    assert root.find('.//visual') is not None
    assert root.find('.//collision') is None


def test_initial_airborne_acquisition_does_not_release_tracking_lock():
    node = SimpleNamespace(tracking_started=False, target_id=7,
                           airborne_search_initialized=False,
                           target_lock=VehicleTargetLock(),
                           settings={'target_reacquire_timeout': 10.0,
                                     'confidence_threshold': 0.25,
                                     'weak_idless_confirm_frames': 3,
                                     'weak_idless_max_age': 2.0,
                                     'acquisition_center_gate': 1.0,
                                     'acquisition_confirm_frames': 1})
    ground_lock = node.target_lock
    ground_lock.reference = np.ones((18, 8), dtype=np.float32)
    PerceptionNode.state_callback(node, SimpleNamespace(data='SEARCH'))
    assert node.target_id is None and node.target_lock.reference is None
    assert node.target_lock is not ground_lock
    node.target_id = 9
    airborne_reference = np.full((18, 8), 2., dtype=np.float32)
    node.target_lock.reference = airborne_reference
    # Loss during APPROACH must preserve the airborne target, even before TRACK.
    PerceptionNode.state_callback(node, SimpleNamespace(data='SEARCH'))
    assert node.target_id == 9
    assert node.target_lock.reference is airborne_reference
    PerceptionNode.state_callback(node, SimpleNamespace(data='TRACK'))
    PerceptionNode.state_callback(node, SimpleNamespace(data='SEARCH'))
    assert node.target_id == 9
    assert node.target_lock.reference is airborne_reference


def test_bytetrack_keeps_low_score_matches_and_exposes_tentative_raw_boxes():
    from ultralytics.engine.results import Boxes
    image = np.zeros((100, 100, 3), np.uint8)
    current = [Boxes(np.array([[30, 30, 70, 70, 0.9, 2]], np.float32), image.shape[:2])]
    settings = {'tracking_confidence_threshold': 0.1, 'image_size': 640, 'device': 'cpu'}
    node = SimpleNamespace(
        model=SimpleNamespace(predict=lambda **kwargs: [SimpleNamespace(boxes=current[0])]),
        tracker=PerceptionNode.create_tracker(0.25), class_ids=[2], settings=settings,
        motion_estimator=None)
    boxes, ids = PerceptionNode.infer_vehicles(node, image)
    identity = ids[0]
    assert identity is not None
    current[0] = Boxes(np.array([[30, 30, 70, 70, 0.15, 2]], np.float32), image.shape[:2])
    boxes, ids = PerceptionNode.infer_vehicles(node, image)
    assert ids == [identity] and abs(boxes.conf[0].item() - 0.15) < 1e-6
    current[0] = Boxes(np.array([[75, 75, 95, 95, 0.9, 2]], np.float32), image.shape[:2])
    boxes, ids = PerceptionNode.infer_vehicles(node, image)
    assert len(boxes) == 1 and ids == [None]
    _, ids = PerceptionNode.infer_vehicles(node, image)
    assert ids[0] is not None and ids[0] != identity
    current[0] = Boxes(np.empty((0, 6), np.float32), image.shape[:2])
    boxes, ids = PerceptionNode.infer_vehicles(node, image)
    assert len(boxes) == 0 and ids == []


def test_low_confidence_cannot_initialize_or_reacquire_target():
    lock = VehicleTargetLock()
    strong = (7, 1600, 0.9, 30, 30, 70, 70)
    weak = (7, 1600, 0.15, 30, 30, 70, 70)
    histogram = np.zeros((18, 8), np.float32)
    histogram[0, 7] = 1
    assert lock.select([weak], [histogram], 100, 100, 0.0) is None
    assert lock.diagnostics[0]['reason'] == 'confidence_gate'
    assert lock.select([strong], [histogram], 100, 100, 0.1) is not None
    assert lock.select([weak], [histogram], 100, 100, 0.2) is not None
    assert lock.diagnostics[0]['low_confidence_continuation']
    assert lock.select([weak], [histogram], 100, 100, 20.0) is None
    assert 'confidence_gate' in lock.diagnostics[0]['rejection_reasons']


def test_unassigned_weak_detection_without_appearance_does_not_drive_continuation():
    lock = VehicleTargetLock()
    strong = (7, 1600, 0.9, 30, 30, 70, 70)
    weak = (None, 1600, 0.15, 30, 30, 70, 70)
    assert lock.select([strong], [None], 100, 100, 0.0) is not None
    assert lock.select([weak], [None], 100, 100, 0.1) is None
    assert lock.diagnostics[0]['reason'] == 'weak_idless_appearance_missing'


def test_weak_idless_requires_three_frames_and_cannot_renew_strong_anchor():
    lock = VehicleTargetLock()
    strong = (7, 1600, 0.9, 30, 30, 70, 70)
    weak = (None, 1600, 0.15, 30, 30, 70, 70)
    appearance = np.array([[1.0], [0.0], [0.0]], np.float32)
    assert lock.select([strong], [appearance], 100, 100, 0.0)
    for index in range(4):
        selected = lock.select([weak], [appearance], 100, 100, 0.1 + index * 0.1)
        assert (selected is not None) == (index >= 2)
        assert lock.diagnostics[0]['confirmation_required'] == 3
    assert lock.target_id == 7 and lock.last_strong_seen == 0.0
    for now in np.arange(0.5, 2.0, 0.1):
        assert lock.select([weak], [appearance], 100, 100, float(now))
    assert lock.select([weak], [appearance], 100, 100, 2.01) is None
    assert lock.diagnostics[0]['reason'] == 'weak_idless_anchor_expired'


def test_weak_idless_missing_frame_or_ambiguity_restarts_confirmation():
    appearance = np.array([[1.0], [0.0], [0.0]], np.float32)
    lock = VehicleTargetLock()
    strong = (7, 1600, 0.9, 30, 30, 70, 70)
    weak = (None, 1600, 0.15, 30, 30, 70, 70)
    lock.select([strong], [appearance], 100, 100, 0)
    for now in (0.1, 0.2):
        assert lock.select([weak], [appearance], 100, 100, now) is None
    assert lock.select([weak, weak], [appearance, appearance], 100, 100, 0.3) is None
    assert lock.reason == 'ambiguous_candidates' and lock.pending_count == 0
    lock.select([weak], [appearance], 100, 100, 0.4)
    lock.select([], [], 100, 100, 0.5)
    for index in range(3):
        result = lock.select([weak], [appearance], 100, 100, 0.6 + index * 0.1)
        assert (result is not None) == (index == 2)


def test_weak_idless_does_not_borrow_strong_confirmation_or_loosen_gates():
    appearance = np.array([[1.0], [0.0], [0.0]], np.float32)
    lock = VehicleTargetLock()
    strong = (7, 1600, 0.9, 30, 30, 70, 70)
    weak = (None, 1600, 0.15, 30, 30, 70, 70)
    assert lock.select([weak], [appearance], 100, 100, 0) is None
    assert lock.reason != 'confirmed'
    lock.select([strong], [appearance], 100, 100, 0.1)
    shifted_strong = (9, 1600, 0.9, 30, 30, 70, 70)
    assert lock.select([shifted_strong], [appearance], 100, 100, 1.0) is None
    assert lock.pending_count == 1
    assert lock.select([weak], [appearance], 100, 100, 1.1) is None
    assert lock.pending_count == 1 and lock.pending_evidence == 'weak_idless'
    shifted_weak = (None, 1600, 0.15, 35, 30, 75, 70)
    assert lock.select([shifted_weak], [appearance], 100, 100, 1.2) is None
    assert 'center_gate' in lock.diagnostics[0]['rejection_reasons']
    assert lock.diagnostics[0]['center_gate'] == 0.03
    wrong = np.array([[0.0], [1.0], [0.0]], np.float32)
    assert lock.select([weak], [wrong], 100, 100, 1.3) is None
    assert 'appearance_gate' in lock.diagnostics[0]['rejection_reasons']
    assert lock.diagnostics[0]['appearance_gate'] == 0.95
    assert lock.select([weak], [appearance], 100, 100, 20) is None
    assert 'weak_idless_anchor_expired' in lock.diagnostics[0]['rejection_reasons']


def test_camera_translation_prevents_false_loss_without_bypassing_identity_gates():
    lock = VehicleTargetLock()
    histogram = np.zeros((18, 8), np.float32)
    histogram[0, 7] = 1
    first = (7, 1600, 0.9, 30, 30, 70, 70)
    moved = (7, 1600, 0.9, 30, 40, 70, 80)
    distractor = (9, 1000, 0.9, 75, 40, 100, 80)
    assert lock.select([first], [histogram], 100, 100, 0.0) is not None
    warp = np.array([[1, 0, 0], [0, 1, 10]], dtype=float)
    assert lock.select([moved, distractor], [histogram, histogram], 100, 100,
                       0.1, camera_motion=warp) == moved
    assert lock.diagnostics[0]['center_error'] < 1e-6
    assert lock.diagnostics[1]['reason'] == 'center_gate'
    assert lock.camera_motion_reason == 'applied'


def test_camera_motion_aligns_pending_frames_but_cannot_refresh_lock_timeout():
    lock = VehicleTargetLock()
    first = (7, 400, 0.9, 40, 40, 60, 60)
    histogram = np.zeros((18, 8), np.float32)
    histogram[0, 7] = 1
    lock.select([first], [histogram], 100, 100, 0.0)
    warp = np.array([[1, 0, 0], [0, 1, 6]], dtype=float)
    for index in range(3):
        moved = (19, 400, 0.9, 40, 46 + index * 6, 60, 66 + index * 6)
        selected = lock.select([moved], [histogram], 100, 100, 20 + index * 0.1,
                               camera_motion=warp)
        assert (selected is not None) == (index == 2)
        if index < 2:
            assert lock.last_seen == 0.0 and lock.mode == 'reacquiring'
    assert lock.target_id == 19


def test_old_tracker_id_cannot_skip_identity_confirmation_after_occlusion():
    lock = VehicleTargetLock()
    item = (7, 400, 0.9, 40, 40, 60, 60)
    histogram = np.array([[1.0], [0.0], [0.0]], np.float32)
    lock.select([item], [histogram], 100, 100, 0.0)
    for count in range(3):
        selected = lock.select([item], [histogram], 100, 100, 2.0 + count * 0.1)
        assert (selected is not None) == (count == 2)
        assert lock.diagnostics[0]['confirmation_required'] == 3
        if count < 2:
            assert lock.last_seen == 0.0


def test_recovery_rejects_missing_appearance_even_if_tracker_id_matches():
    lock = VehicleTargetLock()
    item = (7, 400, 0.9, 40, 40, 60, 60)
    histogram = np.array([[1.0], [0.0], [0.0]], np.float32)
    lock.select([item], [histogram], 100, 100, 0.0)
    assert lock.select([item], [None], 100, 100, 2.0) is None
    assert 'recovery_appearance_missing' in lock.diagnostics[0]['rejection_reasons']


def test_brief_same_id_dropout_does_not_repeat_occlusion_confirmation():
    lock = VehicleTargetLock()
    item = (7, 400, 0.9, 40, 40, 60, 60)
    histogram = np.array([[1.0], [0.0], [0.0]], np.float32)
    lock.select([item], [histogram], 100, 100, 0.0)
    lock.select([], [], 100, 100, 0.8)
    assert lock.select([item], [histogram], 100, 100, 1.0) == item
    assert lock.pending_count == 0


def test_invalid_or_extreme_camera_warps_are_not_applied():
    lock = VehicleTargetLock()
    first = (7, 400, 0.9, 40, 40, 60, 60)
    lock.select([first], [None], 100, 100, 0.0)
    measurement = lock.last_measurement.copy()
    for warp in (np.full((2, 3), np.nan), np.eye(3),
                 np.array([[1, 0, 90], [0, 1, 0]]),
                 np.array([[-1, 0, 0], [0, 1, 0]])):
        lock.compensate_camera_motion(warp, 100, 100)
        assert lock.camera_motion_reason in ('invalid_warp', 'warp_bounds')
        np.testing.assert_array_equal(lock.last_measurement, measurement)


def test_real_gmc_estimates_previous_to_current_view_translation():
    import cv2
    estimator = PerceptionNode.create_motion_estimator()
    image = np.random.default_rng(7).integers(0, 256, (200, 300, 3), dtype=np.uint8)
    estimator.apply(image)
    shifted = cv2.warpAffine(image, np.array([[1, 0, 4], [0, 1, 10]], np.float32), (300, 200))
    warp = estimator.apply(shifted)
    np.testing.assert_allclose(warp[:, 2], [4, 10], atol=1)


def test_recovery_deadline_returns_home():
    events, transitions = [], []
    node = SimpleNamespace(
        timer_tick=0, tracking_deadline=10.0, now_s=lambda: 11.0,
        state=MissionState.SEARCH, home_x=0, home_y=0,
        takeoff_z=-3, home_yaw=0, set_target=lambda *args, **kwargs: None,
        publish_mission_event=events.append, transition_to=transitions.append)
    PX4OffboardController.timer_callback(node)
    assert events == ['TRACK_RECOVERY_TIMEOUT']
    assert transitions == [MissionState.RETURN]


def test_controller_initializes_without_sending_commands():
    import rclpy
    rclpy.init()
    node = None
    try:
        node = PX4OffboardController()
        assert node.state == MissionState.WAIT_FOR_PX4
        assert node.tracking_deadline is None
    finally:
        if node is not None:
            node.destroy_node()
        rclpy.shutdown()


def test_tracking_loss_enters_recovery_without_counting_track_time():
    calls = []
    node = SimpleNamespace(
        timer_tick=0, state=MissionState.TRACK, tracking_elapsed=0.0,
        TIMER_PERIOD=0.1, approach_target_lost_timeout=0.8,
        get_parameter=lambda name: SimpleNamespace(value=90.0),
        target_currently_visible=lambda: False,
        handle_follow_gap=lambda: calls.append('recover') or True,
        publish_offboard_stream=lambda: None)
    PX4OffboardController.timer_callback(node)
    assert calls == ['recover']
    assert node.tracking_elapsed == 0.0


def test_scene_mesh_paths_resolve():
    from ament_index_python.packages import get_package_share_directory
    from pathlib import Path
    model = (Path(get_package_share_directory('uav_learning'))
             / 'config/models/tracking_car/model.sdf')
    root = ET.fromstring(car_sdf(model, 'test_car', 16, 0))
    assert all(Path(uri.text).is_file() for uri in root.iter('uri'))
    assert len(ET.fromstring(street_sdf()).findall('.//collision')) == 21


@pytest.mark.parametrize('scenario,color,model_name', [
    ('crossing', 'auto', 'tracking_car'),
    ('overtaking', 'auto', 'tracking_car_blue'),
    ('crossing', 'red', 'tracking_car'),
    ('overtaking', 'red', 'tracking_car'),
    ('crossing', 'blue', 'tracking_car_blue'),
    ('overtaking', 'blue', 'tracking_car_blue'),
])
def test_distractor_model_color_selection_preserves_scenario_defaults(scenario, color, model_name):
    from pathlib import Path
    model = Path(__file__).resolve().parents[1] / 'config/models/tracking_car/model.sdf'
    selected = distractor_model_file(model, scenario, color)
    assert selected == model.parent.parent / model_name / 'model.sdf'
    assert selected.is_file()


def test_distractor_model_default_and_invalid_color():
    from pathlib import Path
    model = Path(__file__).resolve().parents[1] / 'config/models/tracking_car/model.sdf'
    assert distractor_model_file(model) == model
    with pytest.raises(ValueError):
        distractor_model_file(model, 'overtaking', 'green')


def test_overtaking_color_changes_rendering_not_collision_geometry():
    from pathlib import Path
    model = Path(__file__).resolve().parents[1] / 'config/models/tracking_car/model.sdf'
    original = ET.fromstring(car_sdf(model, 'target', 16, 0))
    blue_model = model.parent.parent / 'tracking_car_blue/model.sdf'
    blue = ET.fromstring(car_sdf(blue_model, 'distractor', 16, 4))
    assert original.find('.//visual/material') is None
    assert all(Path(uri.text).is_file() for uri in blue.iter('uri'))
    def geometry(path):
        return [line for line in path.read_text().splitlines() if line.startswith(('v ', 'vt ', 'vn ', 'f '))]
    assert geometry(model.parent / 'meshes/hatchback.obj') == geometry(
        blue_model.parent / 'meshes/hatchback_blue.obj')
    assert model.parent.joinpath('materials/textures/hatchback.png').read_bytes() != blue_model.parent.joinpath(
        'materials/textures/hatchback_blue.png').read_bytes()
    material = blue_model.parent.joinpath('meshes/hatchback_blue.mtl').read_text()
    assert 'https://' not in material
    for line in material.splitlines():
        if line.strip().startswith(('map_Kd ', 'map_Ka ')):
            assert (blue_model.parent / 'meshes' / line.split(maxsplit=1)[1]).resolve().is_file()
    assert 'newmtl HatchbackBlue' in material
    for field in ('pose', 'geometry/mesh/scale'):
        assert original.findtext('.//collision/' + field) == blue.findtext('.//collision/' + field)
    road = ET.fromstring(street_sdf(overtaking=True)).find('.//visual[@name="road"]')
    assert road.findtext('geometry/box/size') == '280 12 0.03'
