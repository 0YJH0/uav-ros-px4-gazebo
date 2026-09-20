// generated from rosidl_typesupport_fastrtps_c/resource/idl__rosidl_typesupport_fastrtps_c.h.em
// with input from uav_interfaces:msg/TargetDetection.idl
// generated code does not contain a copyright notice
#ifndef UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_
#define UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_


#include <stddef.h>
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "uav_interfaces/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "uav_interfaces/msg/detail/target_detection__struct.h"
#include "fastcdr/Cdr.h"

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_uav_interfaces
bool cdr_serialize_uav_interfaces__msg__TargetDetection(
  const uav_interfaces__msg__TargetDetection * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_uav_interfaces
bool cdr_deserialize_uav_interfaces__msg__TargetDetection(
  eprosima::fastcdr::Cdr &,
  uav_interfaces__msg__TargetDetection * ros_message);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_uav_interfaces
size_t get_serialized_size_uav_interfaces__msg__TargetDetection(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_uav_interfaces
size_t max_serialized_size_uav_interfaces__msg__TargetDetection(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_uav_interfaces
bool cdr_serialize_key_uav_interfaces__msg__TargetDetection(
  const uav_interfaces__msg__TargetDetection * ros_message,
  eprosima::fastcdr::Cdr & cdr);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_uav_interfaces
size_t get_serialized_size_key_uav_interfaces__msg__TargetDetection(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_uav_interfaces
size_t max_serialized_size_key_uav_interfaces__msg__TargetDetection(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_uav_interfaces
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, uav_interfaces, msg, TargetDetection)();

#ifdef __cplusplus
}
#endif

#endif  // UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__ROSIDL_TYPESUPPORT_FASTRTPS_C_H_
