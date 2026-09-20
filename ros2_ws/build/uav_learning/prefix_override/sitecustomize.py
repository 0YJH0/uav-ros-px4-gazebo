import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/yjh/ROS2_manmade/ros2_ws/install/uav_learning'
