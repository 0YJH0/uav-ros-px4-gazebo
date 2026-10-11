"""Exercise actual ROS publication without running PX4 or loading weights."""

import json
import sys
import time
from types import SimpleNamespace

import numpy as np
import pytest
import rclpy
from cv_bridge import CvBridge
from std_msgs.msg import String
from uav_interfaces.msg import TargetDetection, VehicleDetections

from uav_learning.perception_node import PerceptionNode


class Values:
    def __init__(self, values):
        self.values = values

    def cpu(self):
        return self

    def tolist(self):
        return self.values


@pytest.mark.parametrize('use_worker', [False, True])
def test_ros_topics_keep_visible_vehicles_separate_from_confirmed_target(monkeypatch, use_worker):
    boxes = SimpleNamespace(xyxy=Values([[30, 30, 70, 70]]),
                            conf=Values([0.9]), id=Values([7]))
    warmups = []
    model = SimpleNamespace(names={2: 'car'}, predict=lambda **kwargs: warmups.append(kwargs))
    monkeypatch.setitem(sys.modules, 'ultralytics', SimpleNamespace(YOLO=lambda *args, **kwargs: model))
    monkeypatch.setattr(PerceptionNode, 'create_tracker', staticmethod(lambda confidence: None))
    monkeypatch.setattr(PerceptionNode, 'create_motion_estimator', staticmethod(lambda: None))
    monkeypatch.setattr(PerceptionNode, 'infer_vehicles',
                        lambda self, image: (boxes, boxes.id.tolist()))
    received = {'vehicles': [], 'association': [], 'target': []}
    rclpy.init()
    perception, listener = None, None
    try:
        perception = PerceptionNode()
        if use_worker:
            perception.start_worker()
            assert len(warmups) == 2
            assert {entry['source'].shape[:2] for entry in warmups} == {(540, 960), (320, 320)}
            assert perception.target_lock.last_seen is None
        listener = rclpy.create_node('vehicle_perception_test_listener')
        listener.create_subscription(VehicleDetections, '/perception/vehicles',
                                     received['vehicles'].append, 10)
        listener.create_subscription(String, '/perception/association',
                                     received['association'].append, 10)
        listener.create_subscription(TargetDetection, '/perception/target',
                                     received['target'].append, 10)
        image = np.zeros((100, 100, 3), np.uint8)
        image[30:70, 30:70, 2] = 255
        bridge = CvBridge()
        for frame in range(5):
            if frame == 1:
                boxes.xyxy, boxes.id = Values([[75, 75, 95, 95]]), Values([9])
            if frame == 2:
                perception.target_lock.last_seen -= 20.0
                boxes.xyxy, boxes.id = Values([[30, 30, 70, 70]]), Values([19])
            message = bridge.cv2_to_imgmsg(image.copy(), 'bgr8')
            message.header.stamp.sec = 100 + frame
            if use_worker:
                perception.enqueue_image(message)
            else:
                perception.image_callback(message)
            deadline = time.monotonic() + 3.0
            while min(len(messages) for messages in received.values()) < frame + 1:
                assert time.monotonic() < deadline, 'ROS publication did not arrive'
                rclpy.spin_once(listener, timeout_sec=0.05)
        states = [json.loads(msg.data) for msg in received['association']]
        assert all(msg.vehicles for msg in received['vehicles'])
        assert [msg.detected for msg in received['target']] == [True, False, False, False, True]
        assert [state['identity_confirmed'] for state in states] == [True, False, False, False, True]
        assert all(state['vehicle_detected'] for state in states)
        assert states[1]['candidates'][0]['reason'] == 'center_gate'
        assert states[-1]['mode'] == 'reacquiring'
        assert received['target'][-1].stamp.sec == received['vehicles'][-1].stamp.sec == 104
    finally:
        if perception is not None:
            perception.destroy_node()
        if listener is not None:
            listener.destroy_node()
        rclpy.shutdown()
