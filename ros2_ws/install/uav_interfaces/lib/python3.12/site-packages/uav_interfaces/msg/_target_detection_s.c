// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from uav_interfaces:msg/TargetDetection.idl
// generated code does not contain a copyright notice
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <stdbool.h>
#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-function"
#endif
#include "numpy/ndarrayobject.h"
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif
#include "rosidl_runtime_c/visibility_control.h"
#include "uav_interfaces/msg/detail/target_detection__struct.h"
#include "uav_interfaces/msg/detail/target_detection__functions.h"

ROSIDL_GENERATOR_C_IMPORT
bool builtin_interfaces__msg__time__convert_from_py(PyObject * _pymsg, void * _ros_message);
ROSIDL_GENERATOR_C_IMPORT
PyObject * builtin_interfaces__msg__time__convert_to_py(void * raw_ros_message);

ROSIDL_GENERATOR_C_EXPORT
bool uav_interfaces__msg__target_detection__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[53];
    {
      char * class_name = NULL;
      char * module_name = NULL;
      {
        PyObject * class_attr = PyObject_GetAttrString(_pymsg, "__class__");
        if (class_attr) {
          PyObject * name_attr = PyObject_GetAttrString(class_attr, "__name__");
          if (name_attr) {
            class_name = (char *)PyUnicode_1BYTE_DATA(name_attr);
            Py_DECREF(name_attr);
          }
          PyObject * module_attr = PyObject_GetAttrString(class_attr, "__module__");
          if (module_attr) {
            module_name = (char *)PyUnicode_1BYTE_DATA(module_attr);
            Py_DECREF(module_attr);
          }
          Py_DECREF(class_attr);
        }
      }
      if (!class_name || !module_name) {
        return false;
      }
      snprintf(full_classname_dest, sizeof(full_classname_dest), "%s.%s", module_name, class_name);
    }
    assert(strncmp("uav_interfaces.msg._target_detection.TargetDetection", full_classname_dest, 52) == 0);
  }
  uav_interfaces__msg__TargetDetection * ros_message = _ros_message;
  {  // stamp
    PyObject * field = PyObject_GetAttrString(_pymsg, "stamp");
    if (!field) {
      return false;
    }
    if (!builtin_interfaces__msg__time__convert_from_py(field, &ros_message->stamp)) {
      Py_DECREF(field);
      return false;
    }
    Py_DECREF(field);
  }
  {  // detected
    PyObject * field = PyObject_GetAttrString(_pymsg, "detected");
    if (!field) {
      return false;
    }
    assert(PyBool_Check(field));
    ros_message->detected = (Py_True == field);
    Py_DECREF(field);
  }
  {  // confidence
    PyObject * field = PyObject_GetAttrString(_pymsg, "confidence");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->confidence = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // center_u
    PyObject * field = PyObject_GetAttrString(_pymsg, "center_u");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->center_u = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // center_v
    PyObject * field = PyObject_GetAttrString(_pymsg, "center_v");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->center_v = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // center_u_norm
    PyObject * field = PyObject_GetAttrString(_pymsg, "center_u_norm");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->center_u_norm = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // center_v_norm
    PyObject * field = PyObject_GetAttrString(_pymsg, "center_v_norm");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->center_v_norm = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // bbox_x
    PyObject * field = PyObject_GetAttrString(_pymsg, "bbox_x");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->bbox_x = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // bbox_y
    PyObject * field = PyObject_GetAttrString(_pymsg, "bbox_y");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->bbox_y = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // bbox_width
    PyObject * field = PyObject_GetAttrString(_pymsg, "bbox_width");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->bbox_width = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // bbox_height
    PyObject * field = PyObject_GetAttrString(_pymsg, "bbox_height");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->bbox_height = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }
  {  // area_ratio
    PyObject * field = PyObject_GetAttrString(_pymsg, "area_ratio");
    if (!field) {
      return false;
    }
    assert(PyFloat_Check(field));
    ros_message->area_ratio = (float)PyFloat_AS_DOUBLE(field);
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * uav_interfaces__msg__target_detection__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of TargetDetection */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("uav_interfaces.msg._target_detection");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "TargetDetection");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  uav_interfaces__msg__TargetDetection * ros_message = (uav_interfaces__msg__TargetDetection *)raw_ros_message;
  {  // stamp
    PyObject * field = NULL;
    field = builtin_interfaces__msg__time__convert_to_py(&ros_message->stamp);
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "stamp", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // detected
    PyObject * field = NULL;
    field = PyBool_FromLong(ros_message->detected ? 1 : 0);
    {
      int rc = PyObject_SetAttrString(_pymessage, "detected", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // confidence
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->confidence);
    {
      int rc = PyObject_SetAttrString(_pymessage, "confidence", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // center_u
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->center_u);
    {
      int rc = PyObject_SetAttrString(_pymessage, "center_u", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // center_v
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->center_v);
    {
      int rc = PyObject_SetAttrString(_pymessage, "center_v", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // center_u_norm
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->center_u_norm);
    {
      int rc = PyObject_SetAttrString(_pymessage, "center_u_norm", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // center_v_norm
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->center_v_norm);
    {
      int rc = PyObject_SetAttrString(_pymessage, "center_v_norm", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // bbox_x
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->bbox_x);
    {
      int rc = PyObject_SetAttrString(_pymessage, "bbox_x", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // bbox_y
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->bbox_y);
    {
      int rc = PyObject_SetAttrString(_pymessage, "bbox_y", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // bbox_width
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->bbox_width);
    {
      int rc = PyObject_SetAttrString(_pymessage, "bbox_width", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // bbox_height
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->bbox_height);
    {
      int rc = PyObject_SetAttrString(_pymessage, "bbox_height", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // area_ratio
    PyObject * field = NULL;
    field = PyFloat_FromDouble(ros_message->area_ratio);
    {
      int rc = PyObject_SetAttrString(_pymessage, "area_ratio", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
