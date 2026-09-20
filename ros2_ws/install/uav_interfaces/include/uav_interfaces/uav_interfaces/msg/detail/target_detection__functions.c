// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from uav_interfaces:msg/TargetDetection.idl
// generated code does not contain a copyright notice
#include "uav_interfaces/msg/detail/target_detection__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `stamp`
#include "builtin_interfaces/msg/detail/time__functions.h"

bool
uav_interfaces__msg__TargetDetection__init(uav_interfaces__msg__TargetDetection * msg)
{
  if (!msg) {
    return false;
  }
  // stamp
  if (!builtin_interfaces__msg__Time__init(&msg->stamp)) {
    uav_interfaces__msg__TargetDetection__fini(msg);
    return false;
  }
  // detected
  // confidence
  // center_u
  // center_v
  // center_u_norm
  // center_v_norm
  // bbox_x
  // bbox_y
  // bbox_width
  // bbox_height
  // area_ratio
  return true;
}

void
uav_interfaces__msg__TargetDetection__fini(uav_interfaces__msg__TargetDetection * msg)
{
  if (!msg) {
    return;
  }
  // stamp
  builtin_interfaces__msg__Time__fini(&msg->stamp);
  // detected
  // confidence
  // center_u
  // center_v
  // center_u_norm
  // center_v_norm
  // bbox_x
  // bbox_y
  // bbox_width
  // bbox_height
  // area_ratio
}

bool
uav_interfaces__msg__TargetDetection__are_equal(const uav_interfaces__msg__TargetDetection * lhs, const uav_interfaces__msg__TargetDetection * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // stamp
  if (!builtin_interfaces__msg__Time__are_equal(
      &(lhs->stamp), &(rhs->stamp)))
  {
    return false;
  }
  // detected
  if (lhs->detected != rhs->detected) {
    return false;
  }
  // confidence
  if (lhs->confidence != rhs->confidence) {
    return false;
  }
  // center_u
  if (lhs->center_u != rhs->center_u) {
    return false;
  }
  // center_v
  if (lhs->center_v != rhs->center_v) {
    return false;
  }
  // center_u_norm
  if (lhs->center_u_norm != rhs->center_u_norm) {
    return false;
  }
  // center_v_norm
  if (lhs->center_v_norm != rhs->center_v_norm) {
    return false;
  }
  // bbox_x
  if (lhs->bbox_x != rhs->bbox_x) {
    return false;
  }
  // bbox_y
  if (lhs->bbox_y != rhs->bbox_y) {
    return false;
  }
  // bbox_width
  if (lhs->bbox_width != rhs->bbox_width) {
    return false;
  }
  // bbox_height
  if (lhs->bbox_height != rhs->bbox_height) {
    return false;
  }
  // area_ratio
  if (lhs->area_ratio != rhs->area_ratio) {
    return false;
  }
  return true;
}

bool
uav_interfaces__msg__TargetDetection__copy(
  const uav_interfaces__msg__TargetDetection * input,
  uav_interfaces__msg__TargetDetection * output)
{
  if (!input || !output) {
    return false;
  }
  // stamp
  if (!builtin_interfaces__msg__Time__copy(
      &(input->stamp), &(output->stamp)))
  {
    return false;
  }
  // detected
  output->detected = input->detected;
  // confidence
  output->confidence = input->confidence;
  // center_u
  output->center_u = input->center_u;
  // center_v
  output->center_v = input->center_v;
  // center_u_norm
  output->center_u_norm = input->center_u_norm;
  // center_v_norm
  output->center_v_norm = input->center_v_norm;
  // bbox_x
  output->bbox_x = input->bbox_x;
  // bbox_y
  output->bbox_y = input->bbox_y;
  // bbox_width
  output->bbox_width = input->bbox_width;
  // bbox_height
  output->bbox_height = input->bbox_height;
  // area_ratio
  output->area_ratio = input->area_ratio;
  return true;
}

uav_interfaces__msg__TargetDetection *
uav_interfaces__msg__TargetDetection__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__msg__TargetDetection * msg = (uav_interfaces__msg__TargetDetection *)allocator.allocate(sizeof(uav_interfaces__msg__TargetDetection), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(uav_interfaces__msg__TargetDetection));
  bool success = uav_interfaces__msg__TargetDetection__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
uav_interfaces__msg__TargetDetection__destroy(uav_interfaces__msg__TargetDetection * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    uav_interfaces__msg__TargetDetection__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
uav_interfaces__msg__TargetDetection__Sequence__init(uav_interfaces__msg__TargetDetection__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__msg__TargetDetection * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(uav_interfaces__msg__TargetDetection)) {
      return false;
    }
    data = (uav_interfaces__msg__TargetDetection *)allocator.zero_allocate(size, sizeof(uav_interfaces__msg__TargetDetection), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = uav_interfaces__msg__TargetDetection__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        uav_interfaces__msg__TargetDetection__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
uav_interfaces__msg__TargetDetection__Sequence__fini(uav_interfaces__msg__TargetDetection__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      uav_interfaces__msg__TargetDetection__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

uav_interfaces__msg__TargetDetection__Sequence *
uav_interfaces__msg__TargetDetection__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__msg__TargetDetection__Sequence * array = (uav_interfaces__msg__TargetDetection__Sequence *)allocator.allocate(sizeof(uav_interfaces__msg__TargetDetection__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = uav_interfaces__msg__TargetDetection__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
uav_interfaces__msg__TargetDetection__Sequence__destroy(uav_interfaces__msg__TargetDetection__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    uav_interfaces__msg__TargetDetection__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
uav_interfaces__msg__TargetDetection__Sequence__are_equal(const uav_interfaces__msg__TargetDetection__Sequence * lhs, const uav_interfaces__msg__TargetDetection__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!uav_interfaces__msg__TargetDetection__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
uav_interfaces__msg__TargetDetection__Sequence__copy(
  const uav_interfaces__msg__TargetDetection__Sequence * input,
  uav_interfaces__msg__TargetDetection__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(uav_interfaces__msg__TargetDetection)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(uav_interfaces__msg__TargetDetection);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    uav_interfaces__msg__TargetDetection * data =
      (uav_interfaces__msg__TargetDetection *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!uav_interfaces__msg__TargetDetection__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          uav_interfaces__msg__TargetDetection__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!uav_interfaces__msg__TargetDetection__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
