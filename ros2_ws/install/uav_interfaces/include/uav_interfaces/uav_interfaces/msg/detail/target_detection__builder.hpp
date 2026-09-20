// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from uav_interfaces:msg/TargetDetection.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "uav_interfaces/msg/target_detection.hpp"


#ifndef UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__BUILDER_HPP_
#define UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "uav_interfaces/msg/detail/target_detection__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace uav_interfaces
{

namespace msg
{

namespace builder
{

class Init_TargetDetection_area_ratio
{
public:
  explicit Init_TargetDetection_area_ratio(::uav_interfaces::msg::TargetDetection & msg)
  : msg_(msg)
  {}
  ::uav_interfaces::msg::TargetDetection area_ratio(::uav_interfaces::msg::TargetDetection::_area_ratio_type arg)
  {
    msg_.area_ratio = std::move(arg);
    return std::move(msg_);
  }

private:
  ::uav_interfaces::msg::TargetDetection msg_;
};

class Init_TargetDetection_bbox_height
{
public:
  explicit Init_TargetDetection_bbox_height(::uav_interfaces::msg::TargetDetection & msg)
  : msg_(msg)
  {}
  Init_TargetDetection_area_ratio bbox_height(::uav_interfaces::msg::TargetDetection::_bbox_height_type arg)
  {
    msg_.bbox_height = std::move(arg);
    return Init_TargetDetection_area_ratio(msg_);
  }

private:
  ::uav_interfaces::msg::TargetDetection msg_;
};

class Init_TargetDetection_bbox_width
{
public:
  explicit Init_TargetDetection_bbox_width(::uav_interfaces::msg::TargetDetection & msg)
  : msg_(msg)
  {}
  Init_TargetDetection_bbox_height bbox_width(::uav_interfaces::msg::TargetDetection::_bbox_width_type arg)
  {
    msg_.bbox_width = std::move(arg);
    return Init_TargetDetection_bbox_height(msg_);
  }

private:
  ::uav_interfaces::msg::TargetDetection msg_;
};

class Init_TargetDetection_bbox_y
{
public:
  explicit Init_TargetDetection_bbox_y(::uav_interfaces::msg::TargetDetection & msg)
  : msg_(msg)
  {}
  Init_TargetDetection_bbox_width bbox_y(::uav_interfaces::msg::TargetDetection::_bbox_y_type arg)
  {
    msg_.bbox_y = std::move(arg);
    return Init_TargetDetection_bbox_width(msg_);
  }

private:
  ::uav_interfaces::msg::TargetDetection msg_;
};

class Init_TargetDetection_bbox_x
{
public:
  explicit Init_TargetDetection_bbox_x(::uav_interfaces::msg::TargetDetection & msg)
  : msg_(msg)
  {}
  Init_TargetDetection_bbox_y bbox_x(::uav_interfaces::msg::TargetDetection::_bbox_x_type arg)
  {
    msg_.bbox_x = std::move(arg);
    return Init_TargetDetection_bbox_y(msg_);
  }

private:
  ::uav_interfaces::msg::TargetDetection msg_;
};

class Init_TargetDetection_center_v_norm
{
public:
  explicit Init_TargetDetection_center_v_norm(::uav_interfaces::msg::TargetDetection & msg)
  : msg_(msg)
  {}
  Init_TargetDetection_bbox_x center_v_norm(::uav_interfaces::msg::TargetDetection::_center_v_norm_type arg)
  {
    msg_.center_v_norm = std::move(arg);
    return Init_TargetDetection_bbox_x(msg_);
  }

private:
  ::uav_interfaces::msg::TargetDetection msg_;
};

class Init_TargetDetection_center_u_norm
{
public:
  explicit Init_TargetDetection_center_u_norm(::uav_interfaces::msg::TargetDetection & msg)
  : msg_(msg)
  {}
  Init_TargetDetection_center_v_norm center_u_norm(::uav_interfaces::msg::TargetDetection::_center_u_norm_type arg)
  {
    msg_.center_u_norm = std::move(arg);
    return Init_TargetDetection_center_v_norm(msg_);
  }

private:
  ::uav_interfaces::msg::TargetDetection msg_;
};

class Init_TargetDetection_center_v
{
public:
  explicit Init_TargetDetection_center_v(::uav_interfaces::msg::TargetDetection & msg)
  : msg_(msg)
  {}
  Init_TargetDetection_center_u_norm center_v(::uav_interfaces::msg::TargetDetection::_center_v_type arg)
  {
    msg_.center_v = std::move(arg);
    return Init_TargetDetection_center_u_norm(msg_);
  }

private:
  ::uav_interfaces::msg::TargetDetection msg_;
};

class Init_TargetDetection_center_u
{
public:
  explicit Init_TargetDetection_center_u(::uav_interfaces::msg::TargetDetection & msg)
  : msg_(msg)
  {}
  Init_TargetDetection_center_v center_u(::uav_interfaces::msg::TargetDetection::_center_u_type arg)
  {
    msg_.center_u = std::move(arg);
    return Init_TargetDetection_center_v(msg_);
  }

private:
  ::uav_interfaces::msg::TargetDetection msg_;
};

class Init_TargetDetection_confidence
{
public:
  explicit Init_TargetDetection_confidence(::uav_interfaces::msg::TargetDetection & msg)
  : msg_(msg)
  {}
  Init_TargetDetection_center_u confidence(::uav_interfaces::msg::TargetDetection::_confidence_type arg)
  {
    msg_.confidence = std::move(arg);
    return Init_TargetDetection_center_u(msg_);
  }

private:
  ::uav_interfaces::msg::TargetDetection msg_;
};

class Init_TargetDetection_detected
{
public:
  explicit Init_TargetDetection_detected(::uav_interfaces::msg::TargetDetection & msg)
  : msg_(msg)
  {}
  Init_TargetDetection_confidence detected(::uav_interfaces::msg::TargetDetection::_detected_type arg)
  {
    msg_.detected = std::move(arg);
    return Init_TargetDetection_confidence(msg_);
  }

private:
  ::uav_interfaces::msg::TargetDetection msg_;
};

class Init_TargetDetection_stamp
{
public:
  Init_TargetDetection_stamp()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_TargetDetection_detected stamp(::uav_interfaces::msg::TargetDetection::_stamp_type arg)
  {
    msg_.stamp = std::move(arg);
    return Init_TargetDetection_detected(msg_);
  }

private:
  ::uav_interfaces::msg::TargetDetection msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::uav_interfaces::msg::TargetDetection>()
{
  return uav_interfaces::msg::builder::Init_TargetDetection_stamp();
}

}  // namespace uav_interfaces

#endif  // UAV_INTERFACES__MSG__DETAIL__TARGET_DETECTION__BUILDER_HPP_
