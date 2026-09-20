import sys

import rclpy
from rclpy.node import Node

from uav_interfaces.srv import SetMode


class UAVModeClient(Node):

    def __init__(self):
        super().__init__('uav_mode_client')

        self.client = self.create_client(
            SetMode,
            'uav/set_mode'
        )

        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(
                'Waiting for /uav/set_mode service...'
            )

    def send_request(self, mode):
        request = SetMode.Request()

        request.mode = mode

        return self.client.call_async(request)


def main(args=None):
    rclpy.init(args=args)

    node = UAVModeClient()

    mode = 'OFFBOARD'

    if len(sys.argv) > 1:
        mode = sys.argv[1]

    future = node.send_request(mode)

    rclpy.spin_until_future_complete(
        node,
        future
    )

    response = future.result()

    if response is not None:
        node.get_logger().info(
            f'Success: {response.success}'
        )

        node.get_logger().info(
            f'Message: {response.message}'
        )

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()