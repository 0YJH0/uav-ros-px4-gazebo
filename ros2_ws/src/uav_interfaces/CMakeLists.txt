cmake_minimum_required(VERSION 3.8)

project(uav_interfaces)


# ============================================================
# Dependencies
# ============================================================

find_package(
  ament_cmake
  REQUIRED
)

find_package(
  rosidl_default_generators
  REQUIRED
)

find_package(
  builtin_interfaces
  REQUIRED
)


# ============================================================
# ROS 2 interfaces
# ============================================================

rosidl_generate_interfaces(
  ${PROJECT_NAME}

  "msg/TargetDetection.msg"

  "srv/SetMode.srv"

  "action/FlyToAltitude.action"

  DEPENDENCIES
  builtin_interfaces
)


# ============================================================
# Runtime
# ============================================================

ament_export_dependencies(
  rosidl_default_runtime
)


ament_package()