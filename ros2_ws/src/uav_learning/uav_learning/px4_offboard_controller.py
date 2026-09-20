#!/usr/bin/env python3

import math
from collections import deque
from enum import Enum, auto

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile,
    ReliabilityPolicy,
    DurabilityPolicy,
    HistoryPolicy,
)

from px4_msgs.msg import OffboardControlMode
from px4_msgs.msg import TrajectorySetpoint
from px4_msgs.msg import VehicleCommand
from px4_msgs.msg import VehicleCommandAck
from px4_msgs.msg import VehicleLocalPosition
from px4_msgs.msg import VehicleStatus
from px4_msgs.msg import VehicleLandDetected
from std_msgs.msg import String

from uav_interfaces.msg import TargetDetection


class MissionState(Enum):
    WAIT_FOR_PX4 = auto()
    PRESTREAM = auto()
    REQUEST_OFFBOARD = auto()
    ARMING = auto()
    TAKEOFF = auto()
    HOVER = auto()
    SEARCH = auto()
    DETECT = auto()
    APPROACH = auto()
    HOLD = auto()
    RETURN = auto()
    LAND = auto()
    DONE = auto()


class PX4OffboardController(Node):

    TIMER_PERIOD = 0.1          # 10 Hz
    PRESTREAM_TICKS = 20        # 2 seconds
    COMMAND_RETRY_INTERVAL = 1.0

    def __init__(self):
        super().__init__('px4_offboard_controller')

        # =========================================================
        # Mission parameters
        # =========================================================

        self.declare_parameter('target_height', 5.0)
        self.declare_parameter('hover_duration', 2.0)
        self.declare_parameter('hold_duration', 3.0)

        self.declare_parameter('position_tolerance', 0.35)
        self.declare_parameter('vertical_tolerance', 0.30)
        self.declare_parameter('speed_tolerance', 0.50)

        # SEARCH parameters
        self.declare_parameter('search_yaw_rate_deg_s', 10.0)
        self.declare_parameter('search_timeout', 45.0)

        # Detection gate
        self.declare_parameter('detection_window', 10)
        self.declare_parameter('detection_required', 6)
        self.declare_parameter('detection_stale_timeout', 0.5)

        # DETECT confirmation time
        self.declare_parameter('detect_confirm_duration', 1.0)

        # APPROACH parameters
        #
        # First version uses image-based visual servoing:
        #   horizontal pixel error -> yaw correction
        #   area_ratio             -> approach stop condition
        #
        # Vertical image error is intentionally not used yet.
        self.declare_parameter('approach_yaw_kp', 0.8)
        self.declare_parameter('approach_max_yaw_rate_deg_s', 20.0)
        self.declare_parameter('approach_yaw_deadband', 0.08)
        self.declare_parameter('approach_heading_tolerance_deg', 8.0)

        self.declare_parameter('approach_forward_speed', 0.30)
        self.declare_parameter('approach_slow_area_ratio', 0.012)
        self.declare_parameter('approach_slow_speed', 0.12)
        self.declare_parameter('done_exit_delay', 1.0)
        self.declare_parameter('approach_max_setpoint_lead', 0.60)

        # Conservative first-test threshold.
        # This is an apparent-size trigger, NOT a calibrated distance.
        self.declare_parameter('approach_stop_area_ratio', 0.020)

        self.declare_parameter('approach_target_lost_timeout', 0.8)
        self.declare_parameter('approach_timeout', 30.0)

        self.target_height = float(
            self.get_parameter('target_height').value
        )

        self.hover_duration = float(
            self.get_parameter('hover_duration').value
        )

        self.hold_duration = float(
            self.get_parameter('hold_duration').value
        )

        self.position_tolerance = float(
            self.get_parameter('position_tolerance').value
        )

        self.vertical_tolerance = float(
            self.get_parameter('vertical_tolerance').value
        )

        self.speed_tolerance = float(
            self.get_parameter('speed_tolerance').value
        )

        self.search_yaw_rate = math.radians(
            float(
                self.get_parameter(
                    'search_yaw_rate_deg_s'
                ).value
            )
        )

        self.search_timeout = float(
            self.get_parameter('search_timeout').value
        )

        self.detection_window = int(
            self.get_parameter('detection_window').value
        )

        self.detection_required = int(
            self.get_parameter('detection_required').value
        )

        self.detection_stale_timeout = float(
            self.get_parameter('detection_stale_timeout').value
        )

        self.detect_confirm_duration = float(
            self.get_parameter('detect_confirm_duration').value
        )

        self.approach_yaw_kp = float(
            self.get_parameter('approach_yaw_kp').value
        )

        self.approach_max_yaw_rate = math.radians(
            float(
                self.get_parameter(
                    'approach_max_yaw_rate_deg_s'
                ).value
            )
        )

        self.approach_yaw_deadband = float(
            self.get_parameter('approach_yaw_deadband').value
        )

        self.approach_heading_tolerance = math.radians(
            float(
                self.get_parameter(
                    'approach_heading_tolerance_deg'
                ).value
            )
        )

        self.approach_forward_speed = float(
            self.get_parameter('approach_forward_speed').value
        )

        self.approach_slow_area_ratio = float(
            self.get_parameter('approach_slow_area_ratio').value
        )

        self.approach_slow_speed = float(
            self.get_parameter('approach_slow_speed').value
        )

        self.done_exit_delay = float(
            self.get_parameter('done_exit_delay').value
        )

        self.approach_max_setpoint_lead = float(
            self.get_parameter('approach_max_setpoint_lead').value
        )

        self.approach_stop_area_ratio = float(
            self.get_parameter('approach_stop_area_ratio').value
        )

        self.approach_target_lost_timeout = float(
            self.get_parameter('approach_target_lost_timeout').value
        )

        self.approach_timeout = float(
            self.get_parameter('approach_timeout').value
        )

        if self.detection_window <= 0:
            raise ValueError('detection_window must be > 0')

        if (
            self.detection_required <= 0
            or self.detection_required > self.detection_window
        ):
            raise ValueError(
                'detection_required must be in [1, detection_window]'
            )

        # =========================================================
        # QoS
        # =========================================================

        self.px4_output_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self.px4_input_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
        )

        # =========================================================
        # ROS2 -> PX4
        # =========================================================

        self.offboard_control_mode_pub = self.create_publisher(
            OffboardControlMode,
            '/fmu/in/offboard_control_mode',
            self.px4_input_qos,
        )

        self.trajectory_setpoint_pub = self.create_publisher(
            TrajectorySetpoint,
            '/fmu/in/trajectory_setpoint',
            self.px4_input_qos,
        )

        self.vehicle_command_pub = self.create_publisher(
            VehicleCommand,
            '/fmu/in/vehicle_command',
            self.px4_input_qos,
        )

        # =========================================================
        # Mission telemetry -> ROS2
        # =========================================================

        self.mission_state_pub = self.create_publisher(
            String,
            '/mission/state',
            10,
        )

        self.mission_event_pub = self.create_publisher(
            String,
            '/mission/event',
            10,
        )

        # =========================================================
        # PX4 -> ROS2
        # =========================================================

        self.vehicle_status_sub = self.create_subscription(
            VehicleStatus,
            '/fmu/out/vehicle_status_v1',
            self.vehicle_status_callback,
            self.px4_output_qos,
        )

        self.local_position_sub = self.create_subscription(
            VehicleLocalPosition,
            '/fmu/out/vehicle_local_position_v1',
            self.local_position_callback,
            self.px4_output_qos,
        )

        self.command_ack_sub = self.create_subscription(
            VehicleCommandAck,
            '/fmu/out/vehicle_command_ack',
            self.command_ack_callback,
            self.px4_output_qos,
        )

        self.land_detected_sub = self.create_subscription(
            VehicleLandDetected,
            '/fmu/out/vehicle_land_detected',
            self.land_detected_callback,
            self.px4_output_qos,
        )

        # =========================================================
        # Perception -> Mission
        # =========================================================

        self.target_detection_sub = self.create_subscription(
            TargetDetection,
            '/perception/target',
            self.target_detection_callback,
            10,
        )

        # =========================================================
        # PX4 state
        # =========================================================

        self.vehicle_status = None
        self.local_position = None
        self.land_detected = None

        # =========================================================
        # Perception state
        # =========================================================

        self.latest_detection = None
        self.last_detection_msg_time = -100.0
        self.last_target_seen_time = -100.0

        self.detection_history = deque(
            maxlen=self.detection_window
        )

        # =========================================================
        # Mission state
        # =========================================================

        self.state = MissionState.WAIT_FOR_PX4
        self.state_enter_time = self.now_s()

        self.timer_tick = 0
        self.done_exit_deadline = None
        self.prestream_tick = 0
        self.last_command_time = -100.0

        # =========================================================
        # Home / mission targets
        # =========================================================

        self.home_x = None
        self.home_y = None
        self.home_z = None
        self.home_yaw = 0.0

        self.takeoff_z = None

        # SEARCH anchor.
        # Initial search uses the takeoff point. If APPROACH loses
        # the target, SEARCH can restart around the current position.
        self.search_x = None
        self.search_y = None
        self.search_z = None

        self.target_x = 0.0
        self.target_y = 0.0
        self.target_z = 0.0
        self.target_yaw = 0.0

        # =========================================================
        # Timer
        # =========================================================

        self.timer = self.create_timer(
            self.TIMER_PERIOD,
            self.timer_callback,
        )

        self.get_logger().info(
            'PX4 Perception Mission State Machine started.'
        )

        self.get_logger().info(
            'Mission: Takeoff -> Hover -> Search -> Detect '
            '-> Approach -> Hold -> Return -> Land'
        )

        self.get_logger().info(
            f'Takeoff height : {self.target_height:.1f} m'
        )

        self.get_logger().info(
            f'Search yaw rate: '
            f'{math.degrees(self.search_yaw_rate):.1f} deg/s'
        )

        self.get_logger().info(
            f'Detection gate : '
            f'{self.detection_required}/'
            f'{self.detection_window} frames'
        )

        self.get_logger().info(
            f'Approach stop  : '
            f'area_ratio >= {self.approach_stop_area_ratio:.3f}'
        )

        self.get_logger().info(
            f'Approach speed : '
            f'{self.approach_forward_speed:.2f} m/s '
            f'(position-setpoint ramp)'
        )

        self.get_logger().info(
            f'Approach slow  : area >= '
            f'{self.approach_slow_area_ratio:.3f} -> '
            f'{self.approach_slow_speed:.2f} m/s'
        )

    # =============================================================
    # Time helpers
    # =============================================================

    def now_s(self):
        return self.get_clock().now().nanoseconds / 1e9

    def timestamp_us(self):
        return int(self.get_clock().now().nanoseconds / 1000)

    def time_in_state(self):
        return self.now_s() - self.state_enter_time

    # =============================================================
    # Angle helper
    # =============================================================

    @staticmethod
    def wrap_pi(angle):
        return (angle + math.pi) % (2.0 * math.pi) - math.pi

    # =============================================================
    # Mission telemetry helpers
    # =============================================================

    def publish_mission_state(self):

        msg = String()
        msg.data = self.state.name
        self.mission_state_pub.publish(msg)

    def publish_mission_event(self, event):

        msg = String()
        msg.data = str(event)
        self.mission_event_pub.publish(msg)

    # =============================================================
    # State transition
    # =============================================================

    def transition_to(self, new_state):

        old_state = self.state

        self.state = new_state
        self.state_enter_time = self.now_s()

        # SEARCH only uses detections collected during this search.
        if new_state == MissionState.SEARCH:
            self.detection_history.clear()

        self.get_logger().info('')
        self.get_logger().info(
            '========================================'
        )

        self.publish_mission_state()

        if new_state == MissionState.DONE:
            self.publish_mission_event('MISSION_DONE')
            self.done_exit_deadline = (
                self.now_s() + self.done_exit_delay
            )
        self.get_logger().info(
            f'MISSION STATE: {old_state.name} -> {new_state.name}'
        )
        self.get_logger().info(
            '========================================'
        )

    # =============================================================
    # PX4 callbacks
    # =============================================================

    def vehicle_status_callback(self, msg):
        self.vehicle_status = msg

    def local_position_callback(self, msg):
        self.local_position = msg

    def land_detected_callback(self, msg):
        self.land_detected = msg

    def target_detection_callback(self, msg):
        self.latest_detection = msg
        self.last_detection_msg_time = self.now_s()

        detected = bool(msg.detected)
        self.detection_history.append(detected)

        if detected:
            self.last_target_seen_time = self.now_s()

    def command_ack_callback(self, msg):

        result_names = {
            VehicleCommandAck.VEHICLE_CMD_RESULT_ACCEPTED:
                'ACCEPTED',
            VehicleCommandAck.VEHICLE_CMD_RESULT_TEMPORARILY_REJECTED:
                'TEMPORARILY_REJECTED',
            VehicleCommandAck.VEHICLE_CMD_RESULT_DENIED:
                'DENIED',
            VehicleCommandAck.VEHICLE_CMD_RESULT_UNSUPPORTED:
                'UNSUPPORTED',
            VehicleCommandAck.VEHICLE_CMD_RESULT_FAILED:
                'FAILED',
            VehicleCommandAck.VEHICLE_CMD_RESULT_IN_PROGRESS:
                'IN_PROGRESS',
            VehicleCommandAck.VEHICLE_CMD_RESULT_CANCELLED:
                'CANCELLED',
        }

        result = result_names.get(
            msg.result,
            f'UNKNOWN({msg.result})'
        )

        self.get_logger().info(
            f'Command ACK: command={msg.command}, result={result}'
        )

    # =============================================================
    # Perception helpers
    # =============================================================

    def detection_stream_fresh(self):
        return (
            self.latest_detection is not None
            and (
                self.now_s() - self.last_detection_msg_time
            ) <= self.detection_stale_timeout
        )

    def stable_detection(self):

        if not self.detection_stream_fresh():
            return False

        if len(self.detection_history) < self.detection_window:
            return False

        positive_count = sum(
            1
            for detected in self.detection_history
            if detected
        )

        return positive_count >= self.detection_required

    def target_currently_visible(self):

        if not self.detection_stream_fresh():
            return False

        return bool(self.latest_detection.detected)

    def target_seen_recently(self, timeout):

        return (
            self.now_s() - self.last_target_seen_time
        ) <= timeout

    # =============================================================
    # Mission initialization
    # =============================================================

    def initialize_mission(self):

        if self.local_position is None:
            return False

        if not self.local_position.xy_valid:
            return False

        if not self.local_position.z_valid:
            return False

        self.home_x = float(self.local_position.x)
        self.home_y = float(self.local_position.y)
        self.home_z = float(self.local_position.z)

        # NED z points downward.
        self.takeoff_z = self.home_z - self.target_height

        if math.isfinite(self.local_position.heading):
            self.home_yaw = float(self.local_position.heading)
        else:
            self.home_yaw = 0.0

        self.set_target(
            self.home_x,
            self.home_y,
            self.takeoff_z,
            yaw=self.home_yaw,
        )

        self.search_x = self.home_x
        self.search_y = self.home_y
        self.search_z = self.takeoff_z

        self.get_logger().info('Mission initialized.')

        self.get_logger().info(
            f'Home NED: '
            f'({self.home_x:.2f}, '
            f'{self.home_y:.2f}, '
            f'{self.home_z:.2f})'
        )

        self.get_logger().info(
            f'Takeoff point: '
            f'({self.home_x:.2f}, '
            f'{self.home_y:.2f}, '
            f'{self.takeoff_z:.2f})'
        )

        self.get_logger().info(
            f'Home yaw: {math.degrees(self.home_yaw):.1f} deg'
        )

        return True

    # =============================================================
    # Target helpers
    # =============================================================

    def set_target(self, x, y, z, yaw=None):

        self.target_x = float(x)
        self.target_y = float(y)
        self.target_z = float(z)

        if yaw is None:
            self.target_yaw = self.home_yaw
        else:
            self.target_yaw = self.wrap_pi(float(yaw))

    def hold_current_xy(self):

        if self.local_position is None:
            return

        self.target_x = float(self.local_position.x)
        self.target_y = float(self.local_position.y)

    def set_search_anchor_from_current(self):

        if self.local_position is None:
            return

        self.search_x = float(self.local_position.x)
        self.search_y = float(self.local_position.y)
        self.search_z = float(self.takeoff_z)

        self.target_x = self.search_x
        self.target_y = self.search_y
        self.target_z = self.search_z

    def advance_approach_setpoint(self, speed=None):

        if self.local_position is None:
            return

        # Increment the position setpoint along the current yaw.
        # This approximates a slow forward motion while keeping
        # Offboard in position-control mode.
        if speed is None:
            speed = self.approach_forward_speed

        step = (
            float(speed)
            * self.TIMER_PERIOD
        )

        proposed_x = (
            self.target_x
            + step * math.cos(self.target_yaw)
        )

        proposed_y = (
            self.target_y
            + step * math.sin(self.target_yaw)
        )

        # Prevent the commanded position from running too far ahead
        # of the real vehicle if the controller cannot keep up.
        lead_x = proposed_x - self.local_position.x
        lead_y = proposed_y - self.local_position.y
        lead = math.sqrt(
            lead_x * lead_x
            + lead_y * lead_y
        )

        if (
            lead > self.approach_max_setpoint_lead
            and lead > 1e-6
        ):
            scale = (
                self.approach_max_setpoint_lead
                / lead
            )

            proposed_x = (
                self.local_position.x
                + lead_x * scale
            )

            proposed_y = (
                self.local_position.y
                + lead_y * scale
            )

        self.target_x = float(proposed_x)
        self.target_y = float(proposed_y)
        self.target_z = float(self.takeoff_z)

    def reached_target(self):

        if self.local_position is None:
            return False

        dx = self.local_position.x - self.target_x
        dy = self.local_position.y - self.target_y
        dz = self.local_position.z - self.target_z

        horizontal_error = math.sqrt(dx * dx + dy * dy)
        vertical_error = abs(dz)

        vx = self.local_position.vx
        vy = self.local_position.vy
        vz = self.local_position.vz

        speed = math.sqrt(
            vx * vx + vy * vy + vz * vz
        )

        return (
            horizontal_error < self.position_tolerance
            and vertical_error < self.vertical_tolerance
            and speed < self.speed_tolerance
        )

    # =============================================================
    # Offboard publishers
    # =============================================================

    def publish_offboard_control_mode(self):

        msg = OffboardControlMode()
        msg.timestamp = self.timestamp_us()

        msg.position = True
        msg.velocity = False
        msg.acceleration = False
        msg.attitude = False
        msg.body_rate = False
        msg.thrust_and_torque = False
        msg.direct_actuator = False

        self.offboard_control_mode_pub.publish(msg)

    def publish_trajectory_setpoint(self):

        msg = TrajectorySetpoint()
        msg.timestamp = self.timestamp_us()

        msg.position = [
            self.target_x,
            self.target_y,
            self.target_z,
        ]

        nan = float('nan')

        msg.velocity = [nan, nan, nan]
        msg.acceleration = [nan, nan, nan]
        msg.jerk = [nan, nan, nan]

        msg.yaw = self.target_yaw
        msg.yawspeed = nan

        self.trajectory_setpoint_pub.publish(msg)

    def publish_offboard_stream(self):
        self.publish_offboard_control_mode()
        self.publish_trajectory_setpoint()

    # =============================================================
    # VehicleCommand
    # =============================================================

    def publish_vehicle_command(
        self,
        command,
        param1=0.0,
        param2=0.0,
    ):

        msg = VehicleCommand()
        msg.timestamp = self.timestamp_us()

        msg.param1 = float(param1)
        msg.param2 = float(param2)
        msg.param3 = 0.0
        msg.param4 = 0.0
        msg.param5 = 0.0
        msg.param6 = 0.0
        msg.param7 = 0.0

        msg.command = command

        msg.target_system = 1
        msg.target_component = 1
        msg.source_system = 1
        msg.source_component = 1
        msg.confirmation = 0
        msg.from_external = True

        self.vehicle_command_pub.publish(msg)

    def request_offboard(self):

        self.get_logger().info('Requesting OFFBOARD mode...')

        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_DO_SET_MODE,
            param1=1.0,
            param2=6.0,
        )

    def request_arm(self):

        self.get_logger().info('Requesting ARM...')

        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,
            param1=1.0,
        )

    def request_disarm(self):

        self.get_logger().info('Requesting DISARM...')

        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_COMPONENT_ARM_DISARM,
            param1=0.0,
        )

    def request_land(self):

        self.get_logger().info('Requesting AUTO LAND...')

        self.publish_vehicle_command(
            VehicleCommand.VEHICLE_CMD_NAV_LAND,
        )

    # =============================================================
    # Command throttling
    # =============================================================

    def command_retry_ready(self):

        now = self.now_s()

        if (
            now - self.last_command_time
            >= self.COMMAND_RETRY_INTERVAL
        ):
            self.last_command_time = now
            return True

        return False

    # =============================================================
    # Status printing
    # =============================================================

    def print_status(self):

        if self.local_position is None:
            return

        detection_text = 'NO_DATA'

        if self.detection_stream_fresh():
            if self.latest_detection.detected:
                detection_text = (
                    'YES '
                    f'ex={self.latest_detection.center_u_norm:+.3f} '
                    f'area={self.latest_detection.area_ratio:.4f}'
                )
            else:
                detection_text = 'NO'

        self.get_logger().info(
            f'STATE={self.state.name} | '
            f'POS=('
            f'{self.local_position.x:.2f}, '
            f'{self.local_position.y:.2f}, '
            f'{self.local_position.z:.2f}) | '
            f'YAW_SP={math.degrees(self.target_yaw):.1f} deg | '
            f'TARGET_DETECTED={detection_text}'
        )

    # =============================================================
    # Main FSM
    # =============================================================

    def timer_callback(self):

        self.timer_tick += 1

        # =========================================================
        # WAIT_FOR_PX4
        # =========================================================

        if self.state == MissionState.WAIT_FOR_PX4:

            if (
                self.vehicle_status is None
                or self.local_position is None
            ):
                if self.timer_tick % 10 == 0:
                    self.get_logger().warning(
                        'Waiting for PX4 telemetry...'
                    )
                return

            if not self.initialize_mission():
                if self.timer_tick % 10 == 0:
                    self.get_logger().warning(
                        'Waiting for valid local position...'
                    )
                return

            self.transition_to(MissionState.PRESTREAM)
            return

        # =========================================================
        # PRESTREAM
        # =========================================================

        if self.state == MissionState.PRESTREAM:

            self.publish_offboard_stream()
            self.prestream_tick += 1

            if self.prestream_tick == 1:
                self.get_logger().info(
                    'Starting Offboard pre-stream...'
                )

            if self.prestream_tick < self.PRESTREAM_TICKS:
                return

            if not self.vehicle_status.pre_flight_checks_pass:
                if self.timer_tick % 10 == 0:
                    self.get_logger().warning(
                        'PX4 pre-flight checks have not passed.'
                    )
                return

            self.transition_to(MissionState.REQUEST_OFFBOARD)
            return

        # =========================================================
        # REQUEST_OFFBOARD
        # =========================================================

        if self.state == MissionState.REQUEST_OFFBOARD:

            self.publish_offboard_stream()

            if (
                self.vehicle_status.nav_state
                == VehicleStatus.NAVIGATION_STATE_OFFBOARD
            ):
                self.transition_to(MissionState.ARMING)
                return

            if self.command_retry_ready():
                self.request_offboard()

            return

        # =========================================================
        # ARMING
        # =========================================================

        if self.state == MissionState.ARMING:

            self.publish_offboard_stream()

            if (
                self.vehicle_status.arming_state
                == VehicleStatus.ARMING_STATE_ARMED
            ):
                self.transition_to(MissionState.TAKEOFF)
                return

            if self.command_retry_ready():
                self.request_arm()

            return

        # =========================================================
        # TAKEOFF
        # =========================================================

        if self.state == MissionState.TAKEOFF:

            self.publish_offboard_stream()

            if self.reached_target():
                self.get_logger().info(
                    'Takeoff altitude reached.'
                )
                self.transition_to(MissionState.HOVER)
                return

        # =========================================================
        # HOVER
        # =========================================================

        elif self.state == MissionState.HOVER:

            self.publish_offboard_stream()

            if self.time_in_state() >= self.hover_duration:

                self.search_x = self.home_x
                self.search_y = self.home_y
                self.search_z = self.takeoff_z

                self.set_target(
                    self.search_x,
                    self.search_y,
                    self.search_z,
                    yaw=self.target_yaw,
                )

                self.get_logger().info(
                    'Starting visual target search.'
                )

                self.transition_to(MissionState.SEARCH)
                return

        # =========================================================
        # SEARCH
        # Hold XYZ and continuously sweep yaw.
        # =========================================================

        elif self.state == MissionState.SEARCH:

            self.target_x = self.search_x
            self.target_y = self.search_y
            self.target_z = self.search_z

            self.target_yaw = self.wrap_pi(
                self.target_yaw
                + self.search_yaw_rate * self.TIMER_PERIOD
            )

            self.publish_offboard_stream()

            if self.stable_detection():

                self.get_logger().info(
                    'Stable target detection acquired.'
                )

                if self.latest_detection is not None:
                    self.get_logger().info(
                        'Detection at SEARCH exit: '
                        f'ex={self.latest_detection.center_u_norm:+.3f}, '
                        f'ey={self.latest_detection.center_v_norm:+.3f}, '
                        f'area={self.latest_detection.area_ratio:.4f}'
                    )

                # target_yaw is now frozen because DETECT does not
                # update it anymore.
                self.transition_to(MissionState.DETECT)
                return

            if self.time_in_state() >= self.search_timeout:

                self.get_logger().warning(
                    'SEARCH timeout. Target was not found.'
                )

                self.publish_mission_event('SEARCH_TIMEOUT')

                self.set_target(
                    self.home_x,
                    self.home_y,
                    self.takeoff_z,
                    yaw=self.home_yaw,
                )

                self.transition_to(MissionState.RETURN)
                return

        # =========================================================
        # DETECT
        # Freeze position/yaw and confirm target for a short time.
        # =========================================================

        elif self.state == MissionState.DETECT:

            self.publish_offboard_stream()

            if not self.target_currently_visible():

                self.get_logger().warning(
                    'Target lost during DETECT. '
                    'Returning to SEARCH.'
                )

                self.publish_mission_event('DETECT_LOST')

                self.transition_to(MissionState.SEARCH)
                return

            if self.time_in_state() >= self.detect_confirm_duration:

                if self.stable_detection():

                    self.get_logger().info(
                        'TARGET CONFIRMED.'
                    )

                    self.get_logger().info(
                        'Target confirmed. Starting visual approach.'
                    )

                    # Start APPROACH from the current vehicle position.
                    self.hold_current_xy()
                    self.target_z = self.takeoff_z

                    self.transition_to(MissionState.APPROACH)
                    return

                self.get_logger().warning(
                    'Detection was not stable during '
                    'confirmation. Returning to SEARCH.'
                )

                self.transition_to(MissionState.SEARCH)
                return

        # =========================================================
        # APPROACH
        #
        # First-version image-based visual servoing:
        #
        #   ex < 0  -> target is left  -> decrease yaw
        #   ex > 0  -> target is right -> increase yaw
        #
        # The sign relationship above was experimentally verified.
        #
        # If |ex| is large:
        #   rotate only, do not advance.
        #
        # If |ex| is small and the body heading has caught up:
        #   advance the position setpoint slowly along current yaw.
        #
        # Stop when target apparent area reaches the configured
        # threshold. Vertical image error is ignored in V1.
        # =========================================================

        elif self.state == MissionState.APPROACH:

            if self.latest_detection is None:
                self.publish_offboard_stream()
                return

            # -----------------------------------------------------
            # Mission timeout
            # -----------------------------------------------------

            if self.time_in_state() >= self.approach_timeout:

                self.get_logger().warning(
                    'APPROACH timeout. Returning home.'
                )

                self.publish_mission_event('APPROACH_TIMEOUT')

                self.set_target(
                    self.home_x,
                    self.home_y,
                    self.takeoff_z,
                    yaw=self.home_yaw,
                )

                self.transition_to(MissionState.RETURN)
                return

            # -----------------------------------------------------
            # Target loss
            # -----------------------------------------------------

            if not self.target_seen_recently(
                self.approach_target_lost_timeout
            ):

                self.get_logger().warning(
                    'Target lost during APPROACH. '
                    'Stopping and restarting SEARCH '
                    'from current position.'
                )

                self.publish_mission_event('APPROACH_TARGET_LOST')

                self.set_search_anchor_from_current()

                self.transition_to(MissionState.SEARCH)
                return

            # -----------------------------------------------------
            # Use latest valid target observation
            # -----------------------------------------------------

            if self.target_currently_visible():

                ex = float(
                    self.latest_detection.center_u_norm
                )

                area_ratio = float(
                    self.latest_detection.area_ratio
                )

                # -------------------------------------------------
                # Stop condition
                # -------------------------------------------------

                if (
                    area_ratio
                    >= self.approach_stop_area_ratio
                ):

                    self.hold_current_xy()
                    self.target_z = self.takeoff_z

                    self.get_logger().info(
                        'APPROACH SUCCESS | '
                        f'area={area_ratio:.4f} >= '
                        f'{self.approach_stop_area_ratio:.4f}'
                    )

                    self.publish_mission_event('APPROACH_SUCCESS')

                    self.transition_to(
                        MissionState.HOLD
                    )

                    return

                # -------------------------------------------------
                # Horizontal visual servo: ex -> yaw rate
                # -------------------------------------------------

                if (
                    abs(ex)
                    > self.approach_yaw_deadband
                ):

                    # Brake translation while re-centering target.
                    self.hold_current_xy()

                    yaw_rate_cmd = (
                        self.approach_yaw_kp
                        * ex
                    )

                    yaw_rate_cmd = max(
                        -self.approach_max_yaw_rate,
                        min(
                            self.approach_max_yaw_rate,
                            yaw_rate_cmd,
                        ),
                    )

                    self.target_yaw = self.wrap_pi(
                        self.target_yaw
                        + yaw_rate_cmd
                        * self.TIMER_PERIOD
                    )

                else:

                    # Target is horizontally centered.
                    # Wait for the real body heading to catch up
                    # before commanding forward motion.
                    heading_ready = True

                    if (
                        self.local_position is not None
                        and math.isfinite(
                            self.local_position.heading
                        )
                    ):

                        heading_error = self.wrap_pi(
                            self.target_yaw
                            - float(
                                self.local_position.heading
                            )
                        )

                        heading_ready = (
                            abs(heading_error)
                            <= self.approach_heading_tolerance
                        )

                    if heading_ready:
                        forward_speed = self.approach_forward_speed

                        if (
                            area_ratio
                            >= self.approach_slow_area_ratio
                        ):
                            forward_speed = self.approach_slow_speed

                        self.advance_approach_setpoint(
                            speed=forward_speed
                        )

            # If one frame is negative but still within the target-loss
            # grace period, simply hold the last setpoint.
            self.publish_offboard_stream()

        # =========================================================
        # HOLD
        # Hold the successful approach pose briefly, then return home.
        # =========================================================

        elif self.state == MissionState.HOLD:

            self.publish_offboard_stream()

            if self.time_in_state() >= self.hold_duration:

                self.set_target(
                    self.home_x,
                    self.home_y,
                    self.takeoff_z,
                    yaw=self.home_yaw,
                )

                self.get_logger().info(
                    'Approach test complete. '
                    'Returning to home position.'
                )

                self.transition_to(MissionState.RETURN)
                return

        # =========================================================
        # RETURN
        # =========================================================

        elif self.state == MissionState.RETURN:

            self.publish_offboard_stream()

            if self.reached_target():

                self.get_logger().info(
                    'Returned above home position.'
                )

                self.transition_to(MissionState.LAND)
                return

        # =========================================================
        # LAND
        # =========================================================

        elif self.state == MissionState.LAND:

            if (
                self.vehicle_status.nav_state
                != VehicleStatus.NAVIGATION_STATE_AUTO_LAND
            ):

                self.publish_offboard_stream()

                if self.command_retry_ready():
                    self.request_land()

            if (
                self.land_detected is not None
                and self.land_detected.landed
            ):

                self.get_logger().info(
                    'Landing detector reports LANDED.'
                )

                if (
                    self.vehicle_status.arming_state
                    == VehicleStatus.ARMING_STATE_ARMED
                ):

                    if self.command_retry_ready():
                        self.request_disarm()

                    return

                self.transition_to(MissionState.DONE)
                return

        # =========================================================
        # DONE
        # =========================================================

        elif self.state == MissionState.DONE:

            if (
                self.done_exit_deadline is not None
                and self.now_s() >= self.done_exit_deadline
            ):
                self.get_logger().info(
                    'Mission complete. Vehicle landed and disarmed. '
                    'Mission controller is exiting.'
                )

                self.timer.cancel()

                if rclpy.ok():
                    rclpy.shutdown()

            return

        # =========================================================
        # Once-per-second mission telemetry
        # =========================================================

        if self.timer_tick % 10 == 0:
            self.publish_mission_state()
            self.print_status()


def main(args=None):

    rclpy.init(args=args)

    node = PX4OffboardController()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        node.get_logger().warning(
            'Mission node interrupted.'
        )

    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
