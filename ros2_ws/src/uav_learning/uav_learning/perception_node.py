#!/usr/bin/env python3

import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from uav_interfaces.msg import TargetDetection


class PerceptionNode(Node):

    def __init__(self):
        super().__init__('perception_node')

        # --------------------------------------------------------
        # Parameters
        # --------------------------------------------------------
        self.declare_parameter(
            'image_topic',
            '/camera/image_raw'
        )

        self.declare_parameter(
            'min_area_ratio',
            0.0005
        )

        self.image_topic = (
            self.get_parameter('image_topic').value
        )

        self.min_area_ratio = float(
            self.get_parameter('min_area_ratio').value
        )

        # --------------------------------------------------------
        # CV Bridge
        # --------------------------------------------------------
        self.bridge = CvBridge()

        # --------------------------------------------------------
        # Subscriber
        # --------------------------------------------------------
        self.image_sub = self.create_subscription(
            Image,
            self.image_topic,
            self.image_callback,
            qos_profile_sensor_data,
        )

        # --------------------------------------------------------
        # Publishers
        # --------------------------------------------------------
        self.target_pub = self.create_publisher(
            TargetDetection,
            '/perception/target',
            10,
        )

        self.debug_pub = self.create_publisher(
            Image,
            '/perception/debug_image',
            10,
        )

        self.last_log_time = 0.0

        self.get_logger().info(
            'Perception node started.'
        )

        self.get_logger().info(
            f'Image topic: {self.image_topic}'
        )

    def image_callback(self, msg):

        # ========================================================
        # ROS Image -> OpenCV
        # ========================================================
        try:
            image = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding='bgr8',
            )

        except Exception as exc:
            self.get_logger().error(
                f'Image conversion failed: {exc}'
            )
            return

        height, width = image.shape[:2]

        # ========================================================
        # BGR -> HSV
        # ========================================================
        hsv = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2HSV,
        )

        # OpenCV HSV:
        # red wraps around H=0
        lower_red_1 = np.array(
            [0, 100, 80],
            dtype=np.uint8,
        )

        upper_red_1 = np.array(
            [10, 255, 255],
            dtype=np.uint8,
        )

        lower_red_2 = np.array(
            [170, 100, 80],
            dtype=np.uint8,
        )

        upper_red_2 = np.array(
            [179, 255, 255],
            dtype=np.uint8,
        )

        mask_1 = cv2.inRange(
            hsv,
            lower_red_1,
            upper_red_1,
        )

        mask_2 = cv2.inRange(
            hsv,
            lower_red_2,
            upper_red_2,
        )

        red_mask = cv2.bitwise_or(
            mask_1,
            mask_2,
        )

        # ========================================================
        # Remove small noise
        # ========================================================
        kernel = np.ones(
            (5, 5),
            np.uint8,
        )

        red_mask = cv2.morphologyEx(
            red_mask,
            cv2.MORPH_OPEN,
            kernel,
        )

        red_mask = cv2.morphologyEx(
            red_mask,
            cv2.MORPH_CLOSE,
            kernel,
        )

        # ========================================================
        # Find contours
        # ========================================================
        contours, _ = cv2.findContours(
            red_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        detection = TargetDetection()

        detection.stamp = msg.header.stamp

        detection.detected = False
        detection.confidence = 0.0

        detection.center_u = 0.0
        detection.center_v = 0.0

        detection.center_u_norm = 0.0
        detection.center_v_norm = 0.0

        detection.bbox_x = 0.0
        detection.bbox_y = 0.0
        detection.bbox_width = 0.0
        detection.bbox_height = 0.0

        detection.area_ratio = 0.0

        # ========================================================
        # Draw image center
        # ========================================================
        image_center_u = width // 2
        image_center_v = height // 2

        cv2.drawMarker(
            image,
            (
                image_center_u,
                image_center_v,
            ),
            (255, 255, 255),
            markerType=cv2.MARKER_CROSS,
            markerSize=30,
            thickness=2,
        )

        # ========================================================
        # Largest red object
        # ========================================================
        if contours:

            largest_contour = max(
                contours,
                key=cv2.contourArea,
            )

            contour_area = cv2.contourArea(
                largest_contour
            )

            area_ratio = (
                contour_area
                / float(width * height)
            )

            if area_ratio >= self.min_area_ratio:

                x, y, w, h = cv2.boundingRect(
                    largest_contour
                )

                center_u = x + w / 2.0
                center_v = y + h / 2.0

                # ------------------------------------------------
                # Normalized pixel error
                #
                # horizontal:
                # -1 = far left
                #  0 = image center
                # +1 = far right
                #
                # vertical:
                # -1 = top
                #  0 = center
                # +1 = bottom
                # ------------------------------------------------
                center_u_norm = (
                    center_u - width / 2.0
                ) / (
                    width / 2.0
                )

                center_v_norm = (
                    center_v - height / 2.0
                ) / (
                    height / 2.0
                )

                bbox_area = float(w * h)

                if bbox_area > 0.0:
                    confidence = (
                        contour_area / bbox_area
                    )
                else:
                    confidence = 0.0

                confidence = max(
                    0.0,
                    min(1.0, confidence),
                )

                # ------------------------------------------------
                # Fill message
                # ------------------------------------------------
                detection.detected = True

                detection.confidence = float(
                    confidence
                )

                detection.center_u = float(
                    center_u
                )

                detection.center_v = float(
                    center_v
                )

                detection.center_u_norm = float(
                    center_u_norm
                )

                detection.center_v_norm = float(
                    center_v_norm
                )

                detection.bbox_x = float(x)
                detection.bbox_y = float(y)

                detection.bbox_width = float(w)
                detection.bbox_height = float(h)

                detection.area_ratio = float(
                    area_ratio
                )

                # ------------------------------------------------
                # Debug drawing
                # ------------------------------------------------
                cv2.rectangle(
                    image,
                    (x, y),
                    (
                        x + w,
                        y + h,
                    ),
                    (0, 255, 0),
                    3,
                )

                cv2.circle(
                    image,
                    (
                        int(center_u),
                        int(center_v),
                    ),
                    7,
                    (255, 255, 0),
                    -1,
                )

                cv2.line(
                    image,
                    (
                        image_center_u,
                        image_center_v,
                    ),
                    (
                        int(center_u),
                        int(center_v),
                    ),
                    (0, 255, 255),
                    2,
                )

                cv2.putText(
                    image,
                    (
                        f'ex={center_u_norm:+.3f} '
                        f'ey={center_v_norm:+.3f}'
                    ),
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 255),
                    2,
                )

                cv2.putText(
                    image,
                    (
                        f'area={area_ratio:.4f} '
                        f'conf={confidence:.2f}'
                    ),
                    (20, 75),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

        # ========================================================
        # No target
        # ========================================================
        if not detection.detected:

            cv2.putText(
                image,
                'TARGET NOT DETECTED',
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 255),
                2,
            )

        # ========================================================
        # Publish target data
        # ========================================================
        self.target_pub.publish(
            detection
        )

        # ========================================================
        # Publish debug image
        # ========================================================
        debug_msg = self.bridge.cv2_to_imgmsg(
            image,
            encoding='bgr8',
        )

        debug_msg.header = msg.header

        self.debug_pub.publish(
            debug_msg
        )

        # ========================================================
        # Console log: about 1 Hz
        # ========================================================
        now_s = (
            self.get_clock()
            .now()
            .nanoseconds
            / 1e9
        )

        if (
            now_s - self.last_log_time
            >= 1.0
        ):

            self.last_log_time = now_s

            if detection.detected:

                self.get_logger().info(
                    'TARGET | '
                    f'u={detection.center_u:.1f}, '
                    f'v={detection.center_v:.1f} | '
                    f'ex={detection.center_u_norm:+.3f}, '
                    f'ey={detection.center_v_norm:+.3f} | '
                    f'area={detection.area_ratio:.4f}'
                )

            else:

                self.get_logger().info(
                    'TARGET NOT DETECTED'
                )


def main(args=None):

    rclpy.init(args=args)

    node = PerceptionNode()

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