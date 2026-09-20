#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from px4_msgs.msg import VehicleLocalPosition
from px4_msgs.msg import VehicleStatus


class UAVStateMonitor(Node):
    """
    Monitor real PX4 vehicle state through ROS 2 / uXRCE-DDS.

    Subscribed topics:
        /fmu/out/vehicle_local_position_v1
        /fmu/out/vehicle_status_v1

    Output:
        Once per second:
        - Position
        - Velocity
        - Heading
        - Arming state
        - Flight mode

    PX4 local coordinate convention:
        NED
        x  -> North
        y  -> East
        z  -> Down

        Therefore:
        altitude relative to local origin ~= -z
    """

    def __init__(self):
        super().__init__('uav_state_monitor')

        # -------------------------------------------------------------
        # Latest PX4 state
        # -------------------------------------------------------------

        self.local_position = None
        self.vehicle_status = None

        # -------------------------------------------------------------
        # PX4 -> ROS 2 subscriptions
        #
        # PX4 publishers use BEST_EFFORT QoS.
        # qos_profile_sensor_data is compatible with PX4 telemetry.
        # -------------------------------------------------------------

        self.local_position_sub = self.create_subscription(
            VehicleLocalPosition,
            '/fmu/out/vehicle_local_position_v1',
            self.local_position_callback,
            qos_profile_sensor_data
        )

        self.vehicle_status_sub = self.create_subscription(
            VehicleStatus,
            '/fmu/out/vehicle_status_v1',
            self.vehicle_status_callback,
            qos_profile_sensor_data
        )

        # -------------------------------------------------------------
        # Print summarized state once per second
        # -------------------------------------------------------------

        self.print_timer = self.create_timer(
            1.0,
            self.print_state
        )

        self.get_logger().info(
            'PX4 UAV State Monitor started.'
        )

        self.get_logger().info(
            'Waiting for PX4 vehicle status and local position...'
        )

    # -----------------------------------------------------------------
    # ROS 2 callbacks
    # -----------------------------------------------------------------

    def local_position_callback(self, msg):
        self.local_position = msg

    def vehicle_status_callback(self, msg):
        self.vehicle_status = msg

    # -----------------------------------------------------------------
    # State decoding
    # -----------------------------------------------------------------

    @staticmethod
    def decode_arming_state(arming_state):
        """
        Convert PX4 arming_state integer into readable text.
        """

        arming_states = {
            VehicleStatus.ARMING_STATE_DISARMED: 'DISARMED',
            VehicleStatus.ARMING_STATE_ARMED: 'ARMED',
        }

        return arming_states.get(
            arming_state,
            f'UNKNOWN({arming_state})'
        )

    @staticmethod
    def decode_nav_state(nav_state):
        """
        Convert PX4 nav_state integer into readable flight-mode text.
        """

        nav_states = {
            VehicleStatus.NAVIGATION_STATE_MANUAL:
                'MANUAL',

            VehicleStatus.NAVIGATION_STATE_ALTCTL:
                'ALTCTL',

            VehicleStatus.NAVIGATION_STATE_POSCTL:
                'POSCTL',

            VehicleStatus.NAVIGATION_STATE_AUTO_MISSION:
                'AUTO_MISSION',

            VehicleStatus.NAVIGATION_STATE_AUTO_LOITER:
                'AUTO_LOITER',

            VehicleStatus.NAVIGATION_STATE_AUTO_RTL:
                'AUTO_RTL',

            VehicleStatus.NAVIGATION_STATE_POSITION_SLOW:
                'POSITION_SLOW',

            VehicleStatus.NAVIGATION_STATE_ALTITUDE_CRUISE:
                'ALTITUDE_CRUISE',

            VehicleStatus.NAVIGATION_STATE_ACRO:
                'ACRO',

            VehicleStatus.NAVIGATION_STATE_DESCEND:
                'DESCEND',

            VehicleStatus.NAVIGATION_STATE_TERMINATION:
                'TERMINATION',

            VehicleStatus.NAVIGATION_STATE_OFFBOARD:
                'OFFBOARD',

            VehicleStatus.NAVIGATION_STATE_STAB:
                'STABILIZED',

            VehicleStatus.NAVIGATION_STATE_AUTO_TAKEOFF:
                'AUTO_TAKEOFF',

            VehicleStatus.NAVIGATION_STATE_AUTO_LAND:
                'AUTO_LAND',

            VehicleStatus.NAVIGATION_STATE_AUTO_FOLLOW_TARGET:
                'AUTO_FOLLOW_TARGET',

            VehicleStatus.NAVIGATION_STATE_AUTO_PRECLAND:
                'AUTO_PRECLAND',

            VehicleStatus.NAVIGATION_STATE_ORBIT:
                'ORBIT',

            VehicleStatus.NAVIGATION_STATE_AUTO_VTOL_TAKEOFF:
                'AUTO_VTOL_TAKEOFF',

            VehicleStatus.NAVIGATION_STATE_EXTERNAL1:
                'EXTERNAL1',

            VehicleStatus.NAVIGATION_STATE_EXTERNAL2:
                'EXTERNAL2',

            VehicleStatus.NAVIGATION_STATE_EXTERNAL3:
                'EXTERNAL3',

            VehicleStatus.NAVIGATION_STATE_EXTERNAL4:
                'EXTERNAL4',

            VehicleStatus.NAVIGATION_STATE_EXTERNAL5:
                'EXTERNAL5',

            VehicleStatus.NAVIGATION_STATE_EXTERNAL6:
                'EXTERNAL6',

            VehicleStatus.NAVIGATION_STATE_EXTERNAL7:
                'EXTERNAL7',

            VehicleStatus.NAVIGATION_STATE_EXTERNAL8:
                'EXTERNAL8',
        }

        return nav_states.get(
            nav_state,
            f'UNKNOWN({nav_state})'
        )

    # -----------------------------------------------------------------
    # Periodic state summary
    # -----------------------------------------------------------------

    def print_state(self):

        # Wait until both PX4 topics have been received.
        if self.local_position is None:
            self.get_logger().warning(
                'Waiting for '
                '/fmu/out/vehicle_local_position_v1 ...'
            )
            return

        if self.vehicle_status is None:
            self.get_logger().warning(
                'Waiting for '
                '/fmu/out/vehicle_status_v1 ...'
            )
            return

        position = self.local_position
        status = self.vehicle_status

        # -------------------------------------------------------------
        # Position
        # -------------------------------------------------------------

        x = position.x
        y = position.y
        z = position.z

        # PX4 NED:
        # z positive downward.
        # Therefore approximate height above local origin is -z.
        altitude = -z

        # -------------------------------------------------------------
        # Velocity
        # -------------------------------------------------------------

        vx = position.vx
        vy = position.vy
        vz = position.vz

        horizontal_speed = math.sqrt(
            vx * vx + vy * vy
        )

        total_speed = math.sqrt(
            vx * vx +
            vy * vy +
            vz * vz
        )

        # -------------------------------------------------------------
        # Heading
        #
        # PX4 gives heading in radians.
        # Convert to degrees for easier observation.
        # -------------------------------------------------------------

        heading_rad = position.heading

        if math.isfinite(heading_rad):
            heading_deg = math.degrees(heading_rad)

            # Convert [-180, 180] style value into [0, 360).
            heading_deg = heading_deg % 360.0

            heading_text = f'{heading_deg:.1f} deg'

        else:
            heading_text = 'INVALID'

        # -------------------------------------------------------------
        # PX4 state
        # -------------------------------------------------------------

        arming_state = self.decode_arming_state(
            status.arming_state
        )

        flight_mode = self.decode_nav_state(
            status.nav_state
        )

        # -------------------------------------------------------------
        # Validity flags
        # -------------------------------------------------------------

        position_valid = (
            position.xy_valid and
            position.z_valid
        )

        velocity_valid = (
            position.v_xy_valid and
            position.v_z_valid
        )

        # -------------------------------------------------------------
        # One-second summarized output
        # -------------------------------------------------------------

        output = (
            '\n'
            '================ PX4 UAV STATE ================\n'
            f'Arming State : {arming_state}\n'
            f'Flight Mode  : {flight_mode}\n'
            f'Failsafe     : {status.failsafe}\n'
            '\n'
            'Position NED [m]\n'
            f'  North (x)  : {x:8.3f}\n'
            f'  East  (y)  : {y:8.3f}\n'
            f'  Down  (z)  : {z:8.3f}\n'
            f'  Altitude   : {altitude:8.3f}\n'
            f'  Valid      : {position_valid}\n'
            '\n'
            'Velocity NED [m/s]\n'
            f'  North (vx) : {vx:8.3f}\n'
            f'  East  (vy) : {vy:8.3f}\n'
            f'  Down  (vz) : {vz:8.3f}\n'
            f'  Horizontal : {horizontal_speed:8.3f}\n'
            f'  Total      : {total_speed:8.3f}\n'
            f'  Valid      : {velocity_valid}\n'
            '\n'
            f'Heading      : {heading_text}\n'
            '================================================'
        )

        self.get_logger().info(output)


def main(args=None):

    rclpy.init(args=args)

    node = UAVStateMonitor()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()