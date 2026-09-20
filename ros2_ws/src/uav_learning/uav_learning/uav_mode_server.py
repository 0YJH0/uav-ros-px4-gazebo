import rclpy
from rclpy.node import Node

from std_msgs.msg import String

from uav_interfaces.srv import SetMode


class UAVModeServer(Node):

    def __init__(self):
        super().__init__('uav_mode_server')

        # 创建 Service
        self.service = self.create_service(
            SetMode,
            'uav/set_mode',
            self.set_mode_callback
        )

        # 模式状态 Publisher
        self.mode_publisher = self.create_publisher(
            String,
            'uav/mode',
            10
        )

        self.current_mode = 'IDLE'

        self.allowed_modes = {
            'IDLE',
            'TAKEOFF',
            'CLIMB',
            'HOVER',
            'OFFBOARD',
            'LAND'
        }

        self.get_logger().info(
            'UAV mode service started.'
        )

    def set_mode_callback(self, request, response):

        requested_mode = request.mode.upper()

        self.get_logger().info(
            f'Requested mode: {requested_mode}'
        )

        if requested_mode in self.allowed_modes:

            self.current_mode = requested_mode

            response.success = True
            response.message = (
                f'Mode changed to {self.current_mode}'
            )

            mode_msg = String()
            mode_msg.data = self.current_mode

            self.mode_publisher.publish(mode_msg)

        else:

            response.success = False

            response.message = (
                f'Invalid mode: {requested_mode}'
            )

        return response


def main(args=None):

    rclpy.init(args=args)

    node = UAVModeServer()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()