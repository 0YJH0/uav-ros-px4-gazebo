
#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "uav_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_Goal() -> *const std::ffi::c_void;
}

#[link(name = "uav_interfaces__rosidl_generator_c")]
extern "C" {
    fn uav_interfaces__action__FlyToAltitude_Goal__init(msg: *mut FlyToAltitude_Goal) -> bool;
    fn uav_interfaces__action__FlyToAltitude_Goal__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_Goal>, size: usize) -> bool;
    fn uav_interfaces__action__FlyToAltitude_Goal__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_Goal>);
    fn uav_interfaces__action__FlyToAltitude_Goal__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<FlyToAltitude_Goal>, out_seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_Goal>) -> bool;
}

// Corresponds to uav_interfaces__action__FlyToAltitude_Goal
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FlyToAltitude_Goal {

    // This member is not documented.
    #[allow(missing_docs)]
    pub target_altitude: f32,

}



impl Default for FlyToAltitude_Goal {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !uav_interfaces__action__FlyToAltitude_Goal__init(&mut msg as *mut _) {
        panic!("Call to uav_interfaces__action__FlyToAltitude_Goal__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for FlyToAltitude_Goal {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_Goal__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_Goal__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_Goal__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for FlyToAltitude_Goal {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for FlyToAltitude_Goal where Self: Sized {
  const TYPE_NAME: &'static str = "uav_interfaces/action/FlyToAltitude_Goal";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_Goal() }
  }
}


#[link(name = "uav_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_Result() -> *const std::ffi::c_void;
}

#[link(name = "uav_interfaces__rosidl_generator_c")]
extern "C" {
    fn uav_interfaces__action__FlyToAltitude_Result__init(msg: *mut FlyToAltitude_Result) -> bool;
    fn uav_interfaces__action__FlyToAltitude_Result__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_Result>, size: usize) -> bool;
    fn uav_interfaces__action__FlyToAltitude_Result__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_Result>);
    fn uav_interfaces__action__FlyToAltitude_Result__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<FlyToAltitude_Result>, out_seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_Result>) -> bool;
}

// Corresponds to uav_interfaces__action__FlyToAltitude_Result
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FlyToAltitude_Result {

    // This member is not documented.
    #[allow(missing_docs)]
    pub success: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub message: rosidl_runtime_rs::String,

}



impl Default for FlyToAltitude_Result {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !uav_interfaces__action__FlyToAltitude_Result__init(&mut msg as *mut _) {
        panic!("Call to uav_interfaces__action__FlyToAltitude_Result__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for FlyToAltitude_Result {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_Result__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_Result__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_Result__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for FlyToAltitude_Result {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for FlyToAltitude_Result where Self: Sized {
  const TYPE_NAME: &'static str = "uav_interfaces/action/FlyToAltitude_Result";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_Result() }
  }
}


#[link(name = "uav_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_Feedback() -> *const std::ffi::c_void;
}

#[link(name = "uav_interfaces__rosidl_generator_c")]
extern "C" {
    fn uav_interfaces__action__FlyToAltitude_Feedback__init(msg: *mut FlyToAltitude_Feedback) -> bool;
    fn uav_interfaces__action__FlyToAltitude_Feedback__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_Feedback>, size: usize) -> bool;
    fn uav_interfaces__action__FlyToAltitude_Feedback__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_Feedback>);
    fn uav_interfaces__action__FlyToAltitude_Feedback__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<FlyToAltitude_Feedback>, out_seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_Feedback>) -> bool;
}

// Corresponds to uav_interfaces__action__FlyToAltitude_Feedback
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FlyToAltitude_Feedback {

    // This member is not documented.
    #[allow(missing_docs)]
    pub current_altitude: f32,

}



impl Default for FlyToAltitude_Feedback {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !uav_interfaces__action__FlyToAltitude_Feedback__init(&mut msg as *mut _) {
        panic!("Call to uav_interfaces__action__FlyToAltitude_Feedback__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for FlyToAltitude_Feedback {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_Feedback__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_Feedback__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_Feedback__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for FlyToAltitude_Feedback {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for FlyToAltitude_Feedback where Self: Sized {
  const TYPE_NAME: &'static str = "uav_interfaces/action/FlyToAltitude_Feedback";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_Feedback() }
  }
}


#[link(name = "uav_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_FeedbackMessage() -> *const std::ffi::c_void;
}

#[link(name = "uav_interfaces__rosidl_generator_c")]
extern "C" {
    fn uav_interfaces__action__FlyToAltitude_FeedbackMessage__init(msg: *mut FlyToAltitude_FeedbackMessage) -> bool;
    fn uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_FeedbackMessage>, size: usize) -> bool;
    fn uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_FeedbackMessage>);
    fn uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<FlyToAltitude_FeedbackMessage>, out_seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_FeedbackMessage>) -> bool;
}

// Corresponds to uav_interfaces__action__FlyToAltitude_FeedbackMessage
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FlyToAltitude_FeedbackMessage {

    // This member is not documented.
    #[allow(missing_docs)]
    pub goal_id: unique_identifier_msgs::msg::rmw::UUID,


    // This member is not documented.
    #[allow(missing_docs)]
    pub feedback: super::super::action::rmw::FlyToAltitude_Feedback,

}



impl Default for FlyToAltitude_FeedbackMessage {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !uav_interfaces__action__FlyToAltitude_FeedbackMessage__init(&mut msg as *mut _) {
        panic!("Call to uav_interfaces__action__FlyToAltitude_FeedbackMessage__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for FlyToAltitude_FeedbackMessage {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_FeedbackMessage__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for FlyToAltitude_FeedbackMessage {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for FlyToAltitude_FeedbackMessage where Self: Sized {
  const TYPE_NAME: &'static str = "uav_interfaces/action/FlyToAltitude_FeedbackMessage";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_FeedbackMessage() }
  }
}




#[link(name = "uav_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_SendGoal_Request() -> *const std::ffi::c_void;
}

#[link(name = "uav_interfaces__rosidl_generator_c")]
extern "C" {
    fn uav_interfaces__action__FlyToAltitude_SendGoal_Request__init(msg: *mut FlyToAltitude_SendGoal_Request) -> bool;
    fn uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_SendGoal_Request>, size: usize) -> bool;
    fn uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_SendGoal_Request>);
    fn uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<FlyToAltitude_SendGoal_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_SendGoal_Request>) -> bool;
}

// Corresponds to uav_interfaces__action__FlyToAltitude_SendGoal_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FlyToAltitude_SendGoal_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub goal_id: unique_identifier_msgs::msg::rmw::UUID,


    // This member is not documented.
    #[allow(missing_docs)]
    pub goal: super::super::action::rmw::FlyToAltitude_Goal,

}



impl Default for FlyToAltitude_SendGoal_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !uav_interfaces__action__FlyToAltitude_SendGoal_Request__init(&mut msg as *mut _) {
        panic!("Call to uav_interfaces__action__FlyToAltitude_SendGoal_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for FlyToAltitude_SendGoal_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_SendGoal_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for FlyToAltitude_SendGoal_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for FlyToAltitude_SendGoal_Request where Self: Sized {
  const TYPE_NAME: &'static str = "uav_interfaces/action/FlyToAltitude_SendGoal_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_SendGoal_Request() }
  }
}


#[link(name = "uav_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_SendGoal_Response() -> *const std::ffi::c_void;
}

#[link(name = "uav_interfaces__rosidl_generator_c")]
extern "C" {
    fn uav_interfaces__action__FlyToAltitude_SendGoal_Response__init(msg: *mut FlyToAltitude_SendGoal_Response) -> bool;
    fn uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_SendGoal_Response>, size: usize) -> bool;
    fn uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_SendGoal_Response>);
    fn uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<FlyToAltitude_SendGoal_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_SendGoal_Response>) -> bool;
}

// Corresponds to uav_interfaces__action__FlyToAltitude_SendGoal_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FlyToAltitude_SendGoal_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub accepted: bool,


    // This member is not documented.
    #[allow(missing_docs)]
    pub stamp: builtin_interfaces::msg::rmw::Time,

}



impl Default for FlyToAltitude_SendGoal_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !uav_interfaces__action__FlyToAltitude_SendGoal_Response__init(&mut msg as *mut _) {
        panic!("Call to uav_interfaces__action__FlyToAltitude_SendGoal_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for FlyToAltitude_SendGoal_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_SendGoal_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for FlyToAltitude_SendGoal_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for FlyToAltitude_SendGoal_Response where Self: Sized {
  const TYPE_NAME: &'static str = "uav_interfaces/action/FlyToAltitude_SendGoal_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_SendGoal_Response() }
  }
}


#[link(name = "uav_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_GetResult_Request() -> *const std::ffi::c_void;
}

#[link(name = "uav_interfaces__rosidl_generator_c")]
extern "C" {
    fn uav_interfaces__action__FlyToAltitude_GetResult_Request__init(msg: *mut FlyToAltitude_GetResult_Request) -> bool;
    fn uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_GetResult_Request>, size: usize) -> bool;
    fn uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_GetResult_Request>);
    fn uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<FlyToAltitude_GetResult_Request>, out_seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_GetResult_Request>) -> bool;
}

// Corresponds to uav_interfaces__action__FlyToAltitude_GetResult_Request
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FlyToAltitude_GetResult_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub goal_id: unique_identifier_msgs::msg::rmw::UUID,

}



impl Default for FlyToAltitude_GetResult_Request {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !uav_interfaces__action__FlyToAltitude_GetResult_Request__init(&mut msg as *mut _) {
        panic!("Call to uav_interfaces__action__FlyToAltitude_GetResult_Request__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for FlyToAltitude_GetResult_Request {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_GetResult_Request__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for FlyToAltitude_GetResult_Request {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for FlyToAltitude_GetResult_Request where Self: Sized {
  const TYPE_NAME: &'static str = "uav_interfaces/action/FlyToAltitude_GetResult_Request";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_GetResult_Request() }
  }
}


#[link(name = "uav_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_GetResult_Response() -> *const std::ffi::c_void;
}

#[link(name = "uav_interfaces__rosidl_generator_c")]
extern "C" {
    fn uav_interfaces__action__FlyToAltitude_GetResult_Response__init(msg: *mut FlyToAltitude_GetResult_Response) -> bool;
    fn uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_GetResult_Response>, size: usize) -> bool;
    fn uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_GetResult_Response>);
    fn uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<FlyToAltitude_GetResult_Response>, out_seq: *mut rosidl_runtime_rs::Sequence<FlyToAltitude_GetResult_Response>) -> bool;
}

// Corresponds to uav_interfaces__action__FlyToAltitude_GetResult_Response
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct FlyToAltitude_GetResult_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub status: i8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub result: super::super::action::rmw::FlyToAltitude_Result,

}



impl Default for FlyToAltitude_GetResult_Response {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !uav_interfaces__action__FlyToAltitude_GetResult_Response__init(&mut msg as *mut _) {
        panic!("Call to uav_interfaces__action__FlyToAltitude_GetResult_Response__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for FlyToAltitude_GetResult_Response {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { uav_interfaces__action__FlyToAltitude_GetResult_Response__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for FlyToAltitude_GetResult_Response {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for FlyToAltitude_GetResult_Response where Self: Sized {
  const TYPE_NAME: &'static str = "uav_interfaces/action/FlyToAltitude_GetResult_Response";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__uav_interfaces__action__FlyToAltitude_GetResult_Response() }
  }
}






#[link(name = "uav_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__uav_interfaces__action__FlyToAltitude_SendGoal() -> *const std::ffi::c_void;
}

// Corresponds to uav_interfaces__action__FlyToAltitude_SendGoal
#[allow(missing_docs, non_camel_case_types)]
pub struct FlyToAltitude_SendGoal;

impl rosidl_runtime_rs::Service for FlyToAltitude_SendGoal {
    type Request = FlyToAltitude_SendGoal_Request;
    type Response = FlyToAltitude_SendGoal_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__uav_interfaces__action__FlyToAltitude_SendGoal() }
    }
}




#[link(name = "uav_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__uav_interfaces__action__FlyToAltitude_GetResult() -> *const std::ffi::c_void;
}

// Corresponds to uav_interfaces__action__FlyToAltitude_GetResult
#[allow(missing_docs, non_camel_case_types)]
pub struct FlyToAltitude_GetResult;

impl rosidl_runtime_rs::Service for FlyToAltitude_GetResult {
    type Request = FlyToAltitude_GetResult_Request;
    type Response = FlyToAltitude_GetResult_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__uav_interfaces__action__FlyToAltitude_GetResult() }
    }
}


