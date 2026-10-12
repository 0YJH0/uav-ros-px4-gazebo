import sys

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from uav_interfaces.action import FlyToAltitude


class FlyToAltitudeClient(Node):

    def __init__(self):
        super().__init__('fly_to_altitude_client')

        self.action_client = ActionClient(
            self,
            FlyToAltitude,
            'uav/fly_to_altitude'
        )

    def send_goal(self, target_altitude):

        goal_msg = FlyToAltitude.Goal()

        goal_msg.target_altitude = (
            target_altitude
        )

        self.action_client.wait_for_server()

        self.get_logger().info(
            f'Sending target altitude: '
            f'{target_altitude:.1f} m'
        )

        send_goal_future = (
            self.action_client.send_goal_async(
                goal_msg,
                feedback_callback=
                self.feedback_callback
            )
        )

        send_goal_future.add_done_callback(
            self.goal_response_callback
        )

    def goal_response_callback(self, future):

        goal_handle = future.result()

        if not goal_handle.accepted:

            self.get_logger().info(
                'Goal rejected.'
            )

            return

        self.get_logger().info(
            'Goal accepted.'
        )

        result_future = (
            goal_handle.get_result_async()
        )

        result_future.add_done_callback(
            self.result_callback
        )

    def feedback_callback(self, feedback_msg):

        feedback = feedback_msg.feedback

        self.get_logger().info(
            f'Feedback altitude: '
            f'{feedback.current_altitude:.1f} m'
        )

    def result_callback(self, future):

        result = future.result().result

        self.get_logger().info(
            f'Result success: {result.success}'
        )

        self.get_logger().info(
            f'Result message: {result.message}'
        )


def main(args=None):

    rclpy.init(args=args)

    node = FlyToAltitudeClient()

    target_altitude = 10.0

    if len(sys.argv) > 1:
        target_altitude = float(sys.argv[1])

    node.send_goal(target_altitude)

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()