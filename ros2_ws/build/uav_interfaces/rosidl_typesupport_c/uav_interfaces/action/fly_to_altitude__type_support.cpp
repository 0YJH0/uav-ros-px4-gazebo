// generated from rosidl_typesupport_c/resource/idl__type_support.cpp.em
// with input from uav_interfaces:action/FlyToAltitude.idl
// generated code does not contain a copyright notice

#include "cstddef"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "uav_interfaces/action/detail/fly_to_altitude__struct.h"
#include "uav_interfaces/action/detail/fly_to_altitude__type_support.h"
#include "uav_interfaces/action/detail/fly_to_altitude__functions.h"
#include "rosidl_typesupport_c/identifier.h"
#include "rosidl_typesupport_c/message_type_support_dispatch.h"
#include "rosidl_typesupport_c/type_support_map.h"
#include "rosidl_typesupport_c/visibility_control.h"
#include "rosidl_typesupport_interface/macros.h"

namespace uav_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _FlyToAltitude_Goal_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _FlyToAltitude_Goal_type_support_ids_t;

static const _FlyToAltitude_Goal_type_support_ids_t _FlyToAltitude_Goal_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _FlyToAltitude_Goal_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _FlyToAltitude_Goal_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _FlyToAltitude_Goal_type_support_symbol_names_t _FlyToAltitude_Goal_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, uav_interfaces, action, FlyToAltitude_Goal)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, uav_interfaces, action, FlyToAltitude_Goal)),
  }
};

typedef struct _FlyToAltitude_Goal_type_support_data_t
{
  void * data[2];
} _FlyToAltitude_Goal_type_support_data_t;

static _FlyToAltitude_Goal_type_support_data_t _FlyToAltitude_Goal_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _FlyToAltitude_Goal_message_typesupport_map = {
  2,
  "uav_interfaces",
  &_FlyToAltitude_Goal_message_typesupport_ids.typesupport_identifier[0],
  &_FlyToAltitude_Goal_message_typesupport_symbol_names.symbol_name[0],
  &_FlyToAltitude_Goal_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t FlyToAltitude_Goal_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_FlyToAltitude_Goal_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
  &uav_interfaces__action__FlyToAltitude_Goal__get_type_hash,
  &uav_interfaces__action__FlyToAltitude_Goal__get_type_description,
  &uav_interfaces__action__FlyToAltitude_Goal__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace uav_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_Goal)() {
  return &::uav_interfaces::action::rosidl_typesupport_c::FlyToAltitude_Goal_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__type_support.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__functions.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace uav_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _FlyToAltitude_Result_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _FlyToAltitude_Result_type_support_ids_t;

static const _FlyToAltitude_Result_type_support_ids_t _FlyToAltitude_Result_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _FlyToAltitude_Result_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _FlyToAltitude_Result_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _FlyToAltitude_Result_type_support_symbol_names_t _FlyToAltitude_Result_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, uav_interfaces, action, FlyToAltitude_Result)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, uav_interfaces, action, FlyToAltitude_Result)),
  }
};

typedef struct _FlyToAltitude_Result_type_support_data_t
{
  void * data[2];
} _FlyToAltitude_Result_type_support_data_t;

static _FlyToAltitude_Result_type_support_data_t _FlyToAltitude_Result_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _FlyToAltitude_Result_message_typesupport_map = {
  2,
  "uav_interfaces",
  &_FlyToAltitude_Result_message_typesupport_ids.typesupport_identifier[0],
  &_FlyToAltitude_Result_message_typesupport_symbol_names.symbol_name[0],
  &_FlyToAltitude_Result_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t FlyToAltitude_Result_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_FlyToAltitude_Result_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
  &uav_interfaces__action__FlyToAltitude_Result__get_type_hash,
  &uav_interfaces__action__FlyToAltitude_Result__get_type_description,
  &uav_interfaces__action__FlyToAltitude_Result__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace uav_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_Result)() {
  return &::uav_interfaces::action::rosidl_typesupport_c::FlyToAltitude_Result_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__type_support.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__functions.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace uav_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _FlyToAltitude_Feedback_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _FlyToAltitude_Feedback_type_support_ids_t;

static const _FlyToAltitude_Feedback_type_support_ids_t _FlyToAltitude_Feedback_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _FlyToAltitude_Feedback_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _FlyToAltitude_Feedback_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _FlyToAltitude_Feedback_type_support_symbol_names_t _FlyToAltitude_Feedback_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, uav_interfaces, action, FlyToAltitude_Feedback)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, uav_interfaces, action, FlyToAltitude_Feedback)),
  }
};

typedef struct _FlyToAltitude_Feedback_type_support_data_t
{
  void * data[2];
} _FlyToAltitude_Feedback_type_support_data_t;

static _FlyToAltitude_Feedback_type_support_data_t _FlyToAltitude_Feedback_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _FlyToAltitude_Feedback_message_typesupport_map = {
  2,
  "uav_interfaces",
  &_FlyToAltitude_Feedback_message_typesupport_ids.typesupport_identifier[0],
  &_FlyToAltitude_Feedback_message_typesupport_symbol_names.symbol_name[0],
  &_FlyToAltitude_Feedback_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t FlyToAltitude_Feedback_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_FlyToAltitude_Feedback_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
  &uav_interfaces__action__FlyToAltitude_Feedback__get_type_hash,
  &uav_interfaces__action__FlyToAltitude_Feedback__get_type_description,
  &uav_interfaces__action__FlyToAltitude_Feedback__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace uav_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_Feedback)() {
  return &::uav_interfaces::action::rosidl_typesupport_c::FlyToAltitude_Feedback_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__type_support.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__functions.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace uav_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _FlyToAltitude_SendGoal_Request_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _FlyToAltitude_SendGoal_Request_type_support_ids_t;

static const _FlyToAltitude_SendGoal_Request_type_support_ids_t _FlyToAltitude_SendGoal_Request_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _FlyToAltitude_SendGoal_Request_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _FlyToAltitude_SendGoal_Request_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _FlyToAltitude_SendGoal_Request_type_support_symbol_names_t _FlyToAltitude_SendGoal_Request_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, uav_interfaces, action, FlyToAltitude_SendGoal_Request)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, uav_interfaces, action, FlyToAltitude_SendGoal_Request)),
  }
};

typedef struct _FlyToAltitude_SendGoal_Request_type_support_data_t
{
  void * data[2];
} _FlyToAltitude_SendGoal_Request_type_support_data_t;

static _FlyToAltitude_SendGoal_Request_type_support_data_t _FlyToAltitude_SendGoal_Request_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _FlyToAltitude_SendGoal_Request_message_typesupport_map = {
  2,
  "uav_interfaces",
  &_FlyToAltitude_SendGoal_Request_message_typesupport_ids.typesupport_identifier[0],
  &_FlyToAltitude_SendGoal_Request_message_typesupport_symbol_names.symbol_name[0],
  &_FlyToAltitude_SendGoal_Request_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t FlyToAltitude_SendGoal_Request_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_FlyToAltitude_SendGoal_Request_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
  &uav_interfaces__action__FlyToAltitude_SendGoal_Request__get_type_hash,
  &uav_interfaces__action__FlyToAltitude_SendGoal_Request__get_type_description,
  &uav_interfaces__action__FlyToAltitude_SendGoal_Request__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace uav_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_SendGoal_Request)() {
  return &::uav_interfaces::action::rosidl_typesupport_c::FlyToAltitude_SendGoal_Request_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__type_support.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__functions.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace uav_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _FlyToAltitude_SendGoal_Response_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _FlyToAltitude_SendGoal_Response_type_support_ids_t;

static const _FlyToAltitude_SendGoal_Response_type_support_ids_t _FlyToAltitude_SendGoal_Response_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _FlyToAltitude_SendGoal_Response_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _FlyToAltitude_SendGoal_Response_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _FlyToAltitude_SendGoal_Response_type_support_symbol_names_t _FlyToAltitude_SendGoal_Response_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, uav_interfaces, action, FlyToAltitude_SendGoal_Response)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, uav_interfaces, action, FlyToAltitude_SendGoal_Response)),
  }
};

typedef struct _FlyToAltitude_SendGoal_Response_type_support_data_t
{
  void * data[2];
} _FlyToAltitude_SendGoal_Response_type_support_data_t;

static _FlyToAltitude_SendGoal_Response_type_support_data_t _FlyToAltitude_SendGoal_Response_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _FlyToAltitude_SendGoal_Response_message_typesupport_map = {
  2,
  "uav_interfaces",
  &_FlyToAltitude_SendGoal_Response_message_typesupport_ids.typesupport_identifier[0],
  &_FlyToAltitude_SendGoal_Response_message_typesupport_symbol_names.symbol_name[0],
  &_FlyToAltitude_SendGoal_Response_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t FlyToAltitude_SendGoal_Response_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_FlyToAltitude_SendGoal_Response_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
  &uav_interfaces__action__FlyToAltitude_SendGoal_Response__get_type_hash,
  &uav_interfaces__action__FlyToAltitude_SendGoal_Response__get_type_description,
  &uav_interfaces__action__FlyToAltitude_SendGoal_Response__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace uav_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_SendGoal_Response)() {
  return &::uav_interfaces::action::rosidl_typesupport_c::FlyToAltitude_SendGoal_Response_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__type_support.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__functions.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace uav_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _FlyToAltitude_SendGoal_Event_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _FlyToAltitude_SendGoal_Event_type_support_ids_t;

static const _FlyToAltitude_SendGoal_Event_type_support_ids_t _FlyToAltitude_SendGoal_Event_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _FlyToAltitude_SendGoal_Event_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _FlyToAltitude_SendGoal_Event_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _FlyToAltitude_SendGoal_Event_type_support_symbol_names_t _FlyToAltitude_SendGoal_Event_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, uav_interfaces, action, FlyToAltitude_SendGoal_Event)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, uav_interfaces, action, FlyToAltitude_SendGoal_Event)),
  }
};

typedef struct _FlyToAltitude_SendGoal_Event_type_support_data_t
{
  void * data[2];
} _FlyToAltitude_SendGoal_Event_type_support_data_t;

static _FlyToAltitude_SendGoal_Event_type_support_data_t _FlyToAltitude_SendGoal_Event_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _FlyToAltitude_SendGoal_Event_message_typesupport_map = {
  2,
  "uav_interfaces",
  &_FlyToAltitude_SendGoal_Event_message_typesupport_ids.typesupport_identifier[0],
  &_FlyToAltitude_SendGoal_Event_message_typesupport_symbol_names.symbol_name[0],
  &_FlyToAltitude_SendGoal_Event_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t FlyToAltitude_SendGoal_Event_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_FlyToAltitude_SendGoal_Event_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
  &uav_interfaces__action__FlyToAltitude_SendGoal_Event__get_type_hash,
  &uav_interfaces__action__FlyToAltitude_SendGoal_Event__get_type_description,
  &uav_interfaces__action__FlyToAltitude_SendGoal_Event__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace uav_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_SendGoal_Event)() {
  return &::uav_interfaces::action::rosidl_typesupport_c::FlyToAltitude_SendGoal_Event_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
#include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__type_support.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
#include "rosidl_typesupport_c/service_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"
#include "service_msgs/msg/service_event_info.h"
#include "builtin_interfaces/msg/time.h"

namespace uav_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{
typedef struct _FlyToAltitude_SendGoal_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _FlyToAltitude_SendGoal_type_support_ids_t;

static const _FlyToAltitude_SendGoal_type_support_ids_t _FlyToAltitude_SendGoal_service_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _FlyToAltitude_SendGoal_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _FlyToAltitude_SendGoal_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _FlyToAltitude_SendGoal_type_support_symbol_names_t _FlyToAltitude_SendGoal_service_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, uav_interfaces, action, FlyToAltitude_SendGoal)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, uav_interfaces, action, FlyToAltitude_SendGoal)),
  }
};

typedef struct _FlyToAltitude_SendGoal_type_support_data_t
{
  void * data[2];
} _FlyToAltitude_SendGoal_type_support_data_t;

static _FlyToAltitude_SendGoal_type_support_data_t _FlyToAltitude_SendGoal_service_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _FlyToAltitude_SendGoal_service_typesupport_map = {
  2,
  "uav_interfaces",
  &_FlyToAltitude_SendGoal_service_typesupport_ids.typesupport_identifier[0],
  &_FlyToAltitude_SendGoal_service_typesupport_symbol_names.symbol_name[0],
  &_FlyToAltitude_SendGoal_service_typesupport_data.data[0],
};

static const rosidl_service_type_support_t FlyToAltitude_SendGoal_service_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_FlyToAltitude_SendGoal_service_typesupport_map),
  rosidl_typesupport_c__get_service_typesupport_handle_function,
  &FlyToAltitude_SendGoal_Request_message_type_support_handle,
  &FlyToAltitude_SendGoal_Response_message_type_support_handle,
  &FlyToAltitude_SendGoal_Event_message_type_support_handle,
  ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_CREATE_EVENT_MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_c,
    uav_interfaces,
    action,
    FlyToAltitude_SendGoal
  ),
  ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_DESTROY_EVENT_MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_c,
    uav_interfaces,
    action,
    FlyToAltitude_SendGoal
  ),
  &uav_interfaces__action__FlyToAltitude_SendGoal__get_type_hash,
  &uav_interfaces__action__FlyToAltitude_SendGoal__get_type_description,
  &uav_interfaces__action__FlyToAltitude_SendGoal__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace uav_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_SendGoal)() {
  return &::uav_interfaces::action::rosidl_typesupport_c::FlyToAltitude_SendGoal_service_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__type_support.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__functions.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace uav_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _FlyToAltitude_GetResult_Request_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _FlyToAltitude_GetResult_Request_type_support_ids_t;

static const _FlyToAltitude_GetResult_Request_type_support_ids_t _FlyToAltitude_GetResult_Request_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _FlyToAltitude_GetResult_Request_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _FlyToAltitude_GetResult_Request_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _FlyToAltitude_GetResult_Request_type_support_symbol_names_t _FlyToAltitude_GetResult_Request_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, uav_interfaces, action, FlyToAltitude_GetResult_Request)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, uav_interfaces, action, FlyToAltitude_GetResult_Request)),
  }
};

typedef struct _FlyToAltitude_GetResult_Request_type_support_data_t
{
  void * data[2];
} _FlyToAltitude_GetResult_Request_type_support_data_t;

static _FlyToAltitude_GetResult_Request_type_support_data_t _FlyToAltitude_GetResult_Request_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _FlyToAltitude_GetResult_Request_message_typesupport_map = {
  2,
  "uav_interfaces",
  &_FlyToAltitude_GetResult_Request_message_typesupport_ids.typesupport_identifier[0],
  &_FlyToAltitude_GetResult_Request_message_typesupport_symbol_names.symbol_name[0],
  &_FlyToAltitude_GetResult_Request_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t FlyToAltitude_GetResult_Request_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_FlyToAltitude_GetResult_Request_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
  &uav_interfaces__action__FlyToAltitude_GetResult_Request__get_type_hash,
  &uav_interfaces__action__FlyToAltitude_GetResult_Request__get_type_description,
  &uav_interfaces__action__FlyToAltitude_GetResult_Request__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace uav_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_GetResult_Request)() {
  return &::uav_interfaces::action::rosidl_typesupport_c::FlyToAltitude_GetResult_Request_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__type_support.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__functions.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace uav_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _FlyToAltitude_GetResult_Response_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _FlyToAltitude_GetResult_Response_type_support_ids_t;

static const _FlyToAltitude_GetResult_Response_type_support_ids_t _FlyToAltitude_GetResult_Response_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _FlyToAltitude_GetResult_Response_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _FlyToAltitude_GetResult_Response_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _FlyToAltitude_GetResult_Response_type_support_symbol_names_t _FlyToAltitude_GetResult_Response_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, uav_interfaces, action, FlyToAltitude_GetResult_Response)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, uav_interfaces, action, FlyToAltitude_GetResult_Response)),
  }
};

typedef struct _FlyToAltitude_GetResult_Response_type_support_data_t
{
  void * data[2];
} _FlyToAltitude_GetResult_Response_type_support_data_t;

static _FlyToAltitude_GetResult_Response_type_support_data_t _FlyToAltitude_GetResult_Response_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _FlyToAltitude_GetResult_Response_message_typesupport_map = {
  2,
  "uav_interfaces",
  &_FlyToAltitude_GetResult_Response_message_typesupport_ids.typesupport_identifier[0],
  &_FlyToAltitude_GetResult_Response_message_typesupport_symbol_names.symbol_name[0],
  &_FlyToAltitude_GetResult_Response_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t FlyToAltitude_GetResult_Response_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_FlyToAltitude_GetResult_Response_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
  &uav_interfaces__action__FlyToAltitude_GetResult_Response__get_type_hash,
  &uav_interfaces__action__FlyToAltitude_GetResult_Response__get_type_description,
  &uav_interfaces__action__FlyToAltitude_GetResult_Response__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace uav_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_GetResult_Response)() {
  return &::uav_interfaces::action::rosidl_typesupport_c::FlyToAltitude_GetResult_Response_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__type_support.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__functions.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace uav_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _FlyToAltitude_GetResult_Event_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _FlyToAltitude_GetResult_Event_type_support_ids_t;

static const _FlyToAltitude_GetResult_Event_type_support_ids_t _FlyToAltitude_GetResult_Event_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _FlyToAltitude_GetResult_Event_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _FlyToAltitude_GetResult_Event_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _FlyToAltitude_GetResult_Event_type_support_symbol_names_t _FlyToAltitude_GetResult_Event_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, uav_interfaces, action, FlyToAltitude_GetResult_Event)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, uav_interfaces, action, FlyToAltitude_GetResult_Event)),
  }
};

typedef struct _FlyToAltitude_GetResult_Event_type_support_data_t
{
  void * data[2];
} _FlyToAltitude_GetResult_Event_type_support_data_t;

static _FlyToAltitude_GetResult_Event_type_support_data_t _FlyToAltitude_GetResult_Event_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _FlyToAltitude_GetResult_Event_message_typesupport_map = {
  2,
  "uav_interfaces",
  &_FlyToAltitude_GetResult_Event_message_typesupport_ids.typesupport_identifier[0],
  &_FlyToAltitude_GetResult_Event_message_typesupport_symbol_names.symbol_name[0],
  &_FlyToAltitude_GetResult_Event_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t FlyToAltitude_GetResult_Event_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_FlyToAltitude_GetResult_Event_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
  &uav_interfaces__action__FlyToAltitude_GetResult_Event__get_type_hash,
  &uav_interfaces__action__FlyToAltitude_GetResult_Event__get_type_description,
  &uav_interfaces__action__FlyToAltitude_GetResult_Event__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace uav_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_GetResult_Event)() {
  return &::uav_interfaces::action::rosidl_typesupport_c::FlyToAltitude_GetResult_Event_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/service_type_support_struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__type_support.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/service_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"
// already included above
// #include "service_msgs/msg/service_event_info.h"
// already included above
// #include "builtin_interfaces/msg/time.h"

namespace uav_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{
typedef struct _FlyToAltitude_GetResult_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _FlyToAltitude_GetResult_type_support_ids_t;

static const _FlyToAltitude_GetResult_type_support_ids_t _FlyToAltitude_GetResult_service_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _FlyToAltitude_GetResult_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _FlyToAltitude_GetResult_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _FlyToAltitude_GetResult_type_support_symbol_names_t _FlyToAltitude_GetResult_service_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, uav_interfaces, action, FlyToAltitude_GetResult)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_introspection_c, uav_interfaces, action, FlyToAltitude_GetResult)),
  }
};

typedef struct _FlyToAltitude_GetResult_type_support_data_t
{
  void * data[2];
} _FlyToAltitude_GetResult_type_support_data_t;

static _FlyToAltitude_GetResult_type_support_data_t _FlyToAltitude_GetResult_service_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _FlyToAltitude_GetResult_service_typesupport_map = {
  2,
  "uav_interfaces",
  &_FlyToAltitude_GetResult_service_typesupport_ids.typesupport_identifier[0],
  &_FlyToAltitude_GetResult_service_typesupport_symbol_names.symbol_name[0],
  &_FlyToAltitude_GetResult_service_typesupport_data.data[0],
};

static const rosidl_service_type_support_t FlyToAltitude_GetResult_service_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_FlyToAltitude_GetResult_service_typesupport_map),
  rosidl_typesupport_c__get_service_typesupport_handle_function,
  &FlyToAltitude_GetResult_Request_message_type_support_handle,
  &FlyToAltitude_GetResult_Response_message_type_support_handle,
  &FlyToAltitude_GetResult_Event_message_type_support_handle,
  ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_CREATE_EVENT_MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_c,
    uav_interfaces,
    action,
    FlyToAltitude_GetResult
  ),
  ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_DESTROY_EVENT_MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_c,
    uav_interfaces,
    action,
    FlyToAltitude_GetResult
  ),
  &uav_interfaces__action__FlyToAltitude_GetResult__get_type_hash,
  &uav_interfaces__action__FlyToAltitude_GetResult__get_type_description,
  &uav_interfaces__action__FlyToAltitude_GetResult__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace uav_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_service_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_GetResult)() {
  return &::uav_interfaces::action::rosidl_typesupport_c::FlyToAltitude_GetResult_service_type_support_handle;
}

#ifdef __cplusplus
}
#endif

// already included above
// #include "cstddef"
// already included above
// #include "rosidl_runtime_c/message_type_support_struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__struct.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__type_support.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__functions.h"
// already included above
// #include "rosidl_typesupport_c/identifier.h"
// already included above
// #include "rosidl_typesupport_c/message_type_support_dispatch.h"
// already included above
// #include "rosidl_typesupport_c/type_support_map.h"
// already included above
// #include "rosidl_typesupport_c/visibility_control.h"
// already included above
// #include "rosidl_typesupport_interface/macros.h"

namespace uav_interfaces
{

namespace action
{

namespace rosidl_typesupport_c
{

typedef struct _FlyToAltitude_FeedbackMessage_type_support_ids_t
{
  const char * typesupport_identifier[2];
} _FlyToAltitude_FeedbackMessage_type_support_ids_t;

static const _FlyToAltitude_FeedbackMessage_type_support_ids_t _FlyToAltitude_FeedbackMessage_message_typesupport_ids = {
  {
    "rosidl_typesupport_fastrtps_c",  // ::rosidl_typesupport_fastrtps_c::typesupport_identifier,
    "rosidl_typesupport_introspection_c",  // ::rosidl_typesupport_introspection_c::typesupport_identifier,
  }
};

typedef struct _FlyToAltitude_FeedbackMessage_type_support_symbol_names_t
{
  const char * symbol_name[2];
} _FlyToAltitude_FeedbackMessage_type_support_symbol_names_t;

#define STRINGIFY_(s) #s
#define STRINGIFY(s) STRINGIFY_(s)

static const _FlyToAltitude_FeedbackMessage_type_support_symbol_names_t _FlyToAltitude_FeedbackMessage_message_typesupport_symbol_names = {
  {
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, uav_interfaces, action, FlyToAltitude_FeedbackMessage)),
    STRINGIFY(ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, uav_interfaces, action, FlyToAltitude_FeedbackMessage)),
  }
};

typedef struct _FlyToAltitude_FeedbackMessage_type_support_data_t
{
  void * data[2];
} _FlyToAltitude_FeedbackMessage_type_support_data_t;

static _FlyToAltitude_FeedbackMessage_type_support_data_t _FlyToAltitude_FeedbackMessage_message_typesupport_data = {
  {
    0,  // will store the shared library later
    0,  // will store the shared library later
  }
};

static const type_support_map_t _FlyToAltitude_FeedbackMessage_message_typesupport_map = {
  2,
  "uav_interfaces",
  &_FlyToAltitude_FeedbackMessage_message_typesupport_ids.typesupport_identifier[0],
  &_FlyToAltitude_FeedbackMessage_message_typesupport_symbol_names.symbol_name[0],
  &_FlyToAltitude_FeedbackMessage_message_typesupport_data.data[0],
};

static const rosidl_message_type_support_t FlyToAltitude_FeedbackMessage_message_type_support_handle = {
  rosidl_typesupport_c__typesupport_identifier,
  reinterpret_cast<const type_support_map_t *>(&_FlyToAltitude_FeedbackMessage_message_typesupport_map),
  rosidl_typesupport_c__get_message_typesupport_handle_function,
  &uav_interfaces__action__FlyToAltitude_FeedbackMessage__get_type_hash,
  &uav_interfaces__action__FlyToAltitude_FeedbackMessage__get_type_description,
  &uav_interfaces__action__FlyToAltitude_FeedbackMessage__get_type_description_sources,
};

}  // namespace rosidl_typesupport_c

}  // namespace action

}  // namespace uav_interfaces

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_FeedbackMessage)() {
  return &::uav_interfaces::action::rosidl_typesupport_c::FlyToAltitude_FeedbackMessage_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif

#include "action_msgs/msg/goal_status_array.h"
#include "action_msgs/srv/cancel_goal.h"
#include "uav_interfaces/action/fly_to_altitude.h"
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__type_support.h"

static rosidl_action_type_support_t _uav_interfaces__action__FlyToAltitude__typesupport_c = {
  NULL, NULL, NULL, NULL, NULL,
  &uav_interfaces__action__FlyToAltitude__get_type_hash,
  &uav_interfaces__action__FlyToAltitude__get_type_description,
  &uav_interfaces__action__FlyToAltitude__get_type_description_sources,
};

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_action_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__ACTION_SYMBOL_NAME(
  rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude)()
{
  // Thread-safe by always writing the same values to the static struct
  _uav_interfaces__action__FlyToAltitude__typesupport_c.goal_service_type_support =
    ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(
    rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_SendGoal)();
  _uav_interfaces__action__FlyToAltitude__typesupport_c.result_service_type_support =
    ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(
    rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_GetResult)();
  _uav_interfaces__action__FlyToAltitude__typesupport_c.cancel_service_type_support =
    ROSIDL_TYPESUPPORT_INTERFACE__SERVICE_SYMBOL_NAME(
    rosidl_typesupport_c, action_msgs, srv, CancelGoal)();
  _uav_interfaces__action__FlyToAltitude__typesupport_c.feedback_message_type_support =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_c, uav_interfaces, action, FlyToAltitude_FeedbackMessage)();
  _uav_interfaces__action__FlyToAltitude__typesupport_c.status_message_type_support =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
    rosidl_typesupport_c, action_msgs, msg, GoalStatusArray)();

  return &_uav_interfaces__action__FlyToAltitude__typesupport_c;
}

#ifdef __cplusplus
}
#endif
