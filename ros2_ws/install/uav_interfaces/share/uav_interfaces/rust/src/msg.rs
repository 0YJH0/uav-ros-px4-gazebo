#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to uav_interfaces__msg__TargetDetection

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct TargetDetection {

    // This member is not documented.
    #[allow(missing_docs)]
    pub stamp: builtin_interfaces::msg::Time,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::TargetDetection::default())
  }
}

impl rosidl_runtime_rs::Message for TargetDetection {
  type RmwMsg = super::msg::rmw::TargetDetection;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        stamp: builtin_interfaces::msg::Time::into_rmw_message(std::borrow::Cow::Owned(msg.stamp)).into_owned(),
        detected: msg.detected,
        confidence: msg.confidence,
        center_u: msg.center_u,
        center_v: msg.center_v,
        center_u_norm: msg.center_u_norm,
        center_v_norm: msg.center_v_norm,
        bbox_x: msg.bbox_x,
        bbox_y: msg.bbox_y,
        bbox_width: msg.bbox_width,
        bbox_height: msg.bbox_height,
        area_ratio: msg.area_ratio,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        stamp: builtin_interfaces::msg::Time::into_rmw_message(std::borrow::Cow::Borrowed(&msg.stamp)).into_owned(),
      detected: msg.detected,
      confidence: msg.confidence,
      center_u: msg.center_u,
      center_v: msg.center_v,
      center_u_norm: msg.center_u_norm,
      center_v_norm: msg.center_v_norm,
      bbox_x: msg.bbox_x,
      bbox_y: msg.bbox_y,
      bbox_width: msg.bbox_width,
      bbox_height: msg.bbox_height,
      area_ratio: msg.area_ratio,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      stamp: builtin_interfaces::msg::Time::from_rmw_message(msg.stamp),
      detected: msg.detected,
      confidence: msg.confidence,
      center_u: msg.center_u,
      center_v: msg.center_v,
      center_u_norm: msg.center_u_norm,
      center_v_norm: msg.center_v_norm,
      bbox_x: msg.bbox_x,
      bbox_y: msg.bbox_y,
      bbox_width: msg.bbox_width,
      bbox_height: msg.bbox_height,
      area_ratio: msg.area_ratio,
    }
  }
}


