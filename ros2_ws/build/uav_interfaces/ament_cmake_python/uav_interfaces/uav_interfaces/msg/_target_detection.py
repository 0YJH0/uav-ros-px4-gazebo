# generated from rosidl_generator_py/resource/_idl.py.em
# with input from uav_interfaces:msg/TargetDetection.idl
# generated code does not contain a copyright notice

# This is being done at the module level and not on the instance level to avoid looking
# for the same variable multiple times on each instance. This variable is not supposed to
# change during runtime so it makes sense to only look for it once.
from os import getenv

ros_python_check_fields = getenv('ROS_PYTHON_CHECK_FIELDS', default='')


# Import statements for member types

import builtins  # noqa: E402, I100

import math  # noqa: E402, I100

import rosidl_parser.definition  # noqa: E402, I100


class Metaclass_TargetDetection(type):
    """Metaclass of message 'TargetDetection'."""

    _CREATE_ROS_MESSAGE = None
    _CONVERT_FROM_PY = None
    _CONVERT_TO_PY = None
    _DESTROY_ROS_MESSAGE = None
    _TYPE_SUPPORT = None

    __constants = {
    }

    @classmethod
    def __import_type_support__(cls):
        try:
            from rosidl_generator_py import import_type_support
            module = import_type_support('uav_interfaces')
        except ImportError:
            import logging
            import traceback
            logger = logging.getLogger(
                'uav_interfaces.msg.TargetDetection')
            logger.debug(
                'Failed to import needed modules for type support:\n' +
                traceback.format_exc())
        else:
            cls._CREATE_ROS_MESSAGE = module.create_ros_message_msg__msg__target_detection
            cls._CONVERT_FROM_PY = module.convert_from_py_msg__msg__target_detection
            cls._CONVERT_TO_PY = module.convert_to_py_msg__msg__target_detection
            cls._TYPE_SUPPORT = module.type_support_msg__msg__target_detection
            cls._DESTROY_ROS_MESSAGE = module.destroy_ros_message_msg__msg__target_detection

            from builtin_interfaces.msg import Time
            if Time.__class__._TYPE_SUPPORT is None:
                Time.__class__.__import_type_support__()

    @classmethod
    def __prepare__(cls, name, bases, **kwargs):
        # list constant names here so that they appear in the help text of
        # the message class under "Data and other attributes defined here:"
        # as well as populate each message instance
        return {
        }


class TargetDetection(metaclass=Metaclass_TargetDetection):
    """Message class 'TargetDetection'."""

    __slots__ = [
        '_stamp',
        '_detected',
        '_confidence',
        '_center_u',
        '_center_v',
        '_center_u_norm',
        '_center_v_norm',
        '_bbox_x',
        '_bbox_y',
        '_bbox_width',
        '_bbox_height',
        '_area_ratio',
        '_check_fields',
    ]

    _fields_and_field_types = {
        'stamp': 'builtin_interfaces/Time',
        'detected': 'boolean',
        'confidence': 'float',
        'center_u': 'float',
        'center_v': 'float',
        'center_u_norm': 'float',
        'center_v_norm': 'float',
        'bbox_x': 'float',
        'bbox_y': 'float',
        'bbox_width': 'float',
        'bbox_height': 'float',
        'area_ratio': 'float',
    }

    # This attribute is used to store an rosidl_parser.definition variable
    # related to the data type of each of the components the message.
    SLOT_TYPES = (
        rosidl_parser.definition.NamespacedType(['builtin_interfaces', 'msg'], 'Time'),  # noqa: E501
        rosidl_parser.definition.BasicType('boolean'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
        rosidl_parser.definition.BasicType('float'),  # noqa: E501
    )

    def __init__(self, **kwargs):
        if 'check_fields' in kwargs:
            self._check_fields = kwargs['check_fields']
        else:
            self._check_fields = ros_python_check_fields == '1'
        if self._check_fields:
            assert all('_' + key in self.__slots__ for key in kwargs.keys()), \
                'Invalid arguments passed to constructor: %s' % \
                ', '.join(sorted(k for k in kwargs.keys() if '_' + k not in self.__slots__))
        from builtin_interfaces.msg import Time
        self.stamp = kwargs.get('stamp', Time())
        self.detected = kwargs.get('detected', bool())
        self.confidence = kwargs.get('confidence', float())
        self.center_u = kwargs.get('center_u', float())
        self.center_v = kwargs.get('center_v', float())
        self.center_u_norm = kwargs.get('center_u_norm', float())
        self.center_v_norm = kwargs.get('center_v_norm', float())
        self.bbox_x = kwargs.get('bbox_x', float())
        self.bbox_y = kwargs.get('bbox_y', float())
        self.bbox_width = kwargs.get('bbox_width', float())
        self.bbox_height = kwargs.get('bbox_height', float())
        self.area_ratio = kwargs.get('area_ratio', float())

    def __repr__(self):
        typename = self.__class__.__module__.split('.')
        typename.pop()
        typename.append(self.__class__.__name__)
        args = []
        for s, t in zip(self.get_fields_and_field_types().keys(), self.SLOT_TYPES):
            field = getattr(self, s)
            fieldstr = repr(field)
            # We use Python array type for fields that can be directly stored
            # in them, and "normal" sequences for everything else.  If it is
            # a type that we store in an array, strip off the 'array' portion.
            if (
                isinstance(t, rosidl_parser.definition.AbstractSequence) and
                isinstance(t.value_type, rosidl_parser.definition.BasicType) and
                t.value_type.typename in ['float', 'double', 'int8', 'uint8', 'int16', 'uint16', 'int32', 'uint32', 'int64', 'uint64']
            ):
                if len(field) == 0:
                    fieldstr = '[]'
                else:
                    if self._check_fields:
                        assert fieldstr.startswith('array(')
                    prefix = "array('X', "
                    suffix = ')'
                    fieldstr = fieldstr[len(prefix):-len(suffix)]
            args.append(s + '=' + fieldstr)
        return '%s(%s)' % ('.'.join(typename), ', '.join(args))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        if self.stamp != other.stamp:
            return False
        if self.detected != other.detected:
            return False
        if self.confidence != other.confidence:
            return False
        if self.center_u != other.center_u:
            return False
        if self.center_v != other.center_v:
            return False
        if self.center_u_norm != other.center_u_norm:
            return False
        if self.center_v_norm != other.center_v_norm:
            return False
        if self.bbox_x != other.bbox_x:
            return False
        if self.bbox_y != other.bbox_y:
            return False
        if self.bbox_width != other.bbox_width:
            return False
        if self.bbox_height != other.bbox_height:
            return False
        if self.area_ratio != other.area_ratio:
            return False
        return True

    @classmethod
    def get_fields_and_field_types(cls):
        from copy import copy
        return copy(cls._fields_and_field_types)

    @builtins.property
    def stamp(self):
        """Message field 'stamp'."""
        return self._stamp

    @stamp.setter
    def stamp(self, value):
        if self._check_fields:
            from builtin_interfaces.msg import Time
            assert \
                isinstance(value, Time), \
                "The 'stamp' field must be a sub message of type 'Time'"
        self._stamp = value

    @builtins.property
    def detected(self):
        """Message field 'detected'."""
        return self._detected

    @detected.setter
    def detected(self, value):
        if self._check_fields:
            assert \
                isinstance(value, bool), \
                "The 'detected' field must be of type 'bool'"
        self._detected = value

    @builtins.property
    def confidence(self):
        """Message field 'confidence'."""
        return self._confidence

    @confidence.setter
    def confidence(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'confidence' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'confidence' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._confidence = value

    @builtins.property
    def center_u(self):
        """Message field 'center_u'."""
        return self._center_u

    @center_u.setter
    def center_u(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'center_u' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'center_u' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._center_u = value

    @builtins.property
    def center_v(self):
        """Message field 'center_v'."""
        return self._center_v

    @center_v.setter
    def center_v(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'center_v' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'center_v' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._center_v = value

    @builtins.property
    def center_u_norm(self):
        """Message field 'center_u_norm'."""
        return self._center_u_norm

    @center_u_norm.setter
    def center_u_norm(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'center_u_norm' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'center_u_norm' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._center_u_norm = value

    @builtins.property
    def center_v_norm(self):
        """Message field 'center_v_norm'."""
        return self._center_v_norm

    @center_v_norm.setter
    def center_v_norm(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'center_v_norm' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'center_v_norm' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._center_v_norm = value

    @builtins.property
    def bbox_x(self):
        """Message field 'bbox_x'."""
        return self._bbox_x

    @bbox_x.setter
    def bbox_x(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'bbox_x' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'bbox_x' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._bbox_x = value

    @builtins.property
    def bbox_y(self):
        """Message field 'bbox_y'."""
        return self._bbox_y

    @bbox_y.setter
    def bbox_y(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'bbox_y' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'bbox_y' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._bbox_y = value

    @builtins.property
    def bbox_width(self):
        """Message field 'bbox_width'."""
        return self._bbox_width

    @bbox_width.setter
    def bbox_width(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'bbox_width' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'bbox_width' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._bbox_width = value

    @builtins.property
    def bbox_height(self):
        """Message field 'bbox_height'."""
        return self._bbox_height

    @bbox_height.setter
    def bbox_height(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'bbox_height' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'bbox_height' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._bbox_height = value

    @builtins.property
    def area_ratio(self):
        """Message field 'area_ratio'."""
        return self._area_ratio

    @area_ratio.setter
    def area_ratio(self, value):
        if self._check_fields:
            assert \
                isinstance(value, float), \
                "The 'area_ratio' field must be of type 'float'"
            assert not (value < -3.402823466e+38 or value > 3.402823466e+38) or math.isinf(value), \
                "The 'area_ratio' field must be a float in [-3.402823466e+38, 3.402823466e+38]"
        self._area_ratio = value
