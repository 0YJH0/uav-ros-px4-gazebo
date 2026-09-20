// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from uav_interfaces:msg/TargetDetection.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "uav_interfaces/msg/target_detection.hpp"


#ifndef UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__STRUCT_HPP_
#define UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__uav_interfaces__msg__TargetDetection __attribute__((deprecated))
#else
# define DEPRECATED__uav_interfaces__msg__TargetDetection __declspec(deprecated)
#endif

namespace uav_interfaces
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct TargetDetection_
{
  using Type = TargetDetection_<ContainerAllocator>;

  explicit TargetDetection_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : stamp(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->detected = false;
      this->confidence = 0.0f;
      this->center_u = 0.0f;
      this->center_v = 0.0f;
      this->center_u_norm = 0.0f;
      this->center_v_norm = 0.0f;
      this->bbox_x = 0.0f;
      this->bbox_y = 0.0f;
      this->bbox_width = 0.0f;
      this->bbox_height = 0.0f;
      this->area_ratio = 0.0f;
    }
  }

  explicit TargetDetection_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : stamp(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->detected = false;
      this->confidence = 0.0f;
      this->center_u = 0.0f;
      this->center_v = 0.0f;
      this->center_u_norm = 0.0f;
      this->center_v_norm = 0.0f;
      this->bbox_x = 0.0f;
      this->bbox_y = 0.0f;
      this->bbox_width = 0.0f;
      this->bbox_height = 0.0f;
      this->area_ratio = 0.0f;
    }
  }

  // field types and members
  using _stamp_type =
    builtin_interfaces::msg::Time_<ContainerAllocator>;
  _stamp_type stamp;
  using _detected_type =
    bool;
  _detected_type detected;
  using _confidence_type =
    float;
  _confidence_type confidence;
  using _center_u_type =
    float;
  _center_u_type center_u;
  using _center_v_type =
    float;
  _center_v_type center_v;
  using _center_u_norm_type =
    float;
  _center_u_norm_type center_u_norm;
  using _center_v_norm_type =
    float;
  _center_v_norm_type center_v_norm;
  using _bbox_x_type =
    float;
  _bbox_x_type bbox_x;
  using _bbox_y_type =
    float;
  _bbox_y_type bbox_y;
  using _bbox_width_type =
    float;
  _bbox_width_type bbox_width;
  using _bbox_height_type =
    float;
  _bbox_height_type bbox_height;
  using _area_ratio_type =
    float;
  _area_ratio_type area_ratio;

  // setters for named parameter idiom
  Type & set__stamp(
    const builtin_interfaces::msg::Time_<ContainerAllocator> & _arg)
  {
    this->stamp = _arg;
    return *this;
  }
  Type & set__detected(
    const bool & _arg)
  {
    this->detected = _arg;
    return *this;
  }
  Type & set__confidence(
    const float & _arg)
  {
    this->confidence = _arg;
    return *this;
  }
  Type & set__center_u(
    const float & _arg)
  {
    this->center_u = _arg;
    return *this;
  }
  Type & set__center_v(
    const float & _arg)
  {
    this->center_v = _arg;
    return *this;
  }
  Type & set__center_u_norm(
    const float & _arg)
  {
    this->center_u_norm = _arg;
    return *this;
  }
  Type & set__center_v_norm(
    const float & _arg)
  {
    this->center_v_norm = _arg;
    return *this;
  }
  Type & set__bbox_x(
    const float & _arg)
  {
    this->bbox_x = _arg;
    return *this;
  }
  Type & set__bbox_y(
    const float & _arg)
  {
    this->bbox_y = _arg;
    return *this;
  }
  Type & set__bbox_width(
    const float & _arg)
  {
    this->bbox_width = _arg;
    return *this;
  }
  Type & set__bbox_height(
    const float & _arg)
  {
    this->bbox_height = _arg;
    return *this;
  }
  Type & set__area_ratio(
    const float & _arg)
  {
    this->area_ratio = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    uav_interfaces::msg::TargetDetection_<ContainerAllocator> *;
  using ConstRawPtr =
    const uav_interfaces::msg::TargetDetection_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<uav_interfaces::msg::TargetDetection_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<uav_interfaces::msg::TargetDetection_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      uav_interfaces::msg::TargetDetection_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<uav_interfaces::msg::TargetDetection_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      uav_interfaces::msg::TargetDetection_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<uav_interfaces::msg::TargetDetection_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<uav_interfaces::msg::TargetDetection_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<uav_interfaces::msg::TargetDetection_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__uav_interfaces__msg__TargetDetection
    std::shared_ptr<uav_interfaces::msg::TargetDetection_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__uav_interfaces__msg__TargetDetection
    std::shared_ptr<uav_interfaces::msg::TargetDetection_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const TargetDetection_ & other) const
  {
    if (this->stamp != other.stamp) {
      return false;
    }
    if (this->detected != other.detected) {
      return false;
    }
    if (this->confidence != other.confidence) {
      return false;
    }
    if (this->center_u != other.center_u) {
      return false;
    }
    if (this->center_v != other.center_v) {
      return false;
    }
    if (this->center_u_norm != other.center_u_norm) {
      return false;
    }
    if (this->center_v_norm != other.center_v_norm) {
      return false;
    }
    if (this->bbox_x != other.bbox_x) {
      return false;
    }
    if (this->bbox_y != other.bbox_y) {
      return false;
    }
    if (this->bbox_width != other.bbox_width) {
      return false;
    }
    if (this->bbox_height != other.bbox_height) {
      return false;
    }
    if (this->area_ratio != other.area_ratio) {
      return false;
    }
    return true;
  }
  bool operator!=(const TargetDetection_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct TargetDetection_

// alias to use template instance with default allocator
using TargetDetection =
  uav_interfaces::msg::TargetDetection_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace uav_interfaces

#endif  // UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__STRUCT_HPP_
