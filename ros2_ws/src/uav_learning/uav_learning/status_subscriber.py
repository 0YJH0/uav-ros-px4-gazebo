import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class StatusSubscriber(Node):

    def __init__(self):
        super().__init__('status_subscriber')

        self.subscription = self.create_subscription(
            String,
            '/uav/status',
            self.status_callback,
            10
        )

        self.get_logger().info('Status subscriber started.')

    def status_callback(self, msg):
        self.get_logger().info(
            f'Received: "{msg.data}"'
        )


def main(args=None):
    rclpy.init(args=args)

    node = StatusSubscriber()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
