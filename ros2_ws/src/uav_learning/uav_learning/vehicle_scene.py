"""Spawn a street and move a rendered vehicle without exposing its pose to control."""

import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from px4_msgs.msg import VehicleLocalPosition
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from uav_learning.vehicle_gazebo_client import GazeboSceneClient


def street_sdf(overtaking=False):
    root = ET.Element('sdf', version='1.9')
    model = ET.SubElement(root, 'model', name='vehicle_tracking_street')
    ET.SubElement(model, 'static').text = 'true'
    link = ET.SubElement(model, 'link', name='street')

    def box(name, pose, size, color, collision=True):
        visual = ET.SubElement(link, 'visual', name=name)
        ET.SubElement(visual, 'pose').text = pose
        geometry = ET.SubElement(visual, 'geometry')
        ET.SubElement(ET.SubElement(geometry, 'box'), 'size').text = size
        material = ET.SubElement(visual, 'material')
        ET.SubElement(material, 'ambient').text = color
        ET.SubElement(material, 'diffuse').text = color
        if collision:
            solid = ET.SubElement(link, 'collision', name=name)
            ET.SubElement(solid, 'pose').text = pose
            geometry = ET.SubElement(solid, 'geometry')
            ET.SubElement(ET.SubElement(geometry, 'box'), 'size').text = size

    center, length, half_width = (110, 280, 6) if overtaking else (70, 160, 4)
    box('road', f'{center} 0 0.015 0 0 0', f'{length} {half_width * 2} 0.03', '0.12 0.14 0.16 1')
    for side in (-1, 1):
        box(f'sidewalk_{side}', f'{center} {side * (half_width + 1)} 0.1 0 0 0',
            f'{length} 2 0.2', '0.55 0.57 0.59 1')
        for index, x in enumerate((8, 32, 56, 80, 104, 128)):
            height = 4 + (index % 3) * 2
            color = ('0.65 0.72 0.74 1' if side == 1 else '0.72 0.65 0.58 1')
            box(f'building_{side}_{index}',
                f'{x} {side * (half_width + 6)} {height / 2} 0 0 0',
                f'6 6 {height}', color)
        for index, x in enumerate((5, 29, 37)):
            box(f'barrier_{side}_{index}', f'{x} {side * (half_width - .2)} 0.4 0 0 0',
                '1.2 0.25 0.8', '0.9 0.55 0.08 1')
    for index, x in enumerate(range(-28, 250, 4) if overtaking else range(0, 152, 4)):
        for lane in ((-2, 2) if overtaking else (0,)):
            box(f'lane_{index}_{lane}' if overtaking else f'lane_{index}', f'{x} {lane} 0.036 0 0 0',
                '2 0.12 0.01', '0.95 0.95 0.9 1', collision=False)
    return ET.tostring(root, encoding='unicode')


def distractor_model_file(target_model, traffic_scenario='crossing', color='auto'):
    if color not in ('auto', 'red', 'blue'):
        raise ValueError('distractor_color must be auto, red or blue')
    if color == 'auto':
        color = 'blue' if traffic_scenario == 'overtaking' else 'red'
    target_model = Path(target_model)
    return (target_model.parent.parent / 'tracking_car_blue/model.sdf'
            if color == 'blue' else target_model)


def car_sdf(model_file, name, x, y):
    root = ET.parse(model_file).getroot()
    model = root.find('model')
    model.set('name', name)
    ET.SubElement(model, 'pose').text = f'{x} {y} 0.05 0 0 0'
    for uri in root.iter('uri'):
        uri.text = str((Path(model_file).parent / uri.text).resolve())
    return ET.tostring(root, encoding='unicode')


def occluder_sdf():
    return '''<sdf version="1.9"><model name="tracking_occluder">
    <static>true</static><pose>12 0 -10 0 0 0</pose><link name="panel">
    <visual name="panel"><geometry><box><size>0.15 8 7</size></box></geometry>
    <material><ambient>0.3 0.35 0.4 1</ambient>
    <diffuse>0.3 0.35 0.4 1</diffuse></material></visual>
    </link></model></sdf>'''


class VehicleScene(Node):
    def __init__(self):
        super().__init__('vehicle_scene')
        self.declare_parameter('world', 'default')
        self.declare_parameter('vehicle_speed', 0.8)
        self.declare_parameter('occlusion_enabled', False)
        self.declare_parameter('occlusion_start', 15.0)
        self.declare_parameter('occlusion_duration', 4.0)
        self.declare_parameter('traffic_scenario', 'crossing')
        self.declare_parameter('distractor_color', 'auto')
        self.declare_parameter('parked_vehicle_y', -12.0)
        self.world = self.get_parameter('world').value
        self.model_file = (Path(get_package_share_directory('uav_learning'))
                           / 'config/models/tracking_car/model.sdf')
        overtaking = self.get_parameter('traffic_scenario').value in ('overtaking', 'lane_change_overtaking')
        distractor_model = distractor_model_file(
            self.model_file, self.get_parameter('traffic_scenario').value,
            self.get_parameter('distractor_color').value)
        parked_y = float(self.get_parameter('parked_vehicle_y').value)
        if not math.isfinite(parked_y):
            raise ValueError('parked_vehicle_y must be finite')
        self.pending = [street_sdf(overtaking=overtaking),
                        car_sdf(self.model_file, 'tracked_vehicle', 16, 0),
                        car_sdf(distractor_model, 'parked_vehicle', 30, parked_y)]
        if self.get_parameter('occlusion_enabled').value:
            self.pending.append(occluder_sdf())
        self.occluded = False
        self.occlusion_pub = self.create_publisher(
            String, '/validation/occlusion', 10)
        self.ready = False
        self.ground_truth_pub = self.create_publisher(
            String, '/validation/vehicle_ground_truth', 10)
        self.service_pub = self.create_publisher(String, '/validation/scene_service', 100)
        self.gazebo_client = GazeboSceneClient(self.world, record=self.record_service)
        self.moving = False
        self.drone_xy = (0.0, 0.0)
        self.elapsed = 0.0
        self.last_time = self.get_clock().now().nanoseconds / 1e9
        self.create_subscription(String, '/mission/state', self.state_callback, 10)
        self.create_subscription(
            VehicleLocalPosition, '/fmu/out/vehicle_local_position_v1',
            self.position_callback,
            QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT,
                       durability=DurabilityPolicy.TRANSIENT_LOCAL))
        self.timer = self.create_timer(0.2, self.tick)

    def request(self, service, request_type, request):
        return self.gazebo_client.request(service, request_type, request)

    def record_service(self, diagnostic):
        diagnostic['sim_s'] = self.get_clock().now().nanoseconds / 1e9
        self.service_pub.publish(String(data=json.dumps(diagnostic)))
        if not diagnostic['success']:
            self.get_logger().warning('Gazebo service failed: ' + json.dumps(diagnostic))

    def state_callback(self, msg):
        if msg.data.strip() == 'TRACK':
            self.moving = True

    def position_callback(self, msg):
        if msg.xy_valid:
            # Default PX4 Gazebo world: ENU world X=east, Y=north.
            self.drone_xy = (float(msg.y), float(msg.x))

    def tick(self):
        now = self.get_clock().now().nanoseconds / 1e9
        dt = max(0.0, min(now - self.last_time, 0.5))
        self.last_time = now
        if self.pending:
            sdf = self.pending[0]
            if self.request('create', 'gz.msgs.EntityFactory',
                            'sdf: ' + json.dumps(sdf)):
                self.pending.pop(0)
                if not self.pending:
                    self.ready = True
                    self.get_logger().info('Street and vehicles ready.')
            return
        if not self.moving:
            return
        self.elapsed += dt
        speed = float(self.get_parameter('vehicle_speed').value)
        x = 16 + speed * self.elapsed
        y = 0.4 * math.sin(self.elapsed * 0.05)
        if self.get_parameter('occlusion_enabled').value:
            start = float(self.get_parameter('occlusion_start').value)
            duration = float(self.get_parameter('occlusion_duration').value)
            active = start <= self.elapsed < start + duration
            if active != self.occluded:
                z = 3.5 if active else -10.0
                screen_x = (self.drone_xy[0] + x) / 2
                screen_y = (self.drone_xy[1] + y) / 2
                screen_yaw = math.atan2(y - self.drone_xy[1], x - self.drone_xy[0])
                if self.request('set_pose', 'gz.msgs.Pose',
                                f'name: "tracking_occluder", '
                                f'position: {{x: {screen_x}, y: {screen_y}, z: {z}}}, '
                                f'orientation: {{z: {math.sin(screen_yaw / 2)}, '
                                f'w: {math.cos(screen_yaw / 2)}}}'):
                    self.occluded = active
                    self.occlusion_pub.publish(String(data=json.dumps({
                        'active': active, 'motion_time': self.elapsed})))
                    self.get_logger().info(f'Occlusion active={active}')
        yaw = math.atan2(0.02 * math.cos(self.elapsed * 0.05), speed)
        request = (
            f'name: "tracked_vehicle", position: {{x: {x}, y: {y}, z: 0.05}}, '
            f'orientation: {{z: {math.sin(yaw / 2)}, w: {math.cos(yaw / 2)}}}')
        if not self.request('set_pose', 'gz.msgs.Pose', request):
            self.get_logger().warning('Vehicle pose update failed.')
        else:
            self.ground_truth_pub.publish(String(data=json.dumps({
                'x': x, 'y': y, 'z': 0.05, 'motion_time': self.elapsed,
                'occluded': self.occluded})))


def main(args=None):
    rclpy.init(args=args)
    node = VehicleScene()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
