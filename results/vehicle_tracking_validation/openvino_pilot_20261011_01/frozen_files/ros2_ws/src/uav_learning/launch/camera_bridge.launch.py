from launch import LaunchDescription
from launch_ros.actions import Node


# ============================================================
# Gazebo RGB camera topics
# ============================================================

GZ_IMAGE_TOPIC = (
    '/world/default/model/x500_perception_0/'
    'link/camera_link/sensor/IMX214/image'
)

GZ_CAMERA_INFO_TOPIC = (
    '/world/default/model/x500_perception_0/'
    'link/camera_link/sensor/IMX214/camera_info'
)


# ============================================================
# Standard ROS 2 camera topics
# ============================================================

ROS_IMAGE_TOPIC = '/camera/image_raw'

ROS_CAMERA_INFO_TOPIC = '/camera/camera_info'


def generate_launch_description():

    # ========================================================
    # RGB image bridge
    #
    # Gazebo:
    #   gz.msgs.Image
    #
    # ROS 2:
    #   sensor_msgs/msg/Image
    # ========================================================

    image_bridge = Node(

        package='ros_gz_image',

        executable='image_bridge',

        name='rgb_image_bridge',

        output='screen',

        arguments=[
            GZ_IMAGE_TOPIC,
        ],

        remappings=[
            (
                GZ_IMAGE_TOPIC,
                ROS_IMAGE_TOPIC,
            ),
        ],
    )


    # ========================================================
    # CameraInfo bridge
    #
    # Gazebo:
    #   gz.msgs.CameraInfo
    #
    # ROS 2:
    #   sensor_msgs/msg/CameraInfo
    #
    # '[' means Gazebo -> ROS 2.
    # ========================================================

    camera_info_bridge = Node(

        package='ros_gz_bridge',

        executable='parameter_bridge',

        name='camera_info_bridge',

        output='screen',

        arguments=[
            (
                f'{GZ_CAMERA_INFO_TOPIC}'
                '@sensor_msgs/msg/CameraInfo'
                '[gz.msgs.CameraInfo'
            ),
        ],

        remappings=[
            (
                GZ_CAMERA_INFO_TOPIC,
                ROS_CAMERA_INFO_TOPIC,
            ),
        ],
    )


    return LaunchDescription([
        image_bridge,
        camera_info_bridge,
    ])