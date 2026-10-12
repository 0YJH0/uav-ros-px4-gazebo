"""Bounded YOLO zoom fallback; crop evidence never establishes target identity."""

import math

import numpy as np

from uav_learning.vehicle_target_lock import VehicleTargetLock


def target_view(lock, width, height, warp, now=None):
    if lock is None or lock.last_measurement is None:
        return None
    view = lock.last_measurement.reshape(4).copy()
    if (now is not None and math.isfinite(now) and lock.last_seen is not None
            and lock.last_predict is not None
            and 0 <= now - lock.last_seen <= lock.prediction_horizon
            and now >= lock.last_predict):
        # Preview the existing motion filter without predict(): ROI/GMC must
        # not advance association state or count a forecast as an observation.
        state = lock.filter.statePost.reshape(8)
        predicted = state[:4] + state[4:] * (now - lock.last_predict)
        if np.all(np.isfinite(predicted)):
            view = predicted.copy()
    warp, _ = VehicleTargetLock.validate_camera_motion(warp, width, height)
    if warp is not None:
        center = warp[:, :2] @ (view[:2] * [width, height]) + warp[:, 2]
        view[:2] = center / [width, height]
        view[2:] += math.log(math.sqrt(float(np.linalg.det(warp[:, :2]))))
    return view if np.all(np.isfinite(view)) else None


def choose_crop(view, width, height):
    if view is None or not np.all((view[:2] >= 0) & (view[:2] <= 1)):
        return None
    dimensions = np.exp(view[2:]) * [width, height]
    size = min(480, max(320, int(math.ceil(2.5 * max(dimensions)))))
    crop_width, crop_height = min(size, width), min(size, height)
    center = view[:2] * [width, height]
    left = int(np.clip(round(center[0] - crop_width / 2), 0, width - crop_width))
    top = int(np.clip(round(center[1] - crop_height / 2), 0, height - crop_height))
    return left, top, left + crop_width, top + crop_height


def needs_zoom(boxes, view, width, height, threshold):
    if view is None:
        return False
    dimensions = np.exp(view[2:])
    for row in boxes.cpu().numpy().data:
        center = (row[:2] + row[2:4]) / (2 * np.array([width, height]))
        sizes = np.maximum((row[2:4] - row[:2]) / [width, height], 1e-6)
        if (row[4] >= threshold and np.linalg.norm(center - view[:2]) <= 0.04
                and np.max(np.abs(np.log(sizes / dimensions))) <= math.log(2)):
            return False
    return True


def merge_boxes(full, crop, bounds, image_shape):
    import torch
    from torchvision.ops import batched_nms
    from ultralytics.engine.results import Boxes

    original = torch.as_tensor(full.data)
    zoom = torch.as_tensor(crop.data).clone()
    zoom[:, [0, 2]] += bounds[0]
    zoom[:, [1, 3]] += bounds[1]
    zoom[:, [0, 2]] = zoom[:, [0, 2]].clamp(0, image_shape[1])
    zoom[:, [1, 3]] = zoom[:, [1, 3]].clamp(0, image_shape[0])
    rows = torch.cat((original, zoom.to(original.device)), dim=0)
    sources = ['full_frame'] * len(full) + ['target_roi'] * len(crop)
    keep = batched_nms(rows[:, :4], rows[:, 4], rows[:, 5], 0.7)
    return Boxes(rows[keep], image_shape), [sources[index] for index in keep.cpu().tolist()]
