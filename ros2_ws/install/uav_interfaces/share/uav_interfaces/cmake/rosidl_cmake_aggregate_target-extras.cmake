# generated from rosidl_cmake/cmake/rosidl_cmake_aggregate_target-extras.cmake.in

# Create a convenience aggregate target uav_interfaces::uav_interfaces
# that links all generated interface targets, so downstream packages can use
# a single modern CMake target name instead of ${uav_interfaces_TARGETS}.
if(uav_interfaces_TARGETS AND NOT TARGET uav_interfaces::uav_interfaces)
  add_library(uav_interfaces::uav_interfaces INTERFACE IMPORTED)
  set_target_properties(uav_interfaces::uav_interfaces PROPERTIES
    INTERFACE_LINK_LIBRARIES "${uav_interfaces_TARGETS}")
endif()
