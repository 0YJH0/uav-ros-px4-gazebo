# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/spdlog/src/spdlog"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/spdlog/src/spdlog-build"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/temp_install/spdlog-1.9.2"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/spdlog/tmp"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/spdlog/src/spdlog-stamp"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/spdlog/src"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/spdlog/src/spdlog-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/spdlog/src/spdlog-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/spdlog/src/spdlog-stamp${cfgdir}") # cfgdir has leading slash
endif()
