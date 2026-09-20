// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from uav_interfaces:action/FlyToAltitude.idl
// generated code does not contain a copyright notice
#include "uav_interfaces/action/detail/fly_to_altitude__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
uav_interfaces__action__FlyToAltitude_Goal__init(uav_interfaces__action__FlyToAltitude_Goal * msg)
{
  if (!msg) {
    return false;
  }
  // target_altitude
  return true;
}

void
uav_interfaces__action__FlyToAltitude_Goal__fini(uav_interfaces__action__FlyToAltitude_Goal * msg)
{
  if (!msg) {
    return;
  }
  // target_altitude
}

bool
uav_interfaces__action__FlyToAltitude_Goal__are_equal(const uav_interfaces__action__FlyToAltitude_Goal * lhs, const uav_interfaces__action__FlyToAltitude_Goal * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // target_altitude
  if (lhs->target_altitude != rhs->target_altitude) {
    return false;
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_Goal__copy(
  const uav_interfaces__action__FlyToAltitude_Goal * input,
  uav_interfaces__action__FlyToAltitude_Goal * output)
{
  if (!input || !output) {
    return false;
  }
  // target_altitude
  output->target_altitude = input->target_altitude;
  return true;
}

uav_interfaces__action__FlyToAltitude_Goal *
uav_interfaces__action__FlyToAltitude_Goal__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_Goal * msg = (uav_interfaces__action__FlyToAltitude_Goal *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_Goal), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(uav_interfaces__action__FlyToAltitude_Goal));
  bool success = uav_interfaces__action__FlyToAltitude_Goal__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
uav_interfaces__action__FlyToAltitude_Goal__destroy(uav_interfaces__action__FlyToAltitude_Goal * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    uav_interfaces__action__FlyToAltitude_Goal__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
uav_interfaces__action__FlyToAltitude_Goal__Sequence__init(uav_interfaces__action__FlyToAltitude_Goal__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_Goal * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_Goal)) {
      return false;
    }
    data = (uav_interfaces__action__FlyToAltitude_Goal *)allocator.zero_allocate(size, sizeof(uav_interfaces__action__FlyToAltitude_Goal), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = uav_interfaces__action__FlyToAltitude_Goal__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        uav_interfaces__action__FlyToAltitude_Goal__fini(&data[i - 1]);
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
uav_interfaces__action__FlyToAltitude_Goal__Sequence__fini(uav_interfaces__action__FlyToAltitude_Goal__Sequence * array)
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
      uav_interfaces__action__FlyToAltitude_Goal__fini(&array->data[i]);
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

uav_interfaces__action__FlyToAltitude_Goal__Sequence *
uav_interfaces__action__FlyToAltitude_Goal__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_Goal__Sequence * array = (uav_interfaces__action__FlyToAltitude_Goal__Sequence *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_Goal__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = uav_interfaces__action__FlyToAltitude_Goal__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
uav_interfaces__action__FlyToAltitude_Goal__Sequence__destroy(uav_interfaces__action__FlyToAltitude_Goal__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    uav_interfaces__action__FlyToAltitude_Goal__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
uav_interfaces__action__FlyToAltitude_Goal__Sequence__are_equal(const uav_interfaces__action__FlyToAltitude_Goal__Sequence * lhs, const uav_interfaces__action__FlyToAltitude_Goal__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_Goal__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_Goal__Sequence__copy(
  const uav_interfaces__action__FlyToAltitude_Goal__Sequence * input,
  uav_interfaces__action__FlyToAltitude_Goal__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_Goal)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(uav_interfaces__action__FlyToAltitude_Goal);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    uav_interfaces__action__FlyToAltitude_Goal * data =
      (uav_interfaces__action__FlyToAltitude_Goal *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!uav_interfaces__action__FlyToAltitude_Goal__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          uav_interfaces__action__FlyToAltitude_Goal__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_Goal__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `message`
#include "rosidl_runtime_c/string_functions.h"

bool
uav_interfaces__action__FlyToAltitude_Result__init(uav_interfaces__action__FlyToAltitude_Result * msg)
{
  if (!msg) {
    return false;
  }
  // success
  // message
  if (!rosidl_runtime_c__String__init(&msg->message)) {
    uav_interfaces__action__FlyToAltitude_Result__fini(msg);
    return false;
  }
  return true;
}

void
uav_interfaces__action__FlyToAltitude_Result__fini(uav_interfaces__action__FlyToAltitude_Result * msg)
{
  if (!msg) {
    return;
  }
  // success
  // message
  rosidl_runtime_c__String__fini(&msg->message);
}

bool
uav_interfaces__action__FlyToAltitude_Result__are_equal(const uav_interfaces__action__FlyToAltitude_Result * lhs, const uav_interfaces__action__FlyToAltitude_Result * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // success
  if (lhs->success != rhs->success) {
    return false;
  }
  // message
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->message), &(rhs->message)))
  {
    return false;
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_Result__copy(
  const uav_interfaces__action__FlyToAltitude_Result * input,
  uav_interfaces__action__FlyToAltitude_Result * output)
{
  if (!input || !output) {
    return false;
  }
  // success
  output->success = input->success;
  // message
  if (!rosidl_runtime_c__String__copy(
      &(input->message), &(output->message)))
  {
    return false;
  }
  return true;
}

uav_interfaces__action__FlyToAltitude_Result *
uav_interfaces__action__FlyToAltitude_Result__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_Result * msg = (uav_interfaces__action__FlyToAltitude_Result *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_Result), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(uav_interfaces__action__FlyToAltitude_Result));
  bool success = uav_interfaces__action__FlyToAltitude_Result__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
uav_interfaces__action__FlyToAltitude_Result__destroy(uav_interfaces__action__FlyToAltitude_Result * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    uav_interfaces__action__FlyToAltitude_Result__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
uav_interfaces__action__FlyToAltitude_Result__Sequence__init(uav_interfaces__action__FlyToAltitude_Result__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_Result * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_Result)) {
      return false;
    }
    data = (uav_interfaces__action__FlyToAltitude_Result *)allocator.zero_allocate(size, sizeof(uav_interfaces__action__FlyToAltitude_Result), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = uav_interfaces__action__FlyToAltitude_Result__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        uav_interfaces__action__FlyToAltitude_Result__fini(&data[i - 1]);
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
uav_interfaces__action__FlyToAltitude_Result__Sequence__fini(uav_interfaces__action__FlyToAltitude_Result__Sequence * array)
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
      uav_interfaces__action__FlyToAltitude_Result__fini(&array->data[i]);
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

uav_interfaces__action__FlyToAltitude_Result__Sequence *
uav_interfaces__action__FlyToAltitude_Result__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_Result__Sequence * array = (uav_interfaces__action__FlyToAltitude_Result__Sequence *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_Result__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = uav_interfaces__action__FlyToAltitude_Result__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
uav_interfaces__action__FlyToAltitude_Result__Sequence__destroy(uav_interfaces__action__FlyToAltitude_Result__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    uav_interfaces__action__FlyToAltitude_Result__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
uav_interfaces__action__FlyToAltitude_Result__Sequence__are_equal(const uav_interfaces__action__FlyToAltitude_Result__Sequence * lhs, const uav_interfaces__action__FlyToAltitude_Result__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_Result__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_Result__Sequence__copy(
  const uav_interfaces__action__FlyToAltitude_Result__Sequence * input,
  uav_interfaces__action__FlyToAltitude_Result__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_Result)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(uav_interfaces__action__FlyToAltitude_Result);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    uav_interfaces__action__FlyToAltitude_Result * data =
      (uav_interfaces__action__FlyToAltitude_Result *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!uav_interfaces__action__FlyToAltitude_Result__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          uav_interfaces__action__FlyToAltitude_Result__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_Result__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


bool
uav_interfaces__action__FlyToAltitude_Feedback__init(uav_interfaces__action__FlyToAltitude_Feedback * msg)
{
  if (!msg) {
    return false;
  }
  // current_altitude
  return true;
}

void
uav_interfaces__action__FlyToAltitude_Feedback__fini(uav_interfaces__action__FlyToAltitude_Feedback * msg)
{
  if (!msg) {
    return;
  }
  // current_altitude
}

bool
uav_interfaces__action__FlyToAltitude_Feedback__are_equal(const uav_interfaces__action__FlyToAltitude_Feedback * lhs, const uav_interfaces__action__FlyToAltitude_Feedback * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // current_altitude
  if (lhs->current_altitude != rhs->current_altitude) {
    return false;
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_Feedback__copy(
  const uav_interfaces__action__FlyToAltitude_Feedback * input,
  uav_interfaces__action__FlyToAltitude_Feedback * output)
{
  if (!input || !output) {
    return false;
  }
  // current_altitude
  output->current_altitude = input->current_altitude;
  return true;
}

uav_interfaces__action__FlyToAltitude_Feedback *
uav_interfaces__action__FlyToAltitude_Feedback__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_Feedback * msg = (uav_interfaces__action__FlyToAltitude_Feedback *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_Feedback), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(uav_interfaces__action__FlyToAltitude_Feedback));
  bool success = uav_interfaces__action__FlyToAltitude_Feedback__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
uav_interfaces__action__FlyToAltitude_Feedback__destroy(uav_interfaces__action__FlyToAltitude_Feedback * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    uav_interfaces__action__FlyToAltitude_Feedback__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
uav_interfaces__action__FlyToAltitude_Feedback__Sequence__init(uav_interfaces__action__FlyToAltitude_Feedback__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_Feedback * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_Feedback)) {
      return false;
    }
    data = (uav_interfaces__action__FlyToAltitude_Feedback *)allocator.zero_allocate(size, sizeof(uav_interfaces__action__FlyToAltitude_Feedback), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = uav_interfaces__action__FlyToAltitude_Feedback__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        uav_interfaces__action__FlyToAltitude_Feedback__fini(&data[i - 1]);
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
uav_interfaces__action__FlyToAltitude_Feedback__Sequence__fini(uav_interfaces__action__FlyToAltitude_Feedback__Sequence * array)
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
      uav_interfaces__action__FlyToAltitude_Feedback__fini(&array->data[i]);
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

uav_interfaces__action__FlyToAltitude_Feedback__Sequence *
uav_interfaces__action__FlyToAltitude_Feedback__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_Feedback__Sequence * array = (uav_interfaces__action__FlyToAltitude_Feedback__Sequence *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_Feedback__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = uav_interfaces__action__FlyToAltitude_Feedback__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
uav_interfaces__action__FlyToAltitude_Feedback__Sequence__destroy(uav_interfaces__action__FlyToAltitude_Feedback__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    uav_interfaces__action__FlyToAltitude_Feedback__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
uav_interfaces__action__FlyToAltitude_Feedback__Sequence__are_equal(const uav_interfaces__action__FlyToAltitude_Feedback__Sequence * lhs, const uav_interfaces__action__FlyToAltitude_Feedback__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_Feedback__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_Feedback__Sequence__copy(
  const uav_interfaces__action__FlyToAltitude_Feedback__Sequence * input,
  uav_interfaces__action__FlyToAltitude_Feedback__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_Feedback)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(uav_interfaces__action__FlyToAltitude_Feedback);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    uav_interfaces__action__FlyToAltitude_Feedback * data =
      (uav_interfaces__action__FlyToAltitude_Feedback *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!uav_interfaces__action__FlyToAltitude_Feedback__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          uav_interfaces__action__FlyToAltitude_Feedback__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_Feedback__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
#include "unique_identifier_msgs/msg/detail/uuid__functions.h"
// Member `goal`
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__functions.h"

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Request__init(uav_interfaces__action__FlyToAltitude_SendGoal_Request * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    uav_interfaces__action__FlyToAltitude_SendGoal_Request__fini(msg);
    return false;
  }
  // goal
  if (!uav_interfaces__action__FlyToAltitude_Goal__init(&msg->goal)) {
    uav_interfaces__action__FlyToAltitude_SendGoal_Request__fini(msg);
    return false;
  }
  return true;
}

void
uav_interfaces__action__FlyToAltitude_SendGoal_Request__fini(uav_interfaces__action__FlyToAltitude_SendGoal_Request * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
  // goal
  uav_interfaces__action__FlyToAltitude_Goal__fini(&msg->goal);
}

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Request__are_equal(const uav_interfaces__action__FlyToAltitude_SendGoal_Request * lhs, const uav_interfaces__action__FlyToAltitude_SendGoal_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  // goal
  if (!uav_interfaces__action__FlyToAltitude_Goal__are_equal(
      &(lhs->goal), &(rhs->goal)))
  {
    return false;
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Request__copy(
  const uav_interfaces__action__FlyToAltitude_SendGoal_Request * input,
  uav_interfaces__action__FlyToAltitude_SendGoal_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  // goal
  if (!uav_interfaces__action__FlyToAltitude_Goal__copy(
      &(input->goal), &(output->goal)))
  {
    return false;
  }
  return true;
}

uav_interfaces__action__FlyToAltitude_SendGoal_Request *
uav_interfaces__action__FlyToAltitude_SendGoal_Request__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_SendGoal_Request * msg = (uav_interfaces__action__FlyToAltitude_SendGoal_Request *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Request));
  bool success = uav_interfaces__action__FlyToAltitude_SendGoal_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
uav_interfaces__action__FlyToAltitude_SendGoal_Request__destroy(uav_interfaces__action__FlyToAltitude_SendGoal_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    uav_interfaces__action__FlyToAltitude_SendGoal_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__init(uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_SendGoal_Request * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Request)) {
      return false;
    }
    data = (uav_interfaces__action__FlyToAltitude_SendGoal_Request *)allocator.zero_allocate(size, sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = uav_interfaces__action__FlyToAltitude_SendGoal_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        uav_interfaces__action__FlyToAltitude_SendGoal_Request__fini(&data[i - 1]);
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
uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__fini(uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence * array)
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
      uav_interfaces__action__FlyToAltitude_SendGoal_Request__fini(&array->data[i]);
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

uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence *
uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence * array = (uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__destroy(uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__are_equal(const uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence * lhs, const uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_SendGoal_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__copy(
  const uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence * input,
  uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Request)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    uav_interfaces__action__FlyToAltitude_SendGoal_Request * data =
      (uav_interfaces__action__FlyToAltitude_SendGoal_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!uav_interfaces__action__FlyToAltitude_SendGoal_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          uav_interfaces__action__FlyToAltitude_SendGoal_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_SendGoal_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `stamp`
#include "builtin_interfaces/msg/detail/time__functions.h"

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Response__init(uav_interfaces__action__FlyToAltitude_SendGoal_Response * msg)
{
  if (!msg) {
    return false;
  }
  // accepted
  // stamp
  if (!builtin_interfaces__msg__Time__init(&msg->stamp)) {
    uav_interfaces__action__FlyToAltitude_SendGoal_Response__fini(msg);
    return false;
  }
  return true;
}

void
uav_interfaces__action__FlyToAltitude_SendGoal_Response__fini(uav_interfaces__action__FlyToAltitude_SendGoal_Response * msg)
{
  if (!msg) {
    return;
  }
  // accepted
  // stamp
  builtin_interfaces__msg__Time__fini(&msg->stamp);
}

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Response__are_equal(const uav_interfaces__action__FlyToAltitude_SendGoal_Response * lhs, const uav_interfaces__action__FlyToAltitude_SendGoal_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // accepted
  if (lhs->accepted != rhs->accepted) {
    return false;
  }
  // stamp
  if (!builtin_interfaces__msg__Time__are_equal(
      &(lhs->stamp), &(rhs->stamp)))
  {
    return false;
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Response__copy(
  const uav_interfaces__action__FlyToAltitude_SendGoal_Response * input,
  uav_interfaces__action__FlyToAltitude_SendGoal_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // accepted
  output->accepted = input->accepted;
  // stamp
  if (!builtin_interfaces__msg__Time__copy(
      &(input->stamp), &(output->stamp)))
  {
    return false;
  }
  return true;
}

uav_interfaces__action__FlyToAltitude_SendGoal_Response *
uav_interfaces__action__FlyToAltitude_SendGoal_Response__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_SendGoal_Response * msg = (uav_interfaces__action__FlyToAltitude_SendGoal_Response *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Response));
  bool success = uav_interfaces__action__FlyToAltitude_SendGoal_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
uav_interfaces__action__FlyToAltitude_SendGoal_Response__destroy(uav_interfaces__action__FlyToAltitude_SendGoal_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    uav_interfaces__action__FlyToAltitude_SendGoal_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__init(uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_SendGoal_Response * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Response)) {
      return false;
    }
    data = (uav_interfaces__action__FlyToAltitude_SendGoal_Response *)allocator.zero_allocate(size, sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = uav_interfaces__action__FlyToAltitude_SendGoal_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        uav_interfaces__action__FlyToAltitude_SendGoal_Response__fini(&data[i - 1]);
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
uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__fini(uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence * array)
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
      uav_interfaces__action__FlyToAltitude_SendGoal_Response__fini(&array->data[i]);
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

uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence *
uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence * array = (uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__destroy(uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__are_equal(const uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence * lhs, const uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_SendGoal_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__copy(
  const uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence * input,
  uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Response)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    uav_interfaces__action__FlyToAltitude_SendGoal_Response * data =
      (uav_interfaces__action__FlyToAltitude_SendGoal_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!uav_interfaces__action__FlyToAltitude_SendGoal_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          uav_interfaces__action__FlyToAltitude_SendGoal_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_SendGoal_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `info`
#include "service_msgs/msg/detail/service_event_info__functions.h"
// Member `request`
// Member `response`
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__functions.h"

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Event__init(uav_interfaces__action__FlyToAltitude_SendGoal_Event * msg)
{
  if (!msg) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__init(&msg->info)) {
    uav_interfaces__action__FlyToAltitude_SendGoal_Event__fini(msg);
    return false;
  }
  // request
  if (!uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__init(&msg->request, 0)) {
    uav_interfaces__action__FlyToAltitude_SendGoal_Event__fini(msg);
    return false;
  }
  // response
  if (!uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__init(&msg->response, 0)) {
    uav_interfaces__action__FlyToAltitude_SendGoal_Event__fini(msg);
    return false;
  }
  return true;
}

void
uav_interfaces__action__FlyToAltitude_SendGoal_Event__fini(uav_interfaces__action__FlyToAltitude_SendGoal_Event * msg)
{
  if (!msg) {
    return;
  }
  // info
  service_msgs__msg__ServiceEventInfo__fini(&msg->info);
  // request
  uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__fini(&msg->request);
  // response
  uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__fini(&msg->response);
}

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Event__are_equal(const uav_interfaces__action__FlyToAltitude_SendGoal_Event * lhs, const uav_interfaces__action__FlyToAltitude_SendGoal_Event * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__are_equal(
      &(lhs->info), &(rhs->info)))
  {
    return false;
  }
  // request
  if (!uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__are_equal(
      &(lhs->request), &(rhs->request)))
  {
    return false;
  }
  // response
  if (!uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__are_equal(
      &(lhs->response), &(rhs->response)))
  {
    return false;
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Event__copy(
  const uav_interfaces__action__FlyToAltitude_SendGoal_Event * input,
  uav_interfaces__action__FlyToAltitude_SendGoal_Event * output)
{
  if (!input || !output) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__copy(
      &(input->info), &(output->info)))
  {
    return false;
  }
  // request
  if (!uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__copy(
      &(input->request), &(output->request)))
  {
    return false;
  }
  // response
  if (!uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__copy(
      &(input->response), &(output->response)))
  {
    return false;
  }
  return true;
}

uav_interfaces__action__FlyToAltitude_SendGoal_Event *
uav_interfaces__action__FlyToAltitude_SendGoal_Event__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_SendGoal_Event * msg = (uav_interfaces__action__FlyToAltitude_SendGoal_Event *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Event), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Event));
  bool success = uav_interfaces__action__FlyToAltitude_SendGoal_Event__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
uav_interfaces__action__FlyToAltitude_SendGoal_Event__destroy(uav_interfaces__action__FlyToAltitude_SendGoal_Event * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    uav_interfaces__action__FlyToAltitude_SendGoal_Event__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence__init(uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_SendGoal_Event * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Event)) {
      return false;
    }
    data = (uav_interfaces__action__FlyToAltitude_SendGoal_Event *)allocator.zero_allocate(size, sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Event), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = uav_interfaces__action__FlyToAltitude_SendGoal_Event__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        uav_interfaces__action__FlyToAltitude_SendGoal_Event__fini(&data[i - 1]);
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
uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence__fini(uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence * array)
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
      uav_interfaces__action__FlyToAltitude_SendGoal_Event__fini(&array->data[i]);
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

uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence *
uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence * array = (uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence__destroy(uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence__are_equal(const uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence * lhs, const uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_SendGoal_Event__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence__copy(
  const uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence * input,
  uav_interfaces__action__FlyToAltitude_SendGoal_Event__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Event)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(uav_interfaces__action__FlyToAltitude_SendGoal_Event);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    uav_interfaces__action__FlyToAltitude_SendGoal_Event * data =
      (uav_interfaces__action__FlyToAltitude_SendGoal_Event *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!uav_interfaces__action__FlyToAltitude_SendGoal_Event__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          uav_interfaces__action__FlyToAltitude_SendGoal_Event__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_SendGoal_Event__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__functions.h"

bool
uav_interfaces__action__FlyToAltitude_GetResult_Request__init(uav_interfaces__action__FlyToAltitude_GetResult_Request * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    uav_interfaces__action__FlyToAltitude_GetResult_Request__fini(msg);
    return false;
  }
  return true;
}

void
uav_interfaces__action__FlyToAltitude_GetResult_Request__fini(uav_interfaces__action__FlyToAltitude_GetResult_Request * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
}

bool
uav_interfaces__action__FlyToAltitude_GetResult_Request__are_equal(const uav_interfaces__action__FlyToAltitude_GetResult_Request * lhs, const uav_interfaces__action__FlyToAltitude_GetResult_Request * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_GetResult_Request__copy(
  const uav_interfaces__action__FlyToAltitude_GetResult_Request * input,
  uav_interfaces__action__FlyToAltitude_GetResult_Request * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  return true;
}

uav_interfaces__action__FlyToAltitude_GetResult_Request *
uav_interfaces__action__FlyToAltitude_GetResult_Request__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_GetResult_Request * msg = (uav_interfaces__action__FlyToAltitude_GetResult_Request *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Request), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Request));
  bool success = uav_interfaces__action__FlyToAltitude_GetResult_Request__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
uav_interfaces__action__FlyToAltitude_GetResult_Request__destroy(uav_interfaces__action__FlyToAltitude_GetResult_Request * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    uav_interfaces__action__FlyToAltitude_GetResult_Request__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__init(uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_GetResult_Request * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Request)) {
      return false;
    }
    data = (uav_interfaces__action__FlyToAltitude_GetResult_Request *)allocator.zero_allocate(size, sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Request), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = uav_interfaces__action__FlyToAltitude_GetResult_Request__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        uav_interfaces__action__FlyToAltitude_GetResult_Request__fini(&data[i - 1]);
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
uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__fini(uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence * array)
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
      uav_interfaces__action__FlyToAltitude_GetResult_Request__fini(&array->data[i]);
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

uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence *
uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence * array = (uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__destroy(uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__are_equal(const uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence * lhs, const uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_GetResult_Request__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__copy(
  const uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence * input,
  uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Request)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Request);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    uav_interfaces__action__FlyToAltitude_GetResult_Request * data =
      (uav_interfaces__action__FlyToAltitude_GetResult_Request *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!uav_interfaces__action__FlyToAltitude_GetResult_Request__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          uav_interfaces__action__FlyToAltitude_GetResult_Request__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_GetResult_Request__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `result`
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__functions.h"

bool
uav_interfaces__action__FlyToAltitude_GetResult_Response__init(uav_interfaces__action__FlyToAltitude_GetResult_Response * msg)
{
  if (!msg) {
    return false;
  }
  // status
  // result
  if (!uav_interfaces__action__FlyToAltitude_Result__init(&msg->result)) {
    uav_interfaces__action__FlyToAltitude_GetResult_Response__fini(msg);
    return false;
  }
  return true;
}

void
uav_interfaces__action__FlyToAltitude_GetResult_Response__fini(uav_interfaces__action__FlyToAltitude_GetResult_Response * msg)
{
  if (!msg) {
    return;
  }
  // status
  // result
  uav_interfaces__action__FlyToAltitude_Result__fini(&msg->result);
}

bool
uav_interfaces__action__FlyToAltitude_GetResult_Response__are_equal(const uav_interfaces__action__FlyToAltitude_GetResult_Response * lhs, const uav_interfaces__action__FlyToAltitude_GetResult_Response * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // status
  if (lhs->status != rhs->status) {
    return false;
  }
  // result
  if (!uav_interfaces__action__FlyToAltitude_Result__are_equal(
      &(lhs->result), &(rhs->result)))
  {
    return false;
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_GetResult_Response__copy(
  const uav_interfaces__action__FlyToAltitude_GetResult_Response * input,
  uav_interfaces__action__FlyToAltitude_GetResult_Response * output)
{
  if (!input || !output) {
    return false;
  }
  // status
  output->status = input->status;
  // result
  if (!uav_interfaces__action__FlyToAltitude_Result__copy(
      &(input->result), &(output->result)))
  {
    return false;
  }
  return true;
}

uav_interfaces__action__FlyToAltitude_GetResult_Response *
uav_interfaces__action__FlyToAltitude_GetResult_Response__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_GetResult_Response * msg = (uav_interfaces__action__FlyToAltitude_GetResult_Response *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Response), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Response));
  bool success = uav_interfaces__action__FlyToAltitude_GetResult_Response__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
uav_interfaces__action__FlyToAltitude_GetResult_Response__destroy(uav_interfaces__action__FlyToAltitude_GetResult_Response * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    uav_interfaces__action__FlyToAltitude_GetResult_Response__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__init(uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_GetResult_Response * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Response)) {
      return false;
    }
    data = (uav_interfaces__action__FlyToAltitude_GetResult_Response *)allocator.zero_allocate(size, sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Response), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = uav_interfaces__action__FlyToAltitude_GetResult_Response__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        uav_interfaces__action__FlyToAltitude_GetResult_Response__fini(&data[i - 1]);
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
uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__fini(uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence * array)
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
      uav_interfaces__action__FlyToAltitude_GetResult_Response__fini(&array->data[i]);
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

uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence *
uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence * array = (uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__destroy(uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__are_equal(const uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence * lhs, const uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_GetResult_Response__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__copy(
  const uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence * input,
  uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Response)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Response);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    uav_interfaces__action__FlyToAltitude_GetResult_Response * data =
      (uav_interfaces__action__FlyToAltitude_GetResult_Response *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!uav_interfaces__action__FlyToAltitude_GetResult_Response__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          uav_interfaces__action__FlyToAltitude_GetResult_Response__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_GetResult_Response__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `info`
// already included above
// #include "service_msgs/msg/detail/service_event_info__functions.h"
// Member `request`
// Member `response`
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__functions.h"

bool
uav_interfaces__action__FlyToAltitude_GetResult_Event__init(uav_interfaces__action__FlyToAltitude_GetResult_Event * msg)
{
  if (!msg) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__init(&msg->info)) {
    uav_interfaces__action__FlyToAltitude_GetResult_Event__fini(msg);
    return false;
  }
  // request
  if (!uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__init(&msg->request, 0)) {
    uav_interfaces__action__FlyToAltitude_GetResult_Event__fini(msg);
    return false;
  }
  // response
  if (!uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__init(&msg->response, 0)) {
    uav_interfaces__action__FlyToAltitude_GetResult_Event__fini(msg);
    return false;
  }
  return true;
}

void
uav_interfaces__action__FlyToAltitude_GetResult_Event__fini(uav_interfaces__action__FlyToAltitude_GetResult_Event * msg)
{
  if (!msg) {
    return;
  }
  // info
  service_msgs__msg__ServiceEventInfo__fini(&msg->info);
  // request
  uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__fini(&msg->request);
  // response
  uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__fini(&msg->response);
}

bool
uav_interfaces__action__FlyToAltitude_GetResult_Event__are_equal(const uav_interfaces__action__FlyToAltitude_GetResult_Event * lhs, const uav_interfaces__action__FlyToAltitude_GetResult_Event * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__are_equal(
      &(lhs->info), &(rhs->info)))
  {
    return false;
  }
  // request
  if (!uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__are_equal(
      &(lhs->request), &(rhs->request)))
  {
    return false;
  }
  // response
  if (!uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__are_equal(
      &(lhs->response), &(rhs->response)))
  {
    return false;
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_GetResult_Event__copy(
  const uav_interfaces__action__FlyToAltitude_GetResult_Event * input,
  uav_interfaces__action__FlyToAltitude_GetResult_Event * output)
{
  if (!input || !output) {
    return false;
  }
  // info
  if (!service_msgs__msg__ServiceEventInfo__copy(
      &(input->info), &(output->info)))
  {
    return false;
  }
  // request
  if (!uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__copy(
      &(input->request), &(output->request)))
  {
    return false;
  }
  // response
  if (!uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__copy(
      &(input->response), &(output->response)))
  {
    return false;
  }
  return true;
}

uav_interfaces__action__FlyToAltitude_GetResult_Event *
uav_interfaces__action__FlyToAltitude_GetResult_Event__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_GetResult_Event * msg = (uav_interfaces__action__FlyToAltitude_GetResult_Event *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Event), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Event));
  bool success = uav_interfaces__action__FlyToAltitude_GetResult_Event__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
uav_interfaces__action__FlyToAltitude_GetResult_Event__destroy(uav_interfaces__action__FlyToAltitude_GetResult_Event * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    uav_interfaces__action__FlyToAltitude_GetResult_Event__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence__init(uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_GetResult_Event * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Event)) {
      return false;
    }
    data = (uav_interfaces__action__FlyToAltitude_GetResult_Event *)allocator.zero_allocate(size, sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Event), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = uav_interfaces__action__FlyToAltitude_GetResult_Event__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        uav_interfaces__action__FlyToAltitude_GetResult_Event__fini(&data[i - 1]);
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
uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence__fini(uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence * array)
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
      uav_interfaces__action__FlyToAltitude_GetResult_Event__fini(&array->data[i]);
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

uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence *
uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence * array = (uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence__destroy(uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence__are_equal(const uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence * lhs, const uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_GetResult_Event__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence__copy(
  const uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence * input,
  uav_interfaces__action__FlyToAltitude_GetResult_Event__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Event)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(uav_interfaces__action__FlyToAltitude_GetResult_Event);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    uav_interfaces__action__FlyToAltitude_GetResult_Event * data =
      (uav_interfaces__action__FlyToAltitude_GetResult_Event *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!uav_interfaces__action__FlyToAltitude_GetResult_Event__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          uav_interfaces__action__FlyToAltitude_GetResult_Event__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_GetResult_Event__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}


// Include directives for member types
// Member `goal_id`
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__functions.h"
// Member `feedback`
// already included above
// #include "uav_interfaces/action/detail/fly_to_altitude__functions.h"

bool
uav_interfaces__action__FlyToAltitude_FeedbackMessage__init(uav_interfaces__action__FlyToAltitude_FeedbackMessage * msg)
{
  if (!msg) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__init(&msg->goal_id)) {
    uav_interfaces__action__FlyToAltitude_FeedbackMessage__fini(msg);
    return false;
  }
  // feedback
  if (!uav_interfaces__action__FlyToAltitude_Feedback__init(&msg->feedback)) {
    uav_interfaces__action__FlyToAltitude_FeedbackMessage__fini(msg);
    return false;
  }
  return true;
}

void
uav_interfaces__action__FlyToAltitude_FeedbackMessage__fini(uav_interfaces__action__FlyToAltitude_FeedbackMessage * msg)
{
  if (!msg) {
    return;
  }
  // goal_id
  unique_identifier_msgs__msg__UUID__fini(&msg->goal_id);
  // feedback
  uav_interfaces__action__FlyToAltitude_Feedback__fini(&msg->feedback);
}

bool
uav_interfaces__action__FlyToAltitude_FeedbackMessage__are_equal(const uav_interfaces__action__FlyToAltitude_FeedbackMessage * lhs, const uav_interfaces__action__FlyToAltitude_FeedbackMessage * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__are_equal(
      &(lhs->goal_id), &(rhs->goal_id)))
  {
    return false;
  }
  // feedback
  if (!uav_interfaces__action__FlyToAltitude_Feedback__are_equal(
      &(lhs->feedback), &(rhs->feedback)))
  {
    return false;
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_FeedbackMessage__copy(
  const uav_interfaces__action__FlyToAltitude_FeedbackMessage * input,
  uav_interfaces__action__FlyToAltitude_FeedbackMessage * output)
{
  if (!input || !output) {
    return false;
  }
  // goal_id
  if (!unique_identifier_msgs__msg__UUID__copy(
      &(input->goal_id), &(output->goal_id)))
  {
    return false;
  }
  // feedback
  if (!uav_interfaces__action__FlyToAltitude_Feedback__copy(
      &(input->feedback), &(output->feedback)))
  {
    return false;
  }
  return true;
}

uav_interfaces__action__FlyToAltitude_FeedbackMessage *
uav_interfaces__action__FlyToAltitude_FeedbackMessage__create(void)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_FeedbackMessage * msg = (uav_interfaces__action__FlyToAltitude_FeedbackMessage *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_FeedbackMessage), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(uav_interfaces__action__FlyToAltitude_FeedbackMessage));
  bool success = uav_interfaces__action__FlyToAltitude_FeedbackMessage__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
uav_interfaces__action__FlyToAltitude_FeedbackMessage__destroy(uav_interfaces__action__FlyToAltitude_FeedbackMessage * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    uav_interfaces__action__FlyToAltitude_FeedbackMessage__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence__init(uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_FeedbackMessage * data = NULL;

  if (size) {
    if (size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_FeedbackMessage)) {
      return false;
    }
    data = (uav_interfaces__action__FlyToAltitude_FeedbackMessage *)allocator.zero_allocate(size, sizeof(uav_interfaces__action__FlyToAltitude_FeedbackMessage), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = uav_interfaces__action__FlyToAltitude_FeedbackMessage__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        uav_interfaces__action__FlyToAltitude_FeedbackMessage__fini(&data[i - 1]);
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
uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence__fini(uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence * array)
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
      uav_interfaces__action__FlyToAltitude_FeedbackMessage__fini(&array->data[i]);
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

uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence *
uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence * array = (uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence *)allocator.allocate(sizeof(uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence__destroy(uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence__are_equal(const uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence * lhs, const uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_FeedbackMessage__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence__copy(
  const uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence * input,
  uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    if (input->size > SIZE_MAX / sizeof(uav_interfaces__action__FlyToAltitude_FeedbackMessage)) {
      return false;
    }
    const size_t allocation_size =
      input->size * sizeof(uav_interfaces__action__FlyToAltitude_FeedbackMessage);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    uav_interfaces__action__FlyToAltitude_FeedbackMessage * data =
      (uav_interfaces__action__FlyToAltitude_FeedbackMessage *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!uav_interfaces__action__FlyToAltitude_FeedbackMessage__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          uav_interfaces__action__FlyToAltitude_FeedbackMessage__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!uav_interfaces__action__FlyToAltitude_FeedbackMessage__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
