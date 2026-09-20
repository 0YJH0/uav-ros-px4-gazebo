import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class StatusPublisher(Node):

    def __init__(self):
        super().__init__('status_publisher')

        self.publisher_ = self.create_publisher(
            String,
            '/uav/status',
            10
        )

        self.timer = self.create_timer(
            1.0,
            self.timer_callback
        )

        self.get_logger().info('Status publisher started.')

    def timer_callback(self):
        msg = String()
        msg.data = 'UAV system alive'

        self.publisher_.publish(msg)

        self.get_logger().info(
            f'Publishing: "{msg.data}"'
        )


def main(args=None):
    rclpy.init(args=args)

    node = StatusPublisher()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()