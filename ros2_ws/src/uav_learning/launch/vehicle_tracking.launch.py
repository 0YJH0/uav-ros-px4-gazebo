from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    share = Path(get_package_share_directory('uav_learning'))
    return LaunchDescription([
        DeclareLaunchArgument('model_path', default_value='yolo11s.pt'),
        DeclareLaunchArgument('device', default_value='cpu'),
        DeclareLaunchArgument('cpu_inference_threads', default_value='0'),
        DeclareLaunchArgument('detector_backend', default_value='torch'),
        DeclareLaunchArgument('backend_artifacts', default_value=''),
        DeclareLaunchArgument('predict_box_scale_velocity', default_value='true'),
        DeclareLaunchArgument('perception_python', default_value=''),
        DeclareLaunchArgument('target_roi_enabled', default_value='true'),
        DeclareLaunchArgument('recovery_competition_enabled', default_value='false'),
        DeclareLaunchArgument('start_controller', default_value='false'),
        DeclareLaunchArgument('occlusion_enabled', default_value='false'),
        DeclareLaunchArgument('vehicle_speed', default_value='0.8'),
        DeclareLaunchArgument('traffic_scenario', default_value='crossing'),
        DeclareLaunchArgument('smooth_recovery_setpoints', default_value='false'),
        DeclareLaunchArgument('occlusion_start', default_value='15.0'),
        DeclareLaunchArgument('occlusion_duration', default_value='4.0'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(
            str(share / 'launch/camera_bridge.launch.py'))),
        Node(package='ros_gz_bridge', executable='parameter_bridge',
             arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock']),
        Node(package='uav_learning', executable='vehicle_scene',
             output='screen', parameters=[{
                 'use_sim_time': True,
                 'traffic_scenario': LaunchConfiguration('traffic_scenario'),
                 'occlusion_enabled': ParameterValue(
                     LaunchConfiguration('occlusion_enabled'), value_type=bool),
                 'vehicle_speed': ParameterValue(
                     LaunchConfiguration('vehicle_speed'), value_type=float),
                 'occlusion_start': ParameterValue(
                     LaunchConfiguration('occlusion_start'), value_type=float),
                 'occlusion_duration': ParameterValue(
                     LaunchConfiguration('occlusion_duration'), value_type=float),
             }]),
        Node(package='uav_learning', executable='perception_node',
             prefix=LaunchConfiguration('perception_python'),
             output='screen', parameters=[{
                 'model_path': LaunchConfiguration('model_path'),
                 'device': LaunchConfiguration('device'),
                 'cpu_inference_threads': ParameterValue(
                     LaunchConfiguration('cpu_inference_threads'), value_type=int),
                 'detector_backend': LaunchConfiguration('detector_backend'),
                 'backend_artifacts': ParameterValue(LaunchConfiguration('backend_artifacts'), value_type=str),
                 'predict_box_scale_velocity': ParameterValue(
                     LaunchConfiguration('predict_box_scale_velocity'), value_type=bool),
                 'target_roi_enabled': ParameterValue(
                     LaunchConfiguration('target_roi_enabled'), value_type=bool),
                 'recovery_competition_enabled': ParameterValue(
                     LaunchConfiguration('recovery_competition_enabled'), value_type=bool),
                 'target_class': 'car',
                 'target_reacquire_timeout': 10.0,
                 'acquisition_center_gate': 0.35,
                 'acquisition_confirm_frames': 3,
             }]),
        Node(package='uav_learning', executable='px4_offboard_controller',
             output='screen',
             condition=IfCondition(LaunchConfiguration('start_controller')),
             parameters=[{
                 'tracking_enabled': True, 'tracking_duration': 90.0,
                 'smooth_recovery_setpoints': ParameterValue(
                     LaunchConfiguration('smooth_recovery_setpoints'), value_type=bool),
                 'target_height': 3.0,
                 'approach_stop_area_ratio': 0.020,
                 'approach_slow_area_ratio': 0.015,
                 'tracking_area_deadband': 0.002,
                 'approach_forward_speed': 2.0,
                 'approach_slow_speed': 0.6,
                 'approach_max_setpoint_lead': 1.5,
                 'approach_timeout': 120.0,
                 'search_yaw_rate_deg_s': 3.0,
                 'search_timeout': 150.0,
                 'approach_target_lost_timeout': 1.5,
                 'recovery_timeout': 10.0,
                 'recovery_max_speed': 0.8,
                 'recovery_max_distance': 4.0,
                 'recovery_confirm_frames': 3,
                 'observation_gap_timeout': 0.5,
                 'tracking_camera_hfov': 1.204,
                 'tracking_lateral_kp': 0.7,
                 'tracking_max_lateral_speed': 0.6,
                 'tracking_range_ki': 20.0,
                 'tracking_use_sim_clock': True,
             }]),
    ])
