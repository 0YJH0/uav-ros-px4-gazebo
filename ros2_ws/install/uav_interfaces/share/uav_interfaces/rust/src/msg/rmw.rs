#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "uav_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__msg__TargetDetection() -> *const std::ffi::c_void;
}

#[link(name = "uav_interfaces__rosidl_generator_c")]
extern "C" {
    fn uav_interfaces__msg__TargetDetection__init(msg: *mut TargetDetection) -> bool;
    fn uav_interfaces__msg__TargetDetection__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<TargetDetection>, size: usize) -> bool;
    fn uav_interfaces__msg__TargetDetection__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<TargetDetection>);
    fn uav_interfaces__msg__TargetDetection__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<TargetDetection>, out_seq: *mut rosidl_runtime_rs::Sequence<TargetDetection>) -> bool;
}

// Corresponds to uav_interfaces__msg__TargetDetection
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TargetDetection {

    // This member is not documented.
    #[allow(missing_docs)]
    pub stamp: builtin_interfaces::msg::rmw::Time,


    // This member is not documented.
    #[allow(missing_docs)]
    pub detected: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub confidence: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub center_u: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub center_v: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub center_u_norm: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub center_v_norm: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_x: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_y: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_width: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub bbox_height: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub area_ratio: f32,

}



impl Default for TargetDetection {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !uav_interfaces__msg__TargetDetection__init(&mut msg as *mut _) {
        panic!("Call to uav_interfaces__msg__TargetDetection__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for TargetDetection {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__msg__TargetDetection__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__msg__TargetDetection__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__msg__TargetDetection__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for TargetDetection {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for TargetDetection where Self: Sized {
  const TYPE_NAME: &'static str = "uav_interfaces/msg/TargetDetection";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__msg__TargetDetection() }
  }
}


