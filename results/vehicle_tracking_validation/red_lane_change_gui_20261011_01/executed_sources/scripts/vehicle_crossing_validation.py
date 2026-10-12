#!/usr/bin/env python3
"""Separate crossing scenario and read-only, timestamp-matched identity evidence."""

import argparse
from collections import Counter, deque
import itertools
import json
import math
from pathlib import Path
import queue
import time
import xml.etree.ElementTree as ET

import numpy as np
from scipy.spatial.transform import Rotation

from vehicle_lane_change import (START as LANE_START, END as LANE_END,
                                 lane_change_pose, lane_change_phase,
                                 lane_change_geometry, lane_change_evidence)

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('x500_perception_0', 'tracked_vehicle', 'parked_vehicle', 'crossing_vehicle')
START, DURATION = 35.0, 8.0


def overtaking_pose(target, motion):
    # Remain behind during initial acquisition, then pass on the +4 m lane.
    offset = (-28. + 20. * motion / START if motion < START
              else -8. + 16. * (motion - START) / DURATION)
    return target['x'] + offset, 4.0, 0.0


def lateral_clearance(corners, target, other):
    target_world = Rotation.from_quat(target['q']).apply(corners) + target['p']
    other_world = Rotation.from_quat(other['q']).apply(corners) + other['p']
    return float(max(other_world[:, 1].min() - target_world[:, 1].max(),
                     target_world[:, 1].min() - other_world[:, 1].max()))


def mesh_corners(model_file):
    visual = ET.parse(model_file).find('.//visual')
    mesh = visual.find('geometry/mesh')
    scale = np.array([float(value) for value in mesh.findtext('scale').split()])
    vertices = []
    with (model_file.parent / mesh.findtext('uri')).open() as stream:
        for line in stream:
            if line.startswith('v '):
                vertices.append([float(value) for value in line.split()[1:4]])
    vertices = np.asarray(vertices) * scale
    pose = [float(value) for value in visual.findtext('pose', '0 0 0 0 0 0').split()]
    corners = np.array(list(itertools.product(*zip(vertices.min(0), vertices.max(0)))))
    return Rotation.from_euler('xyz', pose[3:]).apply(corners) + pose[:3]


def project_box(corners, car, drone, camera, intrinsic, width, height):
    # Gazebo camera axes: X forward, Y left, Z up. Link pose is model-relative.
    world = Rotation.from_quat(car['q']).apply(corners) + car['p']
    local = Rotation.from_quat(drone['q']).inv().apply(world - drone['p'])
    local = Rotation.from_quat(camera['q']).inv().apply(local - camera['p'])
    depth = local[:, 0]
    if np.any(depth <= 0.1):
        return None
    pixels = np.column_stack((-local[:, 1] / depth, -local[:, 2] / depth, np.ones(len(local))))
    pixels = pixels @ np.asarray(intrinsic).reshape(3, 3).T
    low, high = pixels[:, :2].min(0), pixels[:, :2].max(0)
    box = [max(0., low[0]), max(0., low[1]), min(float(width), high[0]), min(float(height), high[1])]
    return box if box[2] > box[0] and box[3] > box[1] else None


def iou(a, b):
    if a is None or b is None:
        return 0.0
    intersection = max(0., min(a[2], b[2])-max(a[0], b[0])) * max(0., min(a[3], b[3])-max(a[1], b[1]))
    union = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - intersection
    return intersection / union if union > 0 else 0.0


def classify_identity(accepted, boxes):
    target = boxes.get('tracked_vehicle')
    others = [name for name in boxes if name != 'tracked_vehicle']
    if any(iou(target, boxes[name]) > 0.1 for name in others):
        return 'overlap_unscorable', {}
    scores = {name: iou(accepted, box) for name, box in boxes.items() if box is not None}
    if accepted is None:
        return 'unconfirmed', scores
    order = sorted(scores, key=scores.get, reverse=True)
    if not order or scores[order[0]] < 0.4 or (len(order) > 1 and scores[order[0]]-scores[order[1]] < 0.2):
        return 'projection_unscorable', scores
    return order[0], scores


def image_capture_reason(row, last_saved_sim):
    if row['label'] in ('crossing_vehicle', 'parked_vehicle'):
        return 'wrong_identity'
    start, end = ((LANE_START, LANE_END) if row.get('traffic_scenario') == 'lane_change_overtaking'
                  else (START, START + DURATION))
    if (start-3 <= row['motion_time'] <= end+5
            and row['sim_s']-last_saved_sim >= 1.):
        return 'periodic_crossing'
    return None


def identity_summary(rows, events, errors, scenario='crossing', distractor_color='auto'):
    if distractor_color not in ('auto', 'red', 'blue'):
        raise ValueError('distractor_color must be auto, red or blue')
    if distractor_color == 'auto':
        distractor_color = 'blue' if scenario == 'overtaking' else 'red'
    phases = {phase: Counter(row.get('label') for row in rows if row.get('phase') == phase)
              for phase in ('pre', 'during', 'post')}
    actual_start = next((event for event in events if event['event'] == scenario + '_started'), None)
    actual_end = next((event for event in events if event['event'] == scenario + '_completed'), None)
    wrong = sum(row.get('label') in ('crossing_vehicle', 'parked_vehicle') for row in rows)
    overlap = sum(row.get('label') == 'overlap_unscorable' and row.get('phase') == 'during' for row in rows)
    post = [row for row in rows if row.get('phase') == 'post' and row.get('label') == 'tracked_vehicle'
            and actual_end and row['sim_s'] >= actual_end['sim_s']]
    delay = post[0]['sim_s']-actual_end['sim_s'] if post and actual_end else None
    overlap_rows = [row for row in rows if row.get('label') == 'overlap_unscorable' and row.get('phase') == 'during']
    recovered = next((row for row in rows if overlap_rows and row['sim_s'] > overlap_rows[-1]['sim_s']
                      and row.get('label') == 'tracked_vehicle'), None)
    recovery_sim = recovered['sim_s']-overlap_rows[-1]['sim_s'] if recovered else None
    recovery_wall = recovered['wall_s']-overlap_rows[-1]['wall_s'] if recovered and 'wall_s' in recovered else None
    scored = [row['label'] for row in rows if row.get('label') in NAMES[1:]]
    switches = sum(a != b for a, b in zip(scored, scored[1:]))
    matched_fraction = sum(row.get('label') not in ('missing_matched_truth', 'unexpected_camera_frame')
                           for row in rows)/len(rows) if rows else 0.
    # Completion alone, detector IDs, and ambiguous overlapping boxes cannot prove identity.
    geometry = [row for row in rows if row.get('phase') in ('during', 'post')
                and 'world_lateral_clearance_m' in row]
    minimum_clearance = min((row['world_lateral_clearance_m'] for row in geometry), default=None)
    during = [row for row in geometry if row.get('phase') == 'during']
    passed = bool(len(during) >= 10 and
                  min(row['relative_longitudinal_m'] for row in during) < -4.1 and
                  max(row['relative_longitudinal_m'] for row in geometry) > 4.1)
    lane_evidence = lane_change_evidence(rows) if scenario == 'lane_change_overtaking' else None
    scenario_evidence = (lane_evidence['maneuver_observed'] if lane_evidence is not None else
                         overlap >= 3 if scenario == 'crossing' else
                         passed and minimum_clearance is not None and minimum_clearance >= .5)
    verified = bool(actual_start and actual_end and scenario_evidence and
                    phases['pre']['tracked_vehicle'] >= 10 and phases['post']['tracked_vehicle'] >= 10
                    and matched_fraction >= .9 and wrong == 0 and not errors)
    return {'identity_independently_verified': verified, 'wrong_identity_observations': wrong,
            'target_color': 'red', 'distractor_color': distractor_color,
            'traffic_scenario': scenario,
            'overtaking_observed': (lane_evidence['maneuver_observed'] if lane_evidence is not None else
                                   passed if scenario == 'overtaking' else None),
            'lane_change': lane_evidence,
            'minimum_world_lateral_clearance_m': minimum_clearance,
            'traffic_started': bool(actual_start), 'traffic_completed': bool(actual_end),
            'phase_counts': {key: dict(value) for key, value in phases.items()},
            'overlap_observations': overlap, 'post_crossing_confirmation_sim_s': delay,
            'post_traffic_confirmation_sim_s': delay,
            'after_last_overlap_confirmation_sim_s': recovery_sim,
            'after_last_overlap_confirmation_wall_s': recovery_wall,
            'scorable_identity_switches': switches,
            'observations_total': len(rows), 'scorable_observations': len(scored),
            'matched_truth_fraction': matched_fraction,
            'crossing_started': scenario == 'crossing' and bool(actual_start),
            'crossing_completed': scenario == 'crossing' and bool(actual_end),
            'errors': errors, 'limitations': [
                'Labels use projected mesh bounding volumes, not per-pixel instance masks.',
                'Overlapping or poorly matched boxes are unscorable, never assumed correct.',
                'Post-confirmation latency is in simulation seconds; mission recovery uses wall seconds.',
                'No identity claims are made for unscorable frames or absent scenario evidence.',
                ('Different-color overtaking does not validate same-appearance crossing recovery.'
                 if scenario == 'overtaking' and distractor_color == 'blue' else
                 'Same-appearance separate-lane overtaking does not validate overlapping crossing recovery.'
                 if scenario == 'overtaking' else
                 'Identity claims apply only to the tested traffic geometry and appearance configuration.')]}


def main():
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import CameraInfo, Image
    from cv_bridge import CvBridge
    import cv2
    from std_msgs.msg import String
    from gz.transport13 import Node as GzNode
    from gz.msgs10.pose_v_pb2 import Pose_V
    from uav_learning.vehicle_scene import car_sdf, distractor_model_file
    from uav_learning.vehicle_gazebo_client import IsolatedGazeboSceneClient

    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--scenario', choices=('crossing', 'overtaking', 'lane_change_overtaking'),
                        default='crossing')
    parser.add_argument('--distractor-color', choices=('auto', 'red', 'blue'), default='auto')
    parser.add_argument('--vehicle-speed', type=float, default=.8)
    args = parser.parse_args()
    if not math.isfinite(args.vehicle_speed) or args.vehicle_speed <= 0:
        parser.error('vehicle-speed must be positive and finite')
    directory = args.output
    rclpy.init()

    class Crossing(Node):
        def __init__(self):
            super().__init__('vehicle_crossing_validation', parameter_overrides=[
                rclpy.parameter.Parameter('use_sim_time', value=True)])
            self.output = (directory / 'identity_observations.jsonl').open('w')
            self.poses_output = (directory / 'identity_poses.jsonl').open('w')
            self.event_output = (directory / 'crossing_events.jsonl').open('w')
            self.image_output = (directory / 'crossing_image_manifest.jsonl').open('w')
            self.service_output = (directory / 'traffic_service.jsonl').open('w')
            self.images, self.cv_bridge = deque(maxlen=30), CvBridge()
            self.last_saved_sim = -math.inf
            self.saved_image_stamps = set()
            self.pose_queue = queue.Queue(maxsize=200)
            self.gz_node = GzNode()
            self.gazebo_client = IsolatedGazeboSceneClient(record=self.record_service, client='traffic')
            self.gz_node.subscribe(Pose_V, '/world/default/pose/info', self.queue_pose)
            self.model = ROOT / 'ros2_ws/src/uav_learning/config/models/tracking_car/model.sdf'
            self.distractor_model = distractor_model_file(self.model, args.scenario, args.distractor_color)
            self.corners = mesh_corners(self.model)
            if not np.allclose(self.corners, mesh_corners(self.distractor_model), atol=1e-8):
                raise ValueError('Identity projections require matching vehicle geometry.')
            self.poses, self.pending = deque(maxlen=600), deque(maxlen=100)
            self.rows, self.events, self.errors = [], [], []
            self.info, self.gt, self.spawned = None, None, False
            self.started, self.completed, self.final_pose = False, False, None
            self.last_maneuver_phase = None
            self.state = ''
            self.start_wall = time.monotonic()
            self.create_subscription(CameraInfo, '/camera/camera_info', self.camera_info, qos_profile_sensor_data)
            self.create_subscription(Image, '/camera/image_raw',
                                     lambda message: self.images.append(message), qos_profile_sensor_data)
            self.create_subscription(String, '/validation/vehicle_ground_truth', self.truth, 10)
            self.create_subscription(String, '/perception/association', self.association, 10)
            self.create_subscription(String, '/mission/state', self.state_callback, 10)
            self.create_timer(0.2, self.tick)
            self.create_timer(0.05, self.drain_poses)

        def record(self, stream, row):
            stream.write(json.dumps(row, allow_nan=False)+'\n')
            stream.flush()

        def camera_info(self, msg):
            changed = self.info is None or (self.info.width, self.info.height, list(self.info.k)) != (
                msg.width, msg.height, list(msg.k))
            self.info = msg
            if changed:
                (directory / 'identity_camera_info.json').write_text(json.dumps({
                    'width': msg.width, 'height': msg.height, 'k': list(msg.k),
                    'stamp': {'sec': msg.header.stamp.sec, 'nanosec': msg.header.stamp.nanosec}}, indent=2) + '\n')

        def truth(self, msg):
            self.gt = json.loads(msg.data)

        def state_callback(self, msg):
            self.state = msg.data.strip()

        def queue_pose(self, msg):
            try:
                self.pose_queue.put_nowait(msg)
            except queue.Full:
                pass

        def drain_poses(self):
            while not self.pose_queue.empty():
                self.pose(self.pose_queue.get_nowait())

        def pose(self, msg):
            poses = {}
            stamp = msg.header.stamp
            for transform in msg.pose:
                name = transform.name
                if name in NAMES or name in ('camera_link', 'tracking_occluder'):
                    t, q = transform.position, transform.orientation
                    poses[name] = {'p': [t.x, t.y, t.z], 'q': [q.x, q.y, q.z, q.w]}
            row = {'sim_s': stamp.sec + stamp.nsec/1e9, 'poses': poses}
            self.poses.append(row)
            self.record(self.poses_output, row)
            self.drain()

        def association(self, msg):
            if self.state not in ('SEARCH', 'DETECT', 'APPROACH', 'TRACK', 'RECOVER'):
                return
            data = json.loads(msg.data)
            stamp = data['stamp']
            self.pending.append((stamp['sec']+stamp['nanosec']/1e9, data,
                                 dict(self.gt) if self.gt else None, time.monotonic()-self.start_wall))
            self.drain()

        def drain(self):
            if not self.poses or self.info is None:
                return
            while self.pending and self.pending[0][0] <= self.poses[-1]['sim_s']:
                sim_s, data, gt, wall_s = self.pending.popleft()
                sample = min(self.poses, key=lambda row: abs(row['sim_s']-sim_s))
                age = abs(sample['sim_s']-sim_s)
                poses = sample['poses']
                motion = (gt or {}).get('motion_time', 0)
                if 'tracked_vehicle' in poses:
                    motion = max(0., (poses['tracked_vehicle']['p'][0]-16.)/args.vehicle_speed)
                crossing_start = next((event['sim_s'] for event in self.events
                                       if event['event'] == args.scenario + '_started'), None)
                crossing_end = next((event['sim_s'] for event in self.events
                                     if event['event'] == args.scenario + '_completed'), None)
                phase = ('pre' if crossing_start is None or sim_s < crossing_start else
                         'post' if crossing_end is not None and sim_s >= crossing_end else 'during')
                row = {'sim_s': sim_s, 'stamp': data['stamp'], 'wall_s': wall_s, 'motion_time': motion, 'phase': phase,
                       'pose_age_sim_s': age, 'locked_track_id': data.get('locked_track_id'),
                       'traffic_scenario': args.scenario}
                if args.scenario in ('overtaking', 'lane_change_overtaking') and age <= .15 and all(
                        name in poses for name in ('tracked_vehicle', 'crossing_vehicle')):
                    row['world_lateral_clearance_m'] = lateral_clearance(
                        self.corners, poses['tracked_vehicle'], poses['crossing_vehicle'])
                    row['relative_longitudinal_m'] = (
                        poses['crossing_vehicle']['p'][0] - poses['tracked_vehicle']['p'][0])
                    if args.scenario == 'lane_change_overtaking':
                        row['maneuver_phase'] = lane_change_phase(motion)
                        row.update(lane_change_geometry(
                            self.corners, poses['tracked_vehicle'], poses['crossing_vehicle']))
                if age > 0.15 or not all(name in poses for name in ('x500_perception_0', 'tracked_vehicle', 'camera_link')):
                    row['label'] = 'missing_matched_truth'
                elif np.linalg.norm(poses['camera_link']['p']) > 1.0:
                    row['label'] = 'unexpected_camera_frame'
                elif poses.get('tracking_occluder', {}).get('p', [0, 0, -10])[2] > 0:
                    row['label'] = 'panel_occlusion_unscorable'
                else:
                    boxes = {name: project_box(self.corners, poses[name], poses['x500_perception_0'],
                        poses['camera_link'], self.info.k, self.info.width, self.info.height)
                        for name in NAMES[1:] if name in poses}
                    accepted = next((item['bbox'] for item in data.get('candidates', []) if item.get('accepted')), None)
                    row['label'], row['scores'] = classify_identity(accepted, boxes)
                    row.update(projected_boxes=boxes, accepted_box=accepted)
                self.rows.append(row)
                self.record(self.output, row)
                capture_reason = image_capture_reason(row, self.last_saved_sim)
                stamp_key = (data['stamp']['sec'], data['stamp']['nanosec'])
                if capture_reason and stamp_key not in self.saved_image_stamps:
                    raw = next((item for item in reversed(self.images)
                                if item.header.stamp.sec == data['stamp']['sec']
                                and item.header.stamp.nanosec == data['stamp']['nanosec']), None)
                    if raw is not None:
                        pixels = self.cv_bridge.imgmsg_to_cv2(raw, desired_encoding='bgr8')
                        name = (f'identity_wrong_{stamp_key[0]:06d}_{stamp_key[1]:09d}_raw.png'
                                if capture_reason == 'wrong_identity' else f'crossing_{sim_s:08.3f}_raw.png')
                        if cv2.imwrite(str(directory / name), pixels):
                            self.record(self.image_output, {'image': name, 'capture_reason': capture_reason, **row})
                            self.saved_image_stamps.add(stamp_key)
                            self.last_saved_sim = sim_s
                        else:
                            self.errors.append('crossing_image_save_failed')
                    elif capture_reason == 'wrong_identity':
                        self.record(self.image_output, {'image': None, 'capture_reason': capture_reason,
                                                       'capture_error': 'matched_raw_image_unavailable', **row})

        def request(self, service, kind, request):
            return self.gazebo_client.request(service, kind, request)

        def record_service(self, diagnostic):
            diagnostic['sim_s'] = self.get_clock().now().nanoseconds / 1e9
            self.record(self.service_output, diagnostic)

        def event(self, name):
            row = {'event': name, 'sim_s': self.get_clock().now().nanoseconds/1e9,
                   'wall_s': time.monotonic()-self.start_wall, 'motion_time': self.gt['motion_time'],
                   'scenario': args.scenario}
            self.events.append(row)
            self.record(self.event_output, row)

        def tick(self):
            if not self.spawned:
                initial_x, initial_y = ((-12, 0) if args.scenario == 'lane_change_overtaking' else
                                        (-12, 4) if args.scenario == 'overtaking' else (16, -15))
                self.spawned = self.request('create', 'gz.msgs.EntityFactory',
                    'sdf: '+json.dumps(car_sdf(self.distractor_model, 'crossing_vehicle',
                                             initial_x, initial_y)))
                return
            if not self.gt or (args.scenario == 'crossing' and (
                    self.gt['motion_time'] < START or self.completed)):
                return
            start, end = ((LANE_START, LANE_END) if args.scenario == 'lane_change_overtaking'
                          else (START, START + DURATION))
            progress = min(1., (self.gt['motion_time']-start)/(end-start))
            if args.scenario == 'lane_change_overtaking':
                x, y, yaw = lane_change_pose(self.gt, self.gt['motion_time'], args.vehicle_speed)
            elif args.scenario == 'overtaking':
                x, y, yaw = overtaking_pose(self.gt, self.gt['motion_time'])
            else:
                x, y = self.gt['x']-2., self.gt['y']-4.5+9.*progress
                yaw = math.atan2(9./DURATION, args.vehicle_speed)
            request = (f'name: "crossing_vehicle", position: {{x: {x}, y: {y}, z: 0.05}}, '
                       f'orientation: {{z: {math.sin(yaw/2)}, w: {math.cos(yaw/2)}}}')
            if not self.request('set_pose', 'gz.msgs.Pose', request):
                self.errors.append('crossing_pose_update_failed')
                return
            if args.scenario == 'lane_change_overtaking':
                phase = lane_change_phase(self.gt['motion_time'])
                if phase != self.last_maneuver_phase:
                    self.event('lane_change_' + phase)
                    self.last_maneuver_phase = phase
            if not self.started and self.gt['motion_time'] >= start:
                self.started = True
                self.event(args.scenario + '_started')
            if progress == 1. and not self.completed:
                self.completed = True
                self.event(args.scenario + '_completed')

        def close(self):
            self.gazebo_client.close()
            self.gz_node.unsubscribe('/world/default/pose/info')
            self.drain_poses()
            result = identity_summary(self.rows, self.events, self.errors, args.scenario, args.distractor_color)
            (directory / 'identity_report.json').write_text(json.dumps(result, indent=2)+'\n')
            for stream in (self.output, self.poses_output, self.event_output, self.image_output, self.service_output):
                stream.close()

    node = Crossing()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
