// generated from rosidl_generator_c/resource/idl__description.c.em
// with input from uav_interfaces:msg/TargetDetection.idl
// generated code does not contain a copyright notice

#include "uav_interfaces/msg/detail/target_detection__functions.h"

ROSIDL_GENERATOR_C_PUBLIC_uav_interfaces
const rosidl_type_hash_t *
uav_interfaces__msg__TargetDetection__get_type_hash(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_type_hash_t hash = {1, {
      0x8d, 0x9e, 0x58, 0x15, 0x15, 0xbd, 0x3d, 0x49,
      0xa5, 0xc5, 0xea, 0xeb, 0xa7, 0x50, 0x0f, 0x31,
      0x16, 0xec, 0xea, 0x70, 0x12, 0x84, 0x67, 0x43,
      0x64, 0x62, 0xc0, 0x87, 0x21, 0x98, 0x63, 0x84,
    }};
  return &hash;
}

#include <assert.h>
#include <string.h>

// Include directives for referenced types
#include "builtin_interfaces/msg/detail/time__functions.h"

// Hashes for external referenced types
#ifndef NDEBUG
static const rosidl_type_hash_t builtin_interfaces__msg__Time__EXPECTED_HASH = {1, {
    0xb1, 0x06, 0x23, 0x5e, 0x25, 0xa4, 0xc5, 0xed,
    0x35, 0x09, 0x8a, 0xa0, 0xa6, 0x1a, 0x3e, 0xe9,
    0xc9, 0xb1, 0x8d, 0x19, 0x7f, 0x39, 0x8b, 0x0e,
    0x42, 0x06, 0xce, 0xa9, 0xac, 0xf9, 0xc1, 0x97,
  }};
#endif

static char uav_interfaces__msg__TargetDetection__TYPE_NAME[] = "uav_interfaces/msg/TargetDetection";
static char builtin_interfaces__msg__Time__TYPE_NAME[] = "builtin_interfaces/msg/Time";

// Define type names, field names, and default values
static char uav_interfaces__msg__TargetDetection__FIELD_NAME__stamp[] = "stamp";
static char uav_interfaces__msg__TargetDetection__FIELD_NAME__detected[] = "detected";
static char uav_interfaces__msg__TargetDetection__FIELD_NAME__confidence[] = "confidence";
static char uav_interfaces__msg__TargetDetection__FIELD_NAME__center_u[] = "center_u";
static char uav_interfaces__msg__TargetDetection__FIELD_NAME__center_v[] = "center_v";
static char uav_interfaces__msg__TargetDetection__FIELD_NAME__center_u_norm[] = "center_u_norm";
static char uav_interfaces__msg__TargetDetection__FIELD_NAME__center_v_norm[] = "center_v_norm";
static char uav_interfaces__msg__TargetDetection__FIELD_NAME__bbox_x[] = "bbox_x";
static char uav_interfaces__msg__TargetDetection__FIELD_NAME__bbox_y[] = "bbox_y";
static char uav_interfaces__msg__TargetDetection__FIELD_NAME__bbox_width[] = "bbox_width";
static char uav_interfaces__msg__TargetDetection__FIELD_NAME__bbox_height[] = "bbox_height";
static char uav_interfaces__msg__TargetDetection__FIELD_NAME__area_ratio[] = "area_ratio";

static rosidl_runtime_c__type_description__Field uav_interfaces__msg__TargetDetection__FIELDS[] = {
  {
    {uav_interfaces__msg__TargetDetection__FIELD_NAME__stamp, 5, 5},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_NESTED_TYPE,
      0,
      0,
      {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    },
    {NULL, 0, 0},
  },
  {
    {uav_interfaces__msg__TargetDetection__FIELD_NAME__detected, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_BOOLEAN,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {uav_interfaces__msg__TargetDetection__FIELD_NAME__confidence, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {uav_interfaces__msg__TargetDetection__FIELD_NAME__center_u, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {uav_interfaces__msg__TargetDetection__FIELD_NAME__center_v, 8, 8},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {uav_interfaces__msg__TargetDetection__FIELD_NAME__center_u_norm, 13, 13},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {uav_interfaces__msg__TargetDetection__FIELD_NAME__center_v_norm, 13, 13},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {uav_interfaces__msg__TargetDetection__FIELD_NAME__bbox_x, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {uav_interfaces__msg__TargetDetection__FIELD_NAME__bbox_y, 6, 6},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {uav_interfaces__msg__TargetDetection__FIELD_NAME__bbox_width, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {uav_interfaces__msg__TargetDetection__FIELD_NAME__bbox_height, 11, 11},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
  {
    {uav_interfaces__msg__TargetDetection__FIELD_NAME__area_ratio, 10, 10},
    {
      rosidl_runtime_c__type_description__FieldType__FIELD_TYPE_FLOAT,
      0,
      0,
      {NULL, 0, 0},
    },
    {NULL, 0, 0},
  },
};

static rosidl_runtime_c__type_description__IndividualTypeDescription uav_interfaces__msg__TargetDetection__REFERENCED_TYPE_DESCRIPTIONS[] = {
  {
    {builtin_interfaces__msg__Time__TYPE_NAME, 27, 27},
    {NULL, 0, 0},
  },
};

const rosidl_runtime_c__type_description__TypeDescription *
uav_interfaces__msg__TargetDetection__get_type_description(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static bool constructed = false;
  static const rosidl_runtime_c__type_description__TypeDescription description = {
    {
      {uav_interfaces__msg__TargetDetection__TYPE_NAME, 34, 34},
      {uav_interfaces__msg__TargetDetection__FIELDS, 12, 12},
    },
    {uav_interfaces__msg__TargetDetection__REFERENCED_TYPE_DESCRIPTIONS, 1, 1},
  };
  if (!constructed) {
    assert(0 == memcmp(&builtin_interfaces__msg__Time__EXPECTED_HASH, builtin_interfaces__msg__Time__get_type_hash(NULL), sizeof(rosidl_type_hash_t)));
    description.referenced_type_descriptions.data[0].fields = builtin_interfaces__msg__Time__get_type_description(NULL)->type_description.fields;
    constructed = true;
  }
  return &description;
}

static char toplevel_type_raw_source[] =
  "builtin_interfaces/Time stamp\n"
  "\n"
  "bool detected\n"
  "\n"
  "float32 confidence\n"
  "\n"
  "float32 center_u\n"
  "float32 center_v\n"
  "\n"
  "float32 center_u_norm\n"
  "float32 center_v_norm\n"
  "\n"
  "float32 bbox_x\n"
  "float32 bbox_y\n"
  "float32 bbox_width\n"
  "float32 bbox_height\n"
  "\n"
  "float32 area_ratio";

static char msg_encoding[] = "msg";

// Define all individual source functions

const rosidl_runtime_c__type_description__TypeSource *
uav_interfaces__msg__TargetDetection__get_individual_type_description_source(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static const rosidl_runtime_c__type_description__TypeSource source = {
    {uav_interfaces__msg__TargetDetection__TYPE_NAME, 34, 34},
    {msg_encoding, 3, 3},
    {toplevel_type_raw_source, 234, 234},
  };
  return &source;
}

const rosidl_runtime_c__type_description__TypeSource__Sequence *
uav_interfaces__msg__TargetDetection__get_type_description_sources(
  const rosidl_message_type_support_t * type_support)
{
  (void)type_support;
  static rosidl_runtime_c__type_description__TypeSource sources[2];
  static const rosidl_runtime_c__type_description__TypeSource__Sequence source_sequence = {sources, 2, 2};
  static bool constructed = false;
  if (!constructed) {
    sources[0] = *uav_interfaces__msg__TargetDetection__get_individual_type_description_source(NULL),
    sources[1] = *builtin_interfaces__msg__Time__get_individual_type_description_source(NULL);
    constructed = true;
  }
  return &source_sequence;
}
