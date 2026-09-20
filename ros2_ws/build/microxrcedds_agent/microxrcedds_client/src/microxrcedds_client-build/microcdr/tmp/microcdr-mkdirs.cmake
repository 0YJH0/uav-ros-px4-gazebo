# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-build"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/temp_install"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/tmp"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-stamp"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src"
  "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-stamp${cfgdir}") # cfgdir has leading slash
endif()
