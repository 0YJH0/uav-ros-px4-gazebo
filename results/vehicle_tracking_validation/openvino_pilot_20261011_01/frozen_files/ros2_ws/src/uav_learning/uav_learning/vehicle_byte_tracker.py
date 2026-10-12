"""Camera registration adapter; association and prediction remain Ultralytics ByteTrack."""

import math

import numpy as np
from ultralytics.trackers.byte_tracker import BYTETracker

from uav_learning.vehicle_target_lock import VehicleTargetLock


class CameraMotionByteTracker(BYTETracker):
    def update(self, results, img=None, camera_motion=None, **kwargs):
        self.camera_motion = None
        self.camera_motion_reason = 'unavailable'
        if img is not None:
            height, width = img.shape[:2]
            self.camera_motion, self.camera_motion_reason = VehicleTargetLock.validate_camera_motion(
                camera_motion, width, height)
        return super().update(results, img, **kwargs)

    def _pre_first_associate(self, strack_pool, unconfirmed, img, results_high):
        if self.camera_motion is None:
            return
        linear = self.camera_motion[:, :2]
        transform = np.eye(8)
        transform[:2, :2] = transform[4:6, 4:6] = linear
        scale = math.sqrt(float(np.linalg.det(linear)))
        # ByteTrack uses XYAH, not XYWH. Aspect ratio and its derivative must
        # not rotate with height; rotate centers/velocity and scale height only.
        transform[3, 3] = transform[7, 7] = scale
        for track in [*strack_pool, *unconfirmed]:
            track.mean = transform @ track.mean
            track.mean[:2] += self.camera_motion[:, 2]
            track.covariance = transform @ track.covariance @ transform.T
