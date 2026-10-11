import time

import rclpy
from rclpy.action import ActionServer
from rclpy.node import Node

from uav_interfaces.action import FlyToAltitude


class FlyToAltitudeServer(Node):

    def __init__(self):
        super().__init__('fly_to_altitude_server')

        self.action_server = ActionServer(
            self,
            FlyToAltitude,
            'uav/fly_to_altitude',
            self.execute_callback
        )

        self.get_logger().info(
            'FlyToAltitude action server started.'
        )

    def execute_callback(self, goal_handle):

        target_altitude = (
            goal_handle.request.target_altitude
        )

        self.get_logger().info(
            f'Received target altitude: '
            f'{target_altitude:.1f} m'
        )

        feedback_msg = FlyToAltitude.Feedback()

        current_altitude = 0.0

        while current_altitude < target_altitude:

            current_altitude += 1.0

            feedback_msg.current_altitude = (
                current_altitude
            )

            goal_handle.publish_feedback(
                feedback_msg
            )

            self.get_logger().info(
                f'Current altitude: '
                f'{current_altitude:.1f} m'
            )

            time.sleep(0.5)

        goal_handle.succeed()

        result = FlyToAltitude.Result()

        result.success = True

        result.message = (
            f'Reached target altitude '
            f'{target_altitude:.1f} m'
        )

        return result


def main(args=None):

    rclpy.init(args=args)

    node = FlyToAltitudeServer()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()