from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    state_monitor_node = Node(
        package='uav_learning',
        executable='uav_state_monitor',
        name='uav_state_monitor',
        output='screen'
    )

    mode_server_node = Node(
        package='uav_learning',
        executable='uav_mode_server',
        name='uav_mode_server',
        output='screen'
    )

    altitude_action_server_node = Node(
        package='uav_learning',
        executable='fly_to_altitude_server',
        name='fly_to_altitude_server',
        output='screen'
    )

    return LaunchDescription([
        state_monitor_node,
        mode_server_node,
        altitude_action_server_node
    ])