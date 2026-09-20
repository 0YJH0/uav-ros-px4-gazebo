// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from uav_interfaces:action/FlyToAltitude.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "uav_interfaces/action/fly_to_altitude.hpp"


#ifndef UAV_INTERFACES__ACTION__DETAIL__FLY_TO_ALTITUDE__BUILDER_HPP_
#define UAV_INTERFACES__ACTION__DETAIL__FLY_TO_ALTITUDE__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "uav_interfaces/action/detail/fly_to_altitude__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace uav_interfaces
{

namespace action
{

namespace builder
{

class Init_FlyToAltitude_Goal_target_altitude
{
public:
  Init_FlyToAltitude_Goal_target_altitude()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::uav_interfaces::action::FlyToAltitude_Goal target_altitude(::uav_interfaces::action::FlyToAltitude_Goal::_target_altitude_type arg)
  {
    msg_.target_altitude = std::move(arg);
    return std::move(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_Goal msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::uav_interfaces::action::FlyToAltitude_Goal>()
{
  return uav_interfaces::action::builder::Init_FlyToAltitude_Goal_target_altitude();
}

}  // namespace uav_interfaces


namespace uav_interfaces
{

namespace action
{

namespace builder
{

class Init_FlyToAltitude_Result_message
{
public:
  explicit Init_FlyToAltitude_Result_message(::uav_interfaces::action::FlyToAltitude_Result & msg)
  : msg_(msg)
  {}
  ::uav_interfaces::action::FlyToAltitude_Result message(::uav_interfaces::action::FlyToAltitude_Result::_message_type arg)
  {
    msg_.message = std::move(arg);
    return std::move(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_Result msg_;
};

class Init_FlyToAltitude_Result_success
{
public:
  Init_FlyToAltitude_Result_success()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FlyToAltitude_Result_message success(::uav_interfaces::action::FlyToAltitude_Result::_success_type arg)
  {
    msg_.success = std::move(arg);
    return Init_FlyToAltitude_Result_message(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_Result msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::uav_interfaces::action::FlyToAltitude_Result>()
{
  return uav_interfaces::action::builder::Init_FlyToAltitude_Result_success();
}

}  // namespace uav_interfaces


namespace uav_interfaces
{

namespace action
{

namespace builder
{

class Init_FlyToAltitude_Feedback_current_altitude
{
public:
  Init_FlyToAltitude_Feedback_current_altitude()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::uav_interfaces::action::FlyToAltitude_Feedback current_altitude(::uav_interfaces::action::FlyToAltitude_Feedback::_current_altitude_type arg)
  {
    msg_.current_altitude = std::move(arg);
    return std::move(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_Feedback msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::uav_interfaces::action::FlyToAltitude_Feedback>()
{
  return uav_interfaces::action::builder::Init_FlyToAltitude_Feedback_current_altitude();
}

}  // namespace uav_interfaces


namespace uav_interfaces
{

namespace action
{

namespace builder
{

class Init_FlyToAltitude_SendGoal_Request_goal
{
public:
  explicit Init_FlyToAltitude_SendGoal_Request_goal(::uav_interfaces::action::FlyToAltitude_SendGoal_Request & msg)
  : msg_(msg)
  {}
  ::uav_interfaces::action::FlyToAltitude_SendGoal_Request goal(::uav_interfaces::action::FlyToAltitude_SendGoal_Request::_goal_type arg)
  {
    msg_.goal = std::move(arg);
    return std::move(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_SendGoal_Request msg_;
};

class Init_FlyToAltitude_SendGoal_Request_goal_id
{
public:
  Init_FlyToAltitude_SendGoal_Request_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FlyToAltitude_SendGoal_Request_goal goal_id(::uav_interfaces::action::FlyToAltitude_SendGoal_Request::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return Init_FlyToAltitude_SendGoal_Request_goal(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_SendGoal_Request msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::uav_interfaces::action::FlyToAltitude_SendGoal_Request>()
{
  return uav_interfaces::action::builder::Init_FlyToAltitude_SendGoal_Request_goal_id();
}

}  // namespace uav_interfaces


namespace uav_interfaces
{

namespace action
{

namespace builder
{

class Init_FlyToAltitude_SendGoal_Response_stamp
{
public:
  explicit Init_FlyToAltitude_SendGoal_Response_stamp(::uav_interfaces::action::FlyToAltitude_SendGoal_Response & msg)
  : msg_(msg)
  {}
  ::uav_interfaces::action::FlyToAltitude_SendGoal_Response stamp(::uav_interfaces::action::FlyToAltitude_SendGoal_Response::_stamp_type arg)
  {
    msg_.stamp = std::move(arg);
    return std::move(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_SendGoal_Response msg_;
};

class Init_FlyToAltitude_SendGoal_Response_accepted
{
public:
  Init_FlyToAltitude_SendGoal_Response_accepted()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FlyToAltitude_SendGoal_Response_stamp accepted(::uav_interfaces::action::FlyToAltitude_SendGoal_Response::_accepted_type arg)
  {
    msg_.accepted = std::move(arg);
    return Init_FlyToAltitude_SendGoal_Response_stamp(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_SendGoal_Response msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::uav_interfaces::action::FlyToAltitude_SendGoal_Response>()
{
  return uav_interfaces::action::builder::Init_FlyToAltitude_SendGoal_Response_accepted();
}

}  // namespace uav_interfaces


namespace uav_interfaces
{

namespace action
{

namespace builder
{

class Init_FlyToAltitude_SendGoal_Event_response
{
public:
  explicit Init_FlyToAltitude_SendGoal_Event_response(::uav_interfaces::action::FlyToAltitude_SendGoal_Event & msg)
  : msg_(msg)
  {}
  ::uav_interfaces::action::FlyToAltitude_SendGoal_Event response(::uav_interfaces::action::FlyToAltitude_SendGoal_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_SendGoal_Event msg_;
};

class Init_FlyToAltitude_SendGoal_Event_request
{
public:
  explicit Init_FlyToAltitude_SendGoal_Event_request(::uav_interfaces::action::FlyToAltitude_SendGoal_Event & msg)
  : msg_(msg)
  {}
  Init_FlyToAltitude_SendGoal_Event_response request(::uav_interfaces::action::FlyToAltitude_SendGoal_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_FlyToAltitude_SendGoal_Event_response(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_SendGoal_Event msg_;
};

class Init_FlyToAltitude_SendGoal_Event_info
{
public:
  Init_FlyToAltitude_SendGoal_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FlyToAltitude_SendGoal_Event_request info(::uav_interfaces::action::FlyToAltitude_SendGoal_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_FlyToAltitude_SendGoal_Event_request(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_SendGoal_Event msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::uav_interfaces::action::FlyToAltitude_SendGoal_Event>()
{
  return uav_interfaces::action::builder::Init_FlyToAltitude_SendGoal_Event_info();
}

}  // namespace uav_interfaces


namespace uav_interfaces
{

namespace action
{

namespace builder
{

class Init_FlyToAltitude_GetResult_Request_goal_id
{
public:
  Init_FlyToAltitude_GetResult_Request_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::uav_interfaces::action::FlyToAltitude_GetResult_Request goal_id(::uav_interfaces::action::FlyToAltitude_GetResult_Request::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return std::move(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_GetResult_Request msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::uav_interfaces::action::FlyToAltitude_GetResult_Request>()
{
  return uav_interfaces::action::builder::Init_FlyToAltitude_GetResult_Request_goal_id();
}

}  // namespace uav_interfaces


namespace uav_interfaces
{

namespace action
{

namespace builder
{

class Init_FlyToAltitude_GetResult_Response_result
{
public:
  explicit Init_FlyToAltitude_GetResult_Response_result(::uav_interfaces::action::FlyToAltitude_GetResult_Response & msg)
  : msg_(msg)
  {}
  ::uav_interfaces::action::FlyToAltitude_GetResult_Response result(::uav_interfaces::action::FlyToAltitude_GetResult_Response::_result_type arg)
  {
    msg_.result = std::move(arg);
    return std::move(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_GetResult_Response msg_;
};

class Init_FlyToAltitude_GetResult_Response_status
{
public:
  Init_FlyToAltitude_GetResult_Response_status()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FlyToAltitude_GetResult_Response_result status(::uav_interfaces::action::FlyToAltitude_GetResult_Response::_status_type arg)
  {
    msg_.status = std::move(arg);
    return Init_FlyToAltitude_GetResult_Response_result(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_GetResult_Response msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::uav_interfaces::action::FlyToAltitude_GetResult_Response>()
{
  return uav_interfaces::action::builder::Init_FlyToAltitude_GetResult_Response_status();
}

}  // namespace uav_interfaces


namespace uav_interfaces
{

namespace action
{

namespace builder
{

class Init_FlyToAltitude_GetResult_Event_response
{
public:
  explicit Init_FlyToAltitude_GetResult_Event_response(::uav_interfaces::action::FlyToAltitude_GetResult_Event & msg)
  : msg_(msg)
  {}
  ::uav_interfaces::action::FlyToAltitude_GetResult_Event response(::uav_interfaces::action::FlyToAltitude_GetResult_Event::_response_type arg)
  {
    msg_.response = std::move(arg);
    return std::move(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_GetResult_Event msg_;
};

class Init_FlyToAltitude_GetResult_Event_request
{
public:
  explicit Init_FlyToAltitude_GetResult_Event_request(::uav_interfaces::action::FlyToAltitude_GetResult_Event & msg)
  : msg_(msg)
  {}
  Init_FlyToAltitude_GetResult_Event_response request(::uav_interfaces::action::FlyToAltitude_GetResult_Event::_request_type arg)
  {
    msg_.request = std::move(arg);
    return Init_FlyToAltitude_GetResult_Event_response(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_GetResult_Event msg_;
};

class Init_FlyToAltitude_GetResult_Event_info
{
public:
  Init_FlyToAltitude_GetResult_Event_info()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FlyToAltitude_GetResult_Event_request info(::uav_interfaces::action::FlyToAltitude_GetResult_Event::_info_type arg)
  {
    msg_.info = std::move(arg);
    return Init_FlyToAltitude_GetResult_Event_request(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_GetResult_Event msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::uav_interfaces::action::FlyToAltitude_GetResult_Event>()
{
  return uav_interfaces::action::builder::Init_FlyToAltitude_GetResult_Event_info();
}

}  // namespace uav_interfaces


namespace uav_interfaces
{

namespace action
{

namespace builder
{

class Init_FlyToAltitude_FeedbackMessage_feedback
{
public:
  explicit Init_FlyToAltitude_FeedbackMessage_feedback(::uav_interfaces::action::FlyToAltitude_FeedbackMessage & msg)
  : msg_(msg)
  {}
  ::uav_interfaces::action::FlyToAltitude_FeedbackMessage feedback(::uav_interfaces::action::FlyToAltitude_FeedbackMessage::_feedback_type arg)
  {
    msg_.feedback = std::move(arg);
    return std::move(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_FeedbackMessage msg_;
};

class Init_FlyToAltitude_FeedbackMessage_goal_id
{
public:
  Init_FlyToAltitude_FeedbackMessage_goal_id()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_FlyToAltitude_FeedbackMessage_feedback goal_id(::uav_interfaces::action::FlyToAltitude_FeedbackMessage::_goal_id_type arg)
  {
    msg_.goal_id = std::move(arg);
    return Init_FlyToAltitude_FeedbackMessage_feedback(msg_);
  }

private:
  ::uav_interfaces::action::FlyToAltitude_FeedbackMessage msg_;
};

}  // namespace builder

}  // namespace action

template<typename MessageType>
auto build();

template<>
inline
auto build<::uav_interfaces::action::FlyToAltitude_FeedbackMessage>()
{
  return uav_interfaces::action::builder::Init_FlyToAltitude_FeedbackMessage_goal_id();
}

}  // namespace uav_interfaces

#endif  // UAV_INTERFACES__ACTION__DETAIL__FLY_TO_ALTITUDE__BUILDER_HPP_
