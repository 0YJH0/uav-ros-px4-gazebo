// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from uav_interfaces:msg/TargetDetection.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "uav_interfaces/msg/target_detection.h"


#ifndef UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__STRUCT_H_
#define UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

// Constants defined in the message

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in msg/TargetDetection in the package uav_interfaces.
typedef struct uav_interfaces__msg__TargetDetection
{
  builtin_interfaces__msg__Time stamp;
  bool detected;
  float confidence;
  float center_u;
  float center_v;
  float center_u_norm;
  float center_v_norm;
  float bbox_x;
  float bbox_y;
  float bbox_width;
  float bbox_height;
  float area_ratio;
} uav_interfaces__msg__TargetDetection;

// Struct for a sequence of uav_interfaces__msg__TargetDetection.
typedef struct uav_interfaces__msg__TargetDetection__Sequence
{
  uav_interfaces__msg__TargetDetection * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} uav_interfaces__msg__TargetDetection__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__STRUCT_H_
