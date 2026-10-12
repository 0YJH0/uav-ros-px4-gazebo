#!/usr/bin/env python3
"""Record a real ROS/PX4 flight and report observed tracking and landing."""

import argparse
from collections import deque
import json
import math
from pathlib import Path
import time

import cv2
from cv_bridge import CvBridge
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from sensor_msgs.msg import Image
from std_msgs.msg import String
from px4_msgs.msg import VehicleLocalPosition, VehicleStatus, VehicleLandDetected, TrajectorySetpoint
from uav_interfaces.msg import TargetDetection


class ValidationRecorder(Node):
    def __init__(self, directory):
        super().__init__('vehicle_tracking_validation')
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.file = (self.directory / 'samples.jsonl').open('w')
        self.association_file = (self.directory / 'association.jsonl').open('w')
        self.scene_service_file = (self.directory / 'scene_service.jsonl').open('w')
        self.latest_association = None
        self.start = time.monotonic()
        self.state = ''
        self.transitions = []
        self.events = []
        self.position = None
        self.navigation = None
        self.setpoint = None
        self.home = None
        self.status = None
        self.landed = None
        self.target = None
        self.track_observations = []
        self.track_positions = []
        self.vehicle_positions = []
        self.occlusions = []
        self.latest_vehicle = None
        self.relative_distances = []
        self.last_image = 0.0
        self.raw_images = deque(maxlen=64)
        self.last_tick = time.monotonic()
        self.track_wall_time = 0.0
        self.follow_started = False
        self.follow_wall_time = 0.0
        self.follow_visible_wall_time = 0.0
        self.follow_positions = []
        self.last_follow_tick = self.start
        self.last_target_time = -math.inf
        self.confirmation_history = deque(maxlen=3)
        self.finished = False
        self.failsafe_observed = False
        self.bridge = CvBridge()
        telemetry = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT,
                               durability=DurabilityPolicy.TRANSIENT_LOCAL)
        images = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
        self.create_subscription(String, '/mission/state', self.state_callback, 10)
        self.create_subscription(String, '/mission/event', self.event_callback, 10)
        self.create_subscription(TargetDetection, '/perception/target',
                                 self.target_callback, 10)
        self.create_subscription(String, '/perception/association',
                                 self.association_callback, 10)
        self.create_subscription(VehicleLocalPosition,
                                 '/fmu/out/vehicle_local_position_v1',
                                 self.position_callback, telemetry)
        self.create_subscription(TrajectorySetpoint, '/fmu/in/trajectory_setpoint',
                                 self.setpoint_callback, images)
        self.create_subscription(VehicleStatus, '/fmu/out/vehicle_status_v1',
                                 self.status_callback, telemetry)
        self.create_subscription(VehicleLandDetected, '/fmu/out/vehicle_land_detected',
                                 self.land_callback, telemetry)
        self.create_subscription(String, '/validation/vehicle_ground_truth',
                                 self.vehicle_callback, 10)
        self.create_subscription(String, '/validation/occlusion',
                                 self.occlusion_callback, 10)
        self.create_subscription(String, '/validation/scene_service', self.scene_service_callback, 100)
        self.create_subscription(Image, '/perception/debug_image',
                                 self.image_callback, images)
        self.create_subscription(Image, '/camera/image_raw',
                                 self.raw_image_callback, images)
        self.create_timer(0.2, self.tick)

    def elapsed(self):
        return time.monotonic() - self.start

    def state_callback(self, msg):
        self.accumulate_follow(time.monotonic())
        if self.state != msg.data:
            self.state = msg.data
            if self.state == 'TRACK':
                self.follow_started = True
            self.transitions.append({'time_s': self.elapsed(), 'state': self.state})
            self.get_logger().info(f'Observed state: {self.state}')

    def event_callback(self, msg):
        self.events.append({'time_s': self.elapsed(), 'event': msg.data})
        if msg.data in ('TARGET_RECOVERED', 'TRACK_REACQUIRED'):
            for event in self.occlusions:
                if (event['end_wall_s'] is not None and
                        event.get('confirmed_recovery_s') is None):
                    event['confirmed_recovery_s'] = self.elapsed() - event['end_wall_s']

    def target_callback(self, msg):
        now = time.monotonic()
        self.accumulate_follow(now)
        if now - self.last_target_time > 0.5:
            self.confirmation_history.clear()
        self.confirmation_history.append(bool(msg.detected))
        self.last_target_time = now
        self.target = {'detected': bool(msg.detected),
                       'confidence': float(msg.confidence),
                       'error_x': float(msg.center_u_norm),
                       'area': float(msg.area_ratio)}
        if self.state == 'TRACK':
            self.track_observations.append(self.target.copy())
        for event in self.occlusions:
            if event.get('end_wall_s') is not None and event.get('recovery_s') is None:
                if msg.detected:
                    event['recovery_s'] = self.elapsed() - event['end_wall_s']
            elif event.get('end_wall_s') is None and not msg.detected:
                event['negative_observations'] += 1

    def association_callback(self, msg):
        self.latest_association = json.loads(msg.data)
        self.association_file.write(json.dumps(
            {'wall_s': self.elapsed(), **self.latest_association}) + '\n')
        self.association_file.flush()

    def scene_service_callback(self, msg):
        self.scene_service_file.write(json.dumps({'wall_s': self.elapsed(), **json.loads(msg.data)}) + '\n')
        self.scene_service_file.flush()

    def occlusion_callback(self, msg):
        info = json.loads(msg.data)
        if info['active']:
            entry_locked = bool(self.state == 'TRACK' and self.target and self.target['detected']
                                and time.monotonic() - self.last_target_time <= 0.5
                                and len(self.confirmation_history) == 3 and all(self.confirmation_history))
            self.occlusions.append({'start_wall_s': self.elapsed(),
                                    'state_at_start': self.state, 'entry_locked': entry_locked,
                                    'end_wall_s': None, 'recovery_s': None,
                                    'confirmed_recovery_s': None,
                                    'negative_observations': 0})
        elif self.occlusions:
            self.occlusions[-1]['end_wall_s'] = self.elapsed()

    def position_callback(self, msg):
        self.navigation = {'heading_rad': float(msg.heading),
                           'velocity_ned': [float(msg.vx), float(msg.vy), float(msg.vz)],
                           'timestamp_sample_us': int(getattr(msg, 'timestamp_sample', 0)),
                           'timestamp_us': int(getattr(msg, 'timestamp', 0)),
                           'xy_valid': bool(msg.xy_valid), 'z_valid': bool(msg.z_valid),
                           'wall_s': self.elapsed()}
        if msg.xy_valid and msg.z_valid:
            self.position = [float(msg.x), float(msg.y), float(msg.z)]
            if self.home is None:
                self.home = self.position.copy()

    def setpoint_callback(self, msg):
        self.setpoint = {'position_ned': [float(value) for value in msg.position], 'yaw_rad': float(msg.yaw),
                         'wall_s': self.elapsed()}

    def status_callback(self, msg):
        self.failsafe_observed = self.failsafe_observed or bool(msg.failsafe)
        self.status = {'arming_state': int(msg.arming_state),
                       'nav_state': int(msg.nav_state),
                       'failsafe': bool(msg.failsafe)}

    def land_callback(self, msg):
        self.landed = bool(msg.landed)

    def vehicle_callback(self, msg):
        self.vehicle_positions.append(json.loads(msg.data))
        self.vehicle_positions[-1]['wall_s'] = self.elapsed()
        self.latest_vehicle = self.vehicle_positions[-1]
        if self.position is not None:
            self.relative_distances.append(math.hypot(
                self.position[1] - self.latest_vehicle['x'],
                self.position[0] - self.latest_vehicle['y']))

    def raw_image_callback(self, msg):
        self.raw_images.append(msg)

    def image_callback(self, msg):
        if self.elapsed() - self.last_image >= 10.0:
            image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            name = f'{self.elapsed():07.1f}_{self.state}'
            cv2.imwrite(str(self.directory / f'{name}.jpg'), image)
            raw = next((frame for frame in reversed(self.raw_images)
                        if frame.header.stamp == msg.header.stamp), None)
            raw_name = None
            if raw is not None:
                pixels = self.bridge.imgmsg_to_cv2(raw, desired_encoding='bgr8')
                candidate = f'{name}_raw.png'
                if cv2.imwrite(str(self.directory / candidate), pixels):
                    raw_name = candidate
            with (self.directory / 'image_manifest.jsonl').open('a') as stream:
                stream.write(json.dumps({'wall_s': self.elapsed(), 'debug_image': name + '.jpg',
                                         'raw_image': raw_name,
                                         'stamp': {'sec': msg.header.stamp.sec,
                                                   'nanosec': msg.header.stamp.nanosec}}) + '\n')
            self.last_image = self.elapsed()

    def tick(self):
        now = time.monotonic()
        self.accumulate_follow(now)
        if self.follow_active() and self.position is not None:
            self.follow_positions.append(self.position.copy())
        if self.state == 'TRACK':
            self.track_wall_time += now - self.last_tick
            if self.position is not None:
                self.track_positions.append(self.position.copy())
        self.last_tick = now
        sample = {'wall_s': self.elapsed(), 'state': self.state,
                  'position_ned': self.position, 'status': self.status,
                  'navigation': self.navigation, 'setpoint': self.setpoint,
                  'landed': self.landed, 'target': self.target,
                  'failsafe_observed': self.failsafe_observed,
                  'association': self.latest_association,
                  'vehicle_ground_truth': self.latest_vehicle}
        self.file.write(json.dumps(sample) + '\n')
        self.file.flush()
        if self.state == 'DONE' and not self.finished:
            self.finish()

    def follow_active(self):
        return self.follow_started and self.state in (
            'TRACK', 'RECOVER', 'SEARCH', 'DETECT', 'APPROACH')

    def accumulate_follow(self, now):
        if self.follow_active():
            self.follow_wall_time += now - self.last_follow_tick
            if self.target is not None and self.target['detected']:
                visible_end = min(now, self.last_target_time + 0.5)
                self.follow_visible_wall_time += max(0.0, visible_end - self.last_follow_tick)
        self.last_follow_tick = now

    def finish(self):
        self.accumulate_follow(time.monotonic())
        self.finished = True
        observations = self.track_observations
        valid = [o for o in observations if o['detected']]
        errors = sorted(abs(o['error_x']) * 480 for o in valid)
        event_names = [event['event'] for event in self.events]
        car_travel = sum(math.hypot(b['x'] - a['x'], b['y'] - a['y'])
                         for a, b in zip(self.vehicle_positions,
                                         self.vehicle_positions[1:]))
        drone_travel = sum(math.dist(a, b) for a, b in zip(
            self.track_positions, self.track_positions[1:]))
        home_error = (math.hypot(self.position[0] - self.home[0],
                                 self.position[1] - self.home[1])
                      if self.position and self.home else None)
        report = {
            'completed': self.state == 'DONE',
            'track_complete_event': 'TRACK_COMPLETE' in event_names,
            'landed': self.landed,
            'disarmed': self.status is not None and
            self.status['arming_state'] == VehicleStatus.ARMING_STATE_DISARMED,
            'final_status': self.status,
            'failsafe_observed': self.failsafe_observed,
            'track_wall_time_s': self.track_wall_time,
            'follow_wall_time_s': self.follow_wall_time,
            'follow_time_visible_fraction': self.follow_visible_wall_time / self.follow_wall_time
            if self.follow_wall_time else 0.0,
            'drone_follow_travel_m': sum(math.dist(a, b) for a, b in zip(
                self.follow_positions, self.follow_positions[1:])),
            'track_detection_fraction': len(valid) / len(observations)
            if observations else 0.0,
            'track_mean_abs_pixel_error': sum(errors) / len(errors) if errors else None,
            'track_p95_abs_pixel_error': errors[int((len(errors) - 1) * .95)]
            if errors else None,
            'vehicle_travel_m': car_travel,
            'drone_track_travel_m': drone_travel,
            'final_home_horizontal_error_m': home_error,
            'wall_duration_s': self.elapsed(),
            'transitions': self.transitions, 'events': self.events,
            'occlusions': self.occlusions,
            'same_vehicle_identity_verified': False,
            'relative_horizontal_distance_min_m': min(self.relative_distances)
            if self.relative_distances else None,
            'relative_horizontal_distance_max_m': max(self.relative_distances)
            if self.relative_distances else None,
        }
        for event in self.occlusions:
            points = [p for p in self.vehicle_positions
                      if event['start_wall_s'] <= p['wall_s'] <=
                      (event['end_wall_s'] or self.elapsed())]
            event['vehicle_travel_during_occlusion_m'] = sum(
                math.hypot(b['x'] - a['x'], b['y'] - a['y'])
                for a, b in zip(points, points[1:]))
        report['occlusion_recovery_passed'] = bool(self.occlusions) and all(
            event.get('entry_locked', False) and event['end_wall_s'] is not None and
            event['negative_observations'] > 0 and
            event['vehicle_travel_during_occlusion_m'] > 0.1 and
            event['recovery_s'] is not None and event['recovery_s'] < 15.0
            and event['confirmed_recovery_s'] is not None
            and event['confirmed_recovery_s'] < 15.0
            for event in self.occlusions)
        report['passed'] = bool(
            report['completed'] and report['track_complete_event'] and
            report['landed'] and report['disarmed'] and
            not self.failsafe_observed and
            car_travel > 1.0 and drone_travel > 1.0 and
            report['track_detection_fraction'] >= .8 and
            report['follow_time_visible_fraction'] >= .8 and
            home_error is not None and home_error <= 1.0)
        if self.occlusions:
            report['passed'] = report['passed'] and report['occlusion_recovery_passed']
        (self.directory / 'report.json').write_text(
            json.dumps(report, indent=2) + '\n')
        self.get_logger().info(json.dumps(report))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    rclpy.init()
    node = ValidationRecorder(args.output)
    try:
        while rclpy.ok() and not node.finished:
            rclpy.spin_once(node, timeout_sec=1.0)
    except KeyboardInterrupt:
        if not node.finished:
            node.finish()
    finally:
        node.file.close()
        node.association_file.close()
        node.scene_service_file.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
