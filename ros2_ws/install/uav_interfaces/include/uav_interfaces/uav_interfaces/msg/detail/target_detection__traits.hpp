// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from uav_interfaces:msg/TargetDetection.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "uav_interfaces/msg/target_detection.hpp"


#ifndef UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__TRAITS_HPP_
#define UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "uav_interfaces/msg/detail/target_detection__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__traits.hpp"

namespace uav_interfaces
{

namespace msg
{

inline void to_flow_style_yaml(
  const TargetDetection & msg,
  std::ostream & out)
{
  out << "{";
  // member: stamp
  {
    out << "stamp: ";
    to_flow_style_yaml(msg.stamp, out);
    out << ", ";
  }

  // member: detected
  {
    out << "detected: ";
    rosidl_generator_traits::value_to_yaml(msg.detected, out);
    out << ", ";
  }

  // member: confidence
  {
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << ", ";
  }

  // member: center_u
  {
    out << "center_u: ";
    rosidl_generator_traits::value_to_yaml(msg.center_u, out);
    out << ", ";
  }

  // member: center_v
  {
    out << "center_v: ";
    rosidl_generator_traits::value_to_yaml(msg.center_v, out);
    out << ", ";
  }

  // member: center_u_norm
  {
    out << "center_u_norm: ";
    rosidl_generator_traits::value_to_yaml(msg.center_u_norm, out);
    out << ", ";
  }

  // member: center_v_norm
  {
    out << "center_v_norm: ";
    rosidl_generator_traits::value_to_yaml(msg.center_v_norm, out);
    out << ", ";
  }

  // member: bbox_x
  {
    out << "bbox_x: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_x, out);
    out << ", ";
  }

  // member: bbox_y
  {
    out << "bbox_y: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_y, out);
    out << ", ";
  }

  // member: bbox_width
  {
    out << "bbox_width: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_width, out);
    out << ", ";
  }

  // member: bbox_height
  {
    out << "bbox_height: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_height, out);
    out << ", ";
  }

  // member: area_ratio
  {
    out << "area_ratio: ";
    rosidl_generator_traits::value_to_yaml(msg.area_ratio, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const TargetDetection & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: stamp
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "stamp:\n";
    to_block_style_yaml(msg.stamp, out, indentation + 2);
  }

  // member: detected
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "detected: ";
    rosidl_generator_traits::value_to_yaml(msg.detected, out);
    out << "\n";
  }

  // member: confidence
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "confidence: ";
    rosidl_generator_traits::value_to_yaml(msg.confidence, out);
    out << "\n";
  }

  // member: center_u
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "center_u: ";
    rosidl_generator_traits::value_to_yaml(msg.center_u, out);
    out << "\n";
  }

  // member: center_v
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "center_v: ";
    rosidl_generator_traits::value_to_yaml(msg.center_v, out);
    out << "\n";
  }

  // member: center_u_norm
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "center_u_norm: ";
    rosidl_generator_traits::value_to_yaml(msg.center_u_norm, out);
    out << "\n";
  }

  // member: center_v_norm
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "center_v_norm: ";
    rosidl_generator_traits::value_to_yaml(msg.center_v_norm, out);
    out << "\n";
  }

  // member: bbox_x
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "bbox_x: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_x, out);
    out << "\n";
  }

  // member: bbox_y
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "bbox_y: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_y, out);
    out << "\n";
  }

  // member: bbox_width
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "bbox_width: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_width, out);
    out << "\n";
  }

  // member: bbox_height
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "bbox_height: ";
    rosidl_generator_traits::value_to_yaml(msg.bbox_height, out);
    out << "\n";
  }

  // member: area_ratio
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "area_ratio: ";
    rosidl_generator_traits::value_to_yaml(msg.area_ratio, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const TargetDetection & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace uav_interfaces

namespace rosidl_generator_traits
{

[[deprecated("use uav_interfaces::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const uav_interfaces::msg::TargetDetection & msg,
  std::ostream & out, size_t indentation = 0)
{
  uav_interfaces::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use uav_interfaces::msg::to_yaml() instead")]]
inline std::string to_yaml(const uav_interfaces::msg::TargetDetection & msg)
{
  return uav_interfaces::msg::to_yaml(msg);
}

template<>
inline const char * data_type<uav_interfaces::msg::TargetDetection>()
{
  return "uav_interfaces::msg::TargetDetection";
}

template<>
inline const char * name<uav_interfaces::msg::TargetDetection>()
{
  return "uav_interfaces/msg/TargetDetection";
}

template<>
struct has_fixed_size<uav_interfaces::msg::TargetDetection>
  : std::integral_constant<bool, has_fixed_size<builtin_interfaces::msg::Time>::value> {};

template<>
struct has_bounded_size<uav_interfaces::msg::TargetDetection>
  : std::integral_constant<bool, has_bounded_size<builtin_interfaces::msg::Time>::value> {};

template<>
struct is_message<uav_interfaces::msg::TargetDetection>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__TRAITS_HPP_
