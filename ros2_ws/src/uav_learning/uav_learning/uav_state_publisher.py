import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32
from std_msgs.msg import String


class UAVStatePublisher(Node):

    def __init__(self):
        super().__init__('uav_state_publisher')

        # 高度 Publisher
        self.altitude_publisher = self.create_publisher(
            Float32,
            'uav/altitude',
            10
        )

        # 飞行模式 Publisher
        self.mode_publisher = self.create_publisher(
            String,
            'uav/mode',
            10
        )

        # 模拟状态
        self.altitude = 0.0
        self.mode = 'IDLE'

        # 1 Hz 定时器
        self.timer = self.create_timer(
            1.0,
            self.timer_callback
        )

        self.get_logger().info(
            'UAV state publisher started.'
        )

    def timer_callback(self):

        # 模拟无人机起飞
        self.altitude += 1.0

        if self.altitude < 3.0:
            self.mode = 'TAKEOFF'
        elif self.altitude < 10.0:
            self.mode = 'CLIMB'
        else:
            self.mode = 'HOVER'

        # 发布高度
        altitude_msg = Float32()
        altitude_msg.data = self.altitude

        self.altitude_publisher.publish(
            altitude_msg
        )

        # 发布模式
        mode_msg = String()
        mode_msg.data = self.mode

        self.mode_publisher.publish(
            mode_msg
        )

        self.get_logger().info(
            f'Altitude: {self.altitude:.1f} m, '
            f'Mode: {self.mode}'
        )


def main(args=None):

    rclpy.init(args=args)

    node = UAVStatePublisher()

    rclpy.spin(node)

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()