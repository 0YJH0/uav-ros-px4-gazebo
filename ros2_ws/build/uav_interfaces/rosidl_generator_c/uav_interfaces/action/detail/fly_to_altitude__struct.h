// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from uav_interfaces:action/FlyToAltitude.idl
// generated code does not contain a copyright notice

// IWYU pragma: private, include "uav_interfaces/action/fly_to_altitude.h"


#ifndef UAV_INTERFACES__ACTION__DETAIL__FLY_TO_ALTITUDE__STRUCT_H_
#define UAV_INTERFACES__ACTION__DETAIL__FLY_TO_ALTITUDE__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in action/FlyToAltitude in the package uav_interfaces.
typedef struct uav_interfaces__action__FlyToAltitude_Goal
{
  float target_altitude;
} uav_interfaces__action__FlyToAltitude_Goal;

// Struct for a sequence of uav_interfaces__action__FlyToAltitude_Goal.
typedef struct uav_interfaces__action__FlyToAltitude_Goal__Sequence
{
  uav_interfaces__action__FlyToAltitude_Goal * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} uav_interfaces__action__FlyToAltitude_Goal__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'message'
#include "rosidl_runtime_c/string.h"

/// Struct defined in action/FlyToAltitude in the package uav_interfaces.
typedef struct uav_interfaces__action__FlyToAltitude_Result
{
  bool success;
  rosidl_runtime_c__String message;
} uav_interfaces__action__FlyToAltitude_Result;

// Struct for a sequence of uav_interfaces__action__FlyToAltitude_Result.
typedef struct uav_interfaces__action__FlyToAltitude_Result__Sequence
{
  uav_interfaces__action__FlyToAltitude_Result * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} uav_interfaces__action__FlyToAltitude_Result__Sequence;

// Constants defined in the message

/// Struct defined in action/FlyToAltitude in the package uav_interfaces.
typedef struct uav_interfaces__action__FlyToAltitude_Feedback
{
  float current_altitude;
} uav_interfaces__action__FlyToAltitude_Feedback;

// Struct for a sequence of uav_interfaces__action__FlyToAltitude_Feedback.
typedef struct uav_interfaces__action__FlyToAltitude_Feedback__Sequence
{
  uav_interfaces__action__FlyToAltitude_Feedback * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} uav_interfaces__action__FlyToAltitude_Feedback__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
#include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'goal'
#include "uav_interfaces/action/detail/fly_to_altitude__struct.h"

/// Struct defined in action/FlyToAltitude in the package uav_interfaces.
typedef struct uav_interfaces__action__FlyToAltitude_SendGoal_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
  uav_interfaces__action__FlyToAltitude_Goal goal;
} uav_interfaces__action__FlyToAltitude_SendGoal_Request;

// Struct for a sequence of uav_interfaces__action__FlyToAltitude_SendGoal_Request.
typedef struct uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence
{
  uav_interfaces__action__FlyToAltitude_SendGoal_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in action/FlyToAltitude in the package uav_interfaces.
typedef struct uav_interfaces__action__FlyToAltitude_SendGoal_Response
{
  bool accepted;
  builtin_interfaces__msg__Time stamp;
} uav_interfaces__action__FlyToAltitude_SendGoal_Response;

// Struct for a sequence of uav_interfaces__action__FlyToAltitude_SendGoal_Response.
typedef struct uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence
{
  uav_interfaces__action__FlyToAltitude_SendGoal_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
#include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  uav_interfaces__action__FlyToAltitude_SendGoal_Event__request__MAX_SIZE = 1
};
// response
enum
{
  uav_interfaces__action__FlyToAltitude_SendGoal_Event__response__MAX_SIZE = 1
};

/// Struct defined in action/FlyToAltitude in the package uav_interfaces.
typedef struct uav_interfaces__action__FlyToAltitude_SendGoal_Event
{
  service_msgs__msg__ServiceEventInfo info;
  uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence request;
  uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence response;
} uav_interfaces__action__FlyToAltitude_SendGoal_Event;

// Struct for a sequence of uav_interfaces__action__FlyToAltitude_SendGoal_Event.
typedef struct uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence
{
  uav_interfaces__action__FlyToAltitude_SendGoal_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"

/// Struct defined in action/FlyToAltitude in the package uav_interfaces.
typedef struct uav_interfaces__action__FlyToAltitude_GetResult_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
} uav_interfaces__action__FlyToAltitude_GetResult_Request;

// Struct for a sequence of uav_interfaces__action__FlyToAltitude_GetResult_Request.
typedef struct uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence
{
  uav_interfaces__action__FlyToAltitude_GetResult_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'result'
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__struct.h"

/// Struct defined in action/FlyToAltitude in the package uav_interfaces.
typedef struct uav_interfaces__action__FlyToAltitude_GetResult_Response
{
  int8_t status;
  uav_interfaces__action__FlyToAltitude_Result result;
} uav_interfaces__action__FlyToAltitude_GetResult_Response;

// Struct for a sequence of uav_interfaces__action__FlyToAltitude_GetResult_Response.
typedef struct uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence
{
  uav_interfaces__action__FlyToAltitude_GetResult_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'info'
// already included above
// #include "service_msgs/msg/detail/service_event_info__struct.h"

// constants for array fields with an upper bound
// request
enum
{
  uav_interfaces__action__FlyToAltitude_GetResult_Event__request__MAX_SIZE = 1
};
// response
enum
{
  uav_interfaces__action__FlyToAltitude_GetResult_Event__response__MAX_SIZE = 1
};

/// Struct defined in action/FlyToAltitude in the package uav_interfaces.
typedef struct uav_interfaces__action__FlyToAltitude_GetResult_Event
{
  service_msgs__msg__ServiceEventInfo info;
  uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence request;
  uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence response;
} uav_interfaces__action__FlyToAltitude_GetResult_Event;

// Struct for a sequence of uav_interfaces__action__FlyToAltitude_GetResult_Event.
typedef struct uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence
{
  uav_interfaces__action__FlyToAltitude_GetResult_Event * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence;

// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'feedback'
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__struct.h"

/// Struct defined in action/FlyToAltitude in the package uav_interfaces.
typedef struct uav_interfaces__action__FlyToAltitude_FeedbackMessage
{
  unique_identifier_msgs__msg__UUID goal_id;
  uav_interfaces__action__FlyToAltitude_Feedback feedback;
} uav_interfaces__action__FlyToAltitude_FeedbackMessage;

// Struct for a sequence of uav_interfaces__action__FlyToAltitude_FeedbackMessage.
typedef struct uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence
{
  uav_interfaces__action__FlyToAltitude_FeedbackMessage * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // UAV_INTERFACES__ACTION__DETAIL__FLY_TO_ALTITUDE__STRUCT_H_
