#!/usr/bin/env python3
"""YOLO vehicle detection with a persistent ByteTrack target identity."""

import json
import math
import time
from threading import Thread

import cv2
from cv_bridge import CvBridge
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String
from uav_interfaces.msg import TargetDetection, VehicleDetections, VehicleObservation
from uav_learning.vehicle_target_lock import VehicleTargetLock
from uav_learning.vehicle_roi_detector import target_view, choose_crop, needs_zoom, merge_boxes
from uav_learning.vehicle_frame_buffer import LatestFrameBuffer


class PerceptionNode(Node):
    def __init__(self):
        super().__init__('perception_node')
        defaults = {
            'image_topic': '/camera/image_raw',
            'model_path': 'yolo11s.pt',
            'target_class': 'car',
            'confidence_threshold': 0.25,
            'tracking_confidence_threshold': 0.1,
            'image_size': 960,
            'device': 'cpu',
            'cpu_inference_threads': 0,
            'detector_backend': 'torch',
            'backend_artifacts': '',
            'min_area_ratio': 0.0005,
            'target_reacquire_timeout': 10.0,
            'acquisition_center_gate': 1.0,
            'acquisition_confirm_frames': 1,
            'camera_motion_compensation': True,
            'weak_idless_confirm_frames': 3,
            'weak_idless_max_age': 2.0,
            'recovery_competition_enabled': False,
            'predict_box_scale_velocity': True,
            'overlap_candidate_recovery': True,
            'bounded_scale_prediction': True,
            'overlap_confirmation_continuity': True,
            'target_roi_enabled': True,
            'target_roi_image_size': 640,
            'target_roi_full_frame_budget_s': 0.25,
            'max_frame_age_s': 0.5,
        }
        for name, value in defaults.items():
            self.declare_parameter(name, value)
        self.settings = {
            name: self.get_parameter(name).value for name in defaults
        }
        if not 0.0 < self.settings['confidence_threshold'] <= 1.0:
            raise ValueError('confidence_threshold must be in (0, 1]')
        if not 0.0 < self.settings['tracking_confidence_threshold'] <= self.settings['confidence_threshold']:
            raise ValueError('tracking_confidence_threshold must be in (0, confidence_threshold]')
        if not 0.0 <= self.settings['min_area_ratio'] <= 1.0:
            raise ValueError('min_area_ratio must be in [0, 1]')
        if self.settings['target_reacquire_timeout'] <= 0:
            raise ValueError('target_reacquire_timeout must be positive')
        if not 0 <= self.settings['cpu_inference_threads'] <= 32:
            raise ValueError('cpu_inference_threads must be in [0, 32]; zero preserves backend defaults')
        if not 0 < self.settings['max_frame_age_s'] <= 0.5:
            raise ValueError('max_frame_age_s must be in (0, 0.5]')
        if not 0 < self.settings['acquisition_center_gate'] <= 1:
            raise ValueError('acquisition_center_gate must be in (0, 1]')
        if self.settings['acquisition_confirm_frames'] < 1:
            raise ValueError('acquisition_confirm_frames must be >= 1')
        if self.settings['weak_idless_confirm_frames'] < 3:
            raise ValueError('weak_idless_confirm_frames must be >= 3')
        if self.settings['target_roi_image_size'] < 320:
            raise ValueError('target_roi_image_size must be >= 320')
        if not 0 < self.settings['target_roi_full_frame_budget_s'] <= 0.3:
            raise ValueError('target_roi_full_frame_budget_s must be in (0, 0.3]')
        if not 0 < self.settings['weak_idless_max_age'] <= self.settings['target_reacquire_timeout']:
            raise ValueError('weak_idless_max_age must be in (0, target_reacquire_timeout]')
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                'Install requirements-yolo.txt in a ROS-compatible venv.'
            ) from exc
        if self.settings['detector_backend'] == 'torch':
            self.model = YOLO(self.settings['model_path'], task='detect')
        elif self.settings['detector_backend'] == 'openvino':
            from uav_learning.vehicle_detector_backend import OpenVINOVehicleDetector
            self.model = OpenVINOVehicleDetector(self.settings['backend_artifacts'], self.settings['model_path'],
                                                 self.settings['cpu_inference_threads'] or 8)
        else:
            raise ValueError('detector_backend must be torch or openvino')
        self.tracker = self.create_tracker(self.settings['confidence_threshold'])
        self.motion_estimator = self.create_motion_estimator() if self.settings['camera_motion_compensation'] else None
        self.camera_motion = None
        self.class_ids = [
            key for key, name in self.model.names.items()
            if name == self.settings['target_class']
        ]
        if not self.class_ids:
            raise ValueError(
                f"Unknown target_class: {self.settings['target_class']}; "
                f'available classes: {self.model.names}')
        self.bridge = CvBridge()
        self.target_id = None
        self.target_lock = VehicleTargetLock(
            self.settings['target_reacquire_timeout'],
            self.settings['acquisition_center_gate'],
            self.settings['acquisition_confirm_frames'],
            self.settings['confidence_threshold'],
            self.settings['weak_idless_confirm_frames'],
            self.settings['weak_idless_max_age'],
            recovery_competition_enabled=self.settings['recovery_competition_enabled'],
            predict_box_scale_velocity=self.settings['predict_box_scale_velocity'],
            overlap_candidate_recovery=self.settings['overlap_candidate_recovery'],
            bounded_scale_prediction=self.settings['bounded_scale_prediction'],
            overlap_confirmation_continuity=self.settings['overlap_confirmation_continuity'])
        self.tracking_started = False
        self.airborne_search_initialized = False
        self.last_log = 0.0
        self.frame_buffer = LatestFrameBuffer()
        self.frame_worker = None
        self.reset_requested = False
        self.last_frame_stamp = None
        self.target_pub = self.create_publisher(
            TargetDetection, '/perception/target', 1)
        self.vehicles_pub = self.create_publisher(
            VehicleDetections, '/perception/vehicles', 10)
        self.association_pub = self.create_publisher(
            String, '/perception/association', 10)
        self.debug_pub = self.create_publisher(
            Image, '/perception/debug_image', qos_profile_sensor_data)
        self.image_sub = self.create_subscription(
            Image, self.settings['image_topic'], self.enqueue_image,
            QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT))
        self.create_subscription(String, '/mission/state', self.state_callback, 10)
        self.get_logger().info(
            f"YOLO tracking {self.settings['target_class']} "
            f"with {self.settings['model_path']} on {self.settings['device']}")

    def enqueue_image(self, msg):
        self.frame_buffer.put(msg, time.monotonic())

    def start_worker(self):
        import numpy as np
        # Initialize/fuse the backend before airborne frames arrive. Warmup is
        # never sent to ByteTrack or identity association.
        for size, shape in [(self.settings['image_size'], (540, 960)),
                            (self.settings['target_roi_image_size'], (320, 320))]:
            self.model.predict(source=np.zeros((*shape, 3), np.uint8),
                               classes=self.class_ids, conf=self.settings['tracking_confidence_threshold'],
                               imgsz=size, device=self.settings['device'], verbose=False)
            # Ultralytics selects its CPU thread count during the first predict.
            PerceptionNode.configure_cpu_threads(self)
        if self.settings['target_roi_enabled']:
            PerceptionNode.warmup_roi_merge()
        self.frame_worker = Thread(target=self.process_latest_frames, name='vehicle-inference')
        self.frame_worker.start()

    @staticmethod
    def warmup_roi_merge():
        import torch
        from torchvision.ops import batched_nms
        # Exercise the optional merge operator before any deadline-bound frame.
        batched_nms(torch.tensor([[0., 0., 20., 20.], [1., 1., 19., 19.]]),
                    torch.tensor([.9, .8]), torch.zeros(2), .7)

    def configure_cpu_threads(self):
        import torch
        requested = self.settings.get('cpu_inference_threads', 0)
        if self.settings['device'] == 'cpu' and requested:
            torch.set_num_threads(requested)
        self.inference_threads_actual = torch.get_num_threads()

    def process_latest_frames(self):
        while True:
            frame = self.frame_buffer.take()
            if frame is None:
                return
            if self.reset_requested:
                self.reset_requested = False
                PerceptionNode.reset_airborne_identity(self)
            self.image_callback(*frame)

    def destroy_node(self):
        self.frame_buffer.close()
        if self.frame_worker is not None:
            self.frame_worker.join()
        return super().destroy_node()

    def image_callback(self, msg, received_at=None):
        started = time.monotonic()
        received_at = started if received_at is None else received_at
        queue_wait_s = started - received_at
        self.frame_received_at = received_at
        detection = TargetDetection()
        detection.stamp = msg.header.stamp
        vehicles = VehicleDetections()
        vehicles.stamp = msg.header.stamp
        debug_payload = None
        diagnostic = {'stamp': {'sec': msg.header.stamp.sec,
                                'nanosec': msg.header.stamp.nanosec},
                      'vehicle_detected': False, 'identity_confirmed': False,
                      'locked_track_id': self.target_id, 'mode': 'error',
                      'reason': 'processing_error', 'candidates': []}
        try:
            stamp = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
            if (stamp > 0 and getattr(self, 'last_frame_stamp', None) is not None
                    and stamp <= self.last_frame_stamp):
                diagnostic['reason'] = 'out_of_order_frame'
                raise ValueError('out_of_order_frame')
            if stamp > 0:
                self.last_frame_stamp = stamp
            if queue_wait_s > self.settings.get('max_frame_age_s', 0.5):
                diagnostic['reason'] = 'stale_queued_frame'
                raise ValueError('stale_queued_frame')
            image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            conversion_s = time.monotonic() - started
            height, width = image.shape[:2]
            diagnostic['image_shape'] = [height, width]
            boxes, ids = self.infer_vehicles(image)
            warp = self.camera_motion
            now = time.monotonic()
            candidates = []
            candidate_indices = []
            if boxes is not None:
                rows = zip(
                    boxes.xyxy.cpu().tolist(), boxes.conf.cpu().tolist(),
                    ids)
                for index, (coords, confidence, track_id) in enumerate(rows):
                    track_id = None if track_id is None else int(track_id)
                    entry = {'index': index, 'track_id': track_id,
                             'byte_track_confirmed': track_id is not None,
                             'confidence': float(confidence), 'bbox': coords,
                             'accepted': False, 'reason': 'invalid_box',
                             'rejection_reasons': ['invalid_box']}
                    sources = getattr(self, 'candidate_sources', [])
                    entry['detector_source'] = sources[index] if index < len(sources) else 'full_frame'
                    diagnostic['candidates'].append(entry)
                    if not all(math.isfinite(value) for value in [*coords, confidence]):
                        entry['bbox'] = [value if math.isfinite(value) else None for value in coords]
                        entry['confidence'] = confidence if math.isfinite(confidence) else None
                        continue
                    x1, y1, x2, y2 = coords
                    x1, x2 = max(0.0, x1), min(float(width), x2)
                    y1, y2 = max(0.0, y1), min(float(height), y2)
                    area = max(0.0, x2 - x1) * max(0.0, y2 - y1)
                    if area <= 0:
                        continue
                    item = (track_id, area, confidence, x1, y1, x2, y2)
                    entry['bbox'] = list(item[3:])
                    observation = VehicleObservation()
                    observation.track_id = -1 if track_id is None else track_id
                    observation.detection = PerceptionNode.to_detection(
                        item, msg.header.stamp, width, height)
                    vehicles.vehicles.append(observation)
                    if area / (width * height) >= self.settings['min_area_ratio']:
                        candidates.append(item)
                        candidate_indices.append(index)
                    else:
                        entry.update(reason='min_area_gate', rejection_reasons=['min_area_gate'],
                                     area_ratio=area / (width * height),
                                     area_gate=self.settings['min_area_ratio'])
            # Extract appearance before annotations can contaminate the crop.
            appearance_started = time.monotonic()
            histograms = [self.appearance(image, item[3:]) for item in candidates]
            appearance_s = time.monotonic() - appearance_started
            association_started = time.monotonic()
            now = association_started
            stale = now - received_at > self.settings.get('max_frame_age_s', 0.5)
            selected = self.target_lock.select([] if stale else candidates, [] if stale else histograms,
                                               width, height, now,
                                               camera_motion=warp)
            association_s = time.monotonic() - association_started
            self.target_id = self.target_lock.target_id
            for index, candidate_diagnostic in zip(candidate_indices, self.target_lock.diagnostics):
                diagnostic['candidates'][index].update(candidate_diagnostic)
            if stale:
                for index in candidate_indices:
                    diagnostic['candidates'][index].update(
                        reason='stale_inference_result', rejection_reasons=['stale_inference_result'])
            diagnostic.update(locked_track_id=self.target_id, mode=self.target_lock.mode,
                              image_conversion_s=conversion_s, appearance_s=appearance_s,
                              identity_association_s=association_s,
                              identity_guard={'active': self.target_lock.overlap_guard_active,
                                              'reason': self.target_lock.overlap_guard_reason},
                              recovery_competition=self.target_lock.competition_diagnostic,
                              detector=getattr(self, 'detector_diagnostic', {}),
                              cpu_inference_threads_actual=getattr(self, 'inference_threads_actual', None),
                              detector_backend=self.settings.get('detector_backend', 'torch'),
                              reason='stale_inference_result' if stale else self.target_lock.reason,
                              camera_motion={'reason': self.target_lock.camera_motion_reason,
                                             'bytetrack_reason': getattr(
                                                 getattr(self, 'tracker', None), 'camera_motion_reason', 'not_recorded'),
                                             'quality': getattr(self.motion_estimator, 'diagnostic', {}),
                                             'warp_px': (None if warp is None or self.target_lock.camera_motion_reason == 'invalid_warp'
                                                         else warp.tolist())},
                              elapsed_since_confirmed_s=self.target_lock.elapsed_since_seen)
            if selected is not None:
                track_id, area, confidence, x1, y1, x2, y2 = selected
                detection = PerceptionNode.to_detection(selected, msg.header.stamp, width, height)
                label = f'TARGET CONFIRMED ID={track_id} conf={confidence:.2f}'
            elif vehicles.vehicles:
                label = f'VEHICLES={len(vehicles.vehicles)} / TARGET UNCONFIRMED'
            else:
                label = 'NO VEHICLE OBSERVATION'
            debug_payload = (image, vehicles, selected, label, msg.header)
        except Exception as exc:
            # Negative observations prevent continued motion on stale positives.
            detection = TargetDetection()
            detection.stamp = msg.header.stamp
            self.target_lock.clear_pending()
            diagnostic.update(mode='error', error=str(exc))
            now = time.monotonic()
            if now - self.last_log >= 1.0:
                self.get_logger().error(f'YOLO frame failed: {exc}')
                self.last_log = now
        publish_started = time.monotonic()
        self.target_pub.publish(detection)
        target_published_at = time.monotonic()
        self.vehicles_pub.publish(vehicles)
        vehicles_published_at = time.monotonic()
        if debug_payload is not None:
            debug_started = time.monotonic()
            try:
                PerceptionNode.publish_debug(self, *debug_payload)
            except Exception as exc:
                diagnostic['debug_publish_error'] = str(exc)
            diagnostic['debug_render_publish_s'] = time.monotonic() - debug_started
        diagnostic.update(vehicle_detected=bool(vehicles.vehicles),
                          vehicle_count=len(vehicles.vehicles),
                          tracked_vehicle_count=sum(item.track_id >= 0 for item in vehicles.vehicles),
                          processing_s=time.monotonic() - started,
                          queue_wait_s=queue_wait_s,
                          frame_age_s=time.monotonic() - received_at,
                          replaced_frames=getattr(getattr(self, 'frame_buffer', None), 'replaced', 0),
                          target_publish_s=target_published_at-publish_started,
                          target_publish_age_s=target_published_at-received_at,
                          vehicles_publish_s=vehicles_published_at-target_published_at,
                          identity_confirmed=bool(detection.detected))
        status = String()
        status.data = json.dumps(diagnostic, allow_nan=False)
        self.association_pub.publish(status)
        if time.monotonic() - self.last_log >= 1.0:
            self.get_logger().info('ASSOCIATION ' + status.data)
            self.last_log = time.monotonic()

    def publish_debug(self, image, vehicles, selected, label, header):
        for observation in vehicles.vehicles:
            box = observation.detection
            cv2.rectangle(image, (int(box.bbox_x), int(box.bbox_y)),
                          (int(box.bbox_x+box.bbox_width), int(box.bbox_y+box.bbox_height)), (0, 165, 255), 1)
        if selected is not None:
            x1, y1, x2, y2 = selected[3:]
            cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(image, label, (16, 32), cv2.FONT_HERSHEY_SIMPLEX, .7, (0, 255, 255), 2)
        debug = self.bridge.cv2_to_imgmsg(image, encoding='bgr8')
        debug.header = header
        self.debug_pub.publish(debug)

    @staticmethod
    def create_motion_estimator():
        from uav_learning.vehicle_camera_motion import BackgroundMotionEstimator
        return BackgroundMotionEstimator(downscale=2)

    @staticmethod
    def create_tracker(confidence):
        from uav_learning.vehicle_byte_tracker import CameraMotionByteTracker
        from ultralytics.utils import YAML, IterableSimpleNamespace
        from ultralytics.utils.checks import check_yaml
        config = YAML.load(check_yaml('bytetrack.yaml'))
        config['track_high_thresh'] = confidence
        config['new_track_thresh'] = confidence
        config['track_low_thresh'] = min(config['track_low_thresh'], confidence)
        if not hasattr(CameraMotionByteTracker.__mro__[1], '_pre_first_associate'):
            raise RuntimeError('Install the tested Ultralytics version from requirements-yolo.txt')
        return CameraMotionByteTracker(IterableSimpleNamespace(**config))

    def infer_vehicles(self, image):
        started = time.monotonic()
        yolo_started = time.monotonic()
        result = self.model.predict(
            source=image, classes=self.class_ids,
            conf=self.settings['tracking_confidence_threshold'],
            imgsz=self.settings['image_size'],
            device=self.settings['device'], verbose=False)[0]
        yolo_s = time.monotonic() - yolo_started
        boxes = result.boxes
        if boxes is None:
            from ultralytics.engine.results import Boxes
            boxes = Boxes(np.empty((0, 6), dtype=np.float32), image.shape[:2])
        gmc_started = time.monotonic()
        lock = getattr(self, 'target_lock', None)
        height, width = image.shape[:2]
        previous_view = target_view(lock, width, height, None, now=gmc_started)
        anchor = None if previous_view is None else previous_view[:2] * [width, height]
        exclusions = boxes.cpu().numpy().xyxy
        predicted_mask = (previous_view is not None and choose_crop(previous_view, width, height) is not None)
        if predicted_mask:
            exclusions = np.vstack((exclusions, VehicleTargetLock.view_box(
                previous_view.reshape(4, 1), width, height)))
        self.camera_motion = (self.motion_estimator.apply(image, exclusions, anchor=anchor)
                              if self.motion_estimator is not None else None)
        gmc_s = time.monotonic() - gmc_started
        self.candidate_sources = ['full_frame'] * len(boxes)
        full_time = time.monotonic() - started
        self.detector_diagnostic = {'full_frame_s': full_time, 'full_frame_count': len(boxes),
                                    'gmc_s': gmc_s, 'full_frame_yolo_s': yolo_s,
                                    'predicted_foreground_mask': bool(predicted_mask),
                                    'roi_reason': 'disabled', 'roi_count': 0}
        if self.settings.get('target_roi_enabled', False):
            # Decay on every frame, including skipped zooms, so a temporary
            # slow pass cannot make the deadline predictor permanently latch.
            self.roi_latency_estimate_s = max(0.18, getattr(self, 'roi_latency_estimate_s', 0.18) * 0.95)
            height, width = image.shape[:2]
            view = target_view(lock, width, height, self.camera_motion, now=gmc_started)
            self.detector_diagnostic['roi_view_norm'] = None if view is None else view[:2].tolist()
            crop = choose_crop(view, width, height)
            if crop is None:
                self.detector_diagnostic['roi_reason'] = 'no_target_view'
            elif not needs_zoom(boxes, view, width, height, self.settings['confidence_threshold']):
                self.detector_diagnostic['roi_reason'] = 'strong_full_frame_evidence'
            elif full_time > self.settings['target_roi_full_frame_budget_s']:
                self.detector_diagnostic['roi_reason'] = 'full_frame_budget_exceeded'
            elif (time.monotonic() - getattr(self, 'frame_received_at', started)
                  + max(0.18, getattr(self, 'roi_latency_estimate_s', 0.18)) + 0.02
                  > self.settings.get('max_frame_age_s', 0.5)):
                self.detector_diagnostic['roi_reason'] = 'frame_deadline_budget'
            else:
                roi_started = time.monotonic()
                self.detector_diagnostic.update(roi_bounds=list(crop), roi_reason='attempted')
                try:
                    left, top, right, bottom = crop
                    zoom = self.model.predict(
                        source=image[top:bottom, left:right], classes=self.class_ids,
                        conf=self.settings['tracking_confidence_threshold'],
                        imgsz=self.settings['target_roi_image_size'],
                        device=self.settings['device'], verbose=False)[0].boxes
                    self.detector_diagnostic['roi_yolo_s'] = time.monotonic() - roi_started
                    if zoom is not None and len(zoom):
                        merge_started = time.monotonic()
                        boxes, self.candidate_sources = merge_boxes(boxes, zoom, crop, image.shape[:2])
                        self.detector_diagnostic['roi_merge_s'] = time.monotonic() - merge_started
                    self.detector_diagnostic.update(roi_reason='completed',
                                                   roi_count=0 if zoom is None else len(zoom))
                except Exception as exc:
                    # Optional zoom failure must not discard valid full-frame evidence.
                    self.detector_diagnostic.update(roi_reason='inference_error', roi_error=str(exc))
                self.detector_diagnostic['roi_s'] = time.monotonic() - roi_started
                self.roi_latency_estimate_s = max(self.detector_diagnostic['roi_s'],
                                                  getattr(self, 'roi_latency_estimate_s', 0.18) * 0.95)
        # ByteTrack returns the original detection index. Keep every YOLO box,
        # including tentative/unassigned boxes that model.track() can suppress.
        tracker_started = time.monotonic()
        tracks = self.tracker.update(boxes.cpu().numpy(), image, camera_motion=self.camera_motion)
        ids = [None] * len(boxes)
        for track in tracks:
            ids[int(track[-1])] = int(track[4])
        self.detector_diagnostic['bytetrack_s'] = time.monotonic() - tracker_started
        return boxes, ids

    @staticmethod
    def to_detection(item, stamp, width, height):
        _, area, confidence, x1, y1, x2, y2 = item
        detection = TargetDetection()
        detection.stamp = stamp
        detection.detected = True
        detection.confidence = float(confidence)
        detection.bbox_x, detection.bbox_y = float(x1), float(y1)
        detection.bbox_width, detection.bbox_height = float(x2 - x1), float(y2 - y1)
        detection.center_u, detection.center_v = float((x1 + x2) / 2), float((y1 + y2) / 2)
        detection.center_u_norm = detection.center_u / (width / 2) - 1.0
        detection.center_v_norm = detection.center_v / (height / 2) - 1.0
        detection.area_ratio = float(area / (width * height))
        return detection

    def state_callback(self, msg):
        if msg.data == 'TRACK':
            self.tracking_started = True
        elif msg.data == 'SEARCH' and not self.airborne_search_initialized:
            # Ground-level appearance is unsuitable after takeoff; acquire
            # the mission target from the airborne view before tracking starts.
            self.airborne_search_initialized = True
            if getattr(self, 'frame_worker', None) is not None:
                self.reset_requested = True
            else:
                PerceptionNode.reset_airborne_identity(self)

    def reset_airborne_identity(self):
        self.target_id = None
        self.target_lock = VehicleTargetLock(
            self.settings['target_reacquire_timeout'],
            self.settings['acquisition_center_gate'],
            self.settings['acquisition_confirm_frames'],
            self.settings['confidence_threshold'],
            self.settings['weak_idless_confirm_frames'],
            self.settings['weak_idless_max_age'],
            recovery_competition_enabled=self.settings.get('recovery_competition_enabled', False),
            predict_box_scale_velocity=self.settings.get('predict_box_scale_velocity', True),
            overlap_candidate_recovery=self.settings.get('overlap_candidate_recovery', True),
            bounded_scale_prediction=self.settings.get('bounded_scale_prediction', True),
            overlap_confirmation_continuity=self.settings.get('overlap_confirmation_continuity', True))

    @staticmethod
    def appearance(image, box):
        x1, y1, x2, y2 = map(int, box)
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            return None
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, (0, 60, 40), (179, 255, 255))
        if cv2.countNonZero(mask) < 10:
            return None
        histogram = cv2.calcHist([hsv], [0, 1], mask, [18, 8], [0, 180, 0, 256])
        return cv2.normalize(histogram, histogram).astype('float32')


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = PerceptionNode()
        node.start_worker()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
