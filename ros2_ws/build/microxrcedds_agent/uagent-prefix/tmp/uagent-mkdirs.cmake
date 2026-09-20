# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/yjh/ROS2_manmade/ros2_ws/src/Micro-XRCE-DDS-Agent"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/uagent-prefix"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/uagent-prefix/tmp"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/uagent-prefix/src/uagent-stamp"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/uagent-prefix/src"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/uagent-prefix/src/uagent-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/uagent-prefix/src/uagent-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/uagent-prefix/src/uagent-stamp${cfgdir}") # cfgdir has leading slash
endif()
