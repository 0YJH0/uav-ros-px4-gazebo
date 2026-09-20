# Install script for directory: /home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/temp_install/microcdr-2.0.1")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "Release")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Install shared libraries without execute permission?
if(NOT DEFINED CMAKE_INSTALL_SO_NO_EXE)
  set(CMAKE_INSTALL_SO_NO_EXE "1")
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set default install directory permissions.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  foreach(file
      "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libmicrocdr.so.2.0.1"
      "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libmicrocdr.so.2.0"
      )
    if(EXISTS "${file}" AND
       NOT IS_SYMLINK "${file}")
      file(RPATH_CHECK
           FILE "${file}"
           RPATH "")
    endif()
  endforeach()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES
    "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-build/libmicrocdr.so.2.0.1"
    "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-build/libmicrocdr.so.2.0"
    )
  foreach(file
      "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libmicrocdr.so.2.0.1"
      "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/lib/libmicrocdr.so.2.0"
      )
    if(EXISTS "${file}" AND
       NOT IS_SYMLINK "${file}")
      if(CMAKE_INSTALL_DO_STRIP)
        execute_process(COMMAND "/usr/bin/strip" "${file}")
      endif()
    endif()
  endforeach()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/lib" TYPE SHARED_LIBRARY FILES "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-build/libmicrocdr.so")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/ucdr" TYPE DIRECTORY FILES "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr/include/ucdr/" FILES_MATCHING REGEX "/[^/]*\\.h$")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/include/ucdr" TYPE FILE FILES "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-build/include/ucdr/config.h")
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  if(EXISTS "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/share/microcdr/cmake/microcdrTargets.cmake")
    file(DIFFERENT _cmake_export_file_changed FILES
         "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/share/microcdr/cmake/microcdrTargets.cmake"
         "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-build/CMakeFiles/Export/7dbace54a6f331dd3fb26f3c05b88776/microcdrTargets.cmake")
    if(_cmake_export_file_changed)
      file(GLOB _cmake_old_config_files "$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/share/microcdr/cmake/microcdrTargets-*.cmake")
      if(_cmake_old_config_files)
        string(REPLACE ";" ", " _cmake_old_config_files_text "${_cmake_old_config_files}")
        message(STATUS "Old export file \"$ENV{DESTDIR}${CMAKE_INSTALL_PREFIX}/share/microcdr/cmake/microcdrTargets.cmake\" will be replaced.  Removing files [${_cmake_old_config_files_text}].")
        unset(_cmake_old_config_files_text)
        file(REMOVE ${_cmake_old_config_files})
      endif()
      unset(_cmake_old_config_files)
    endif()
    unset(_cmake_export_file_changed)
  endif()
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/microcdr/cmake" TYPE FILE FILES "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-build/CMakeFiles/Export/7dbace54a6f331dd3fb26f3c05b88776/microcdrTargets.cmake")
  if(CMAKE_INSTALL_CONFIG_NAME MATCHES "^([Rr][Ee][Ll][Ee][Aa][Ss][Ee])$")
    file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/microcdr/cmake" TYPE FILE FILES "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-build/CMakeFiles/Export/7dbace54a6f331dd3fb26f3c05b88776/microcdrTargets-release.cmake")
  endif()
endif()

if(CMAKE_INSTALL_COMPONENT STREQUAL "Unspecified" OR NOT CMAKE_INSTALL_COMPONENT)
  file(INSTALL DESTINATION "${CMAKE_INSTALL_PREFIX}/share/microcdr/cmake" TYPE FILE FILES
    "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-build/cmake/config/microcdrConfig.cmake"
    "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-build/cmake/config/microcdrConfigVersion.cmake"
    )
endif()

if(CMAKE_INSTALL_COMPONENT)
  set(CMAKE_INSTALL_MANIFEST "install_manifest_${CMAKE_INSTALL_COMPONENT}.txt")
else()
  set(CMAKE_INSTALL_MANIFEST "install_manifest.txt")
endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
file(WRITE "/home/yjh/ROS2_manmade/ros2_ws/build/microxrcedds_agent/microxrcedds_client/src/microxrcedds_client-build/microcdr/src/microcdr-build/${CMAKE_INSTALL_MANIFEST}"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
