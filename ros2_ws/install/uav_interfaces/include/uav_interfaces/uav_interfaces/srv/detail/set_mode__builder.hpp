// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from uav_interfaces:srv/SetMode.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "uav_interfaces/srv/set_mode.hpp"


#ifndef UAV_INTERFACES__SRV__DETAIL__SET_MODE__BUILDER_HPP_
#define UAV_INTERFACES__SRV__DETAIL__SET_MODE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "uav_interfaces/srv/detail/set_mode__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace uav_interfaces
{

namespace srv
{

namespace builder
{

class Init_SetMode_Request_mode
{
public:
  Init_SetMode_Request_mode()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::uav_interfaces::srv::SetMode_Request mode(::uav_interfaces::srv::SetMode_Request::_mode_type arg)
  {
    msg_.mode = std::move(arg);
    return std::move(msg_);
  }

private:
  ::uav_interfaces::srv::SetMode_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::uav_interfaces::srv::SetMode_Request>()
{
  return uav_interfaces::srv::builder::Init_SetMode_Request_mode();
}

}  // namespace uav_interfaces


namespace uav_interfaces
{

namespace srv
{

namespace builder
{

class Init_SetMode_Response_message
{
public:
  explicit Init_SetMode_Response_message(::uav_interfaces::srv::SetMode_Response & msg)
  : msg_(msg)
  {}
  ::uav_interfaces::srv::SetMode_Response message(::uav_interfaces::srv::SetMode_Response::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::uav_interfaces::srv::SetMode_Response msg_;
};

class Init_SetMode_Response_success
{
public:
  Init_SetMode_Response_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_SetMode_Response_message success(::uav_interfaces::srv::SetMode_Response::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_SetMode_Response_message(msg_);
  }

private:
  ::uav_interfaces::srv::SetMode_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::uav_interfaces::srv::SetMode_Response>()
{
  return uav_interfaces::srv::builder::Init_SetMode_Response_success();
}

}  // namespace uav_interfaces


namespace uav_interfaces
{

namespace srv
{

namespace builder
{

class Init_SetMode_Event_response
{
public:
  explicit Init_SetMode_Event_response(::uav_interfaces::srv::SetMode_Event & msg)
  : msg_(msg)
  {}
  ::uav_interfaces::srv::SetMode_Event response(::uav_interfaces::srv::SetMode_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::uav_interfaces::srv::SetMode_Event msg_;
};

class Init_SetMode_Event_request
{
public:
  explicit Init_SetMode_Event_request(::uav_interfaces::srv::SetMode_Event & msg)
  : msg_(msg)
  {}
  Init_SetMode_Event_response request(::uav_interfaces::srv::SetMode_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_SetMode_Event_response(msg_);
  }

private:
  ::uav_interfaces::srv::SetMode_Event msg_;
};

class Init_SetMode_Event_info
{
public:
  Init_SetMode_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_SetMode_Event_request info(::uav_interfaces::srv::SetMode_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_SetMode_Event_request(msg_);
  }

private:
  ::uav_interfaces::srv::SetMode_Event msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::uav_interfaces::srv::SetMode_Event>()
{
  return uav_interfaces::srv::builder::Init_SetMode_Event_info();
}

}  // namespace uav_interfaces

#endif  // UAV_INTERFACES__SRV__DETAIL__SET_MODE__BUILDER_HPP_
