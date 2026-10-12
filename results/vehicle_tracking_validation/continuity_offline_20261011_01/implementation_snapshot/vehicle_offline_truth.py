"""Reconstruct missing evaluation-only projections from archived Gazebo poses."""

from bisect import bisect_left
import json
import math
import xml.etree.ElementTree as ET

import numpy as np

from vehicle_crossing_validation import NAMES, mesh_corners, project_box


def extend_truth(directory, truth, associations, assets):
    camera_path = assets / 'PX4-Autopilot/Tools/simulation/gz/models/uav_rgb_camera/model.sdf'
    model_path = assets / 'ros2_ws/src/uav_learning/config/models/tracking_car/model.sdf'
    camera = ET.parse(camera_path).find('.//sensor/camera')
    width, height = (int(camera.findtext('image/' + name)) for name in ('width', 'height'))
    focal = width / (2 * math.tan(float(camera.findtext('horizontal_fov')) / 2))
    intrinsic = [focal, 0., width / 2, 0., focal, height / 2, 0., 0., 1.]
    info = directory / 'identity_camera_info.json'
    if info.is_file():
        recorded = json.loads(info.read_text())
        if (recorded['width'], recorded['height']) != (width, height):
            raise ValueError('Archived camera dimensions differ from the model.')
        intrinsic = recorded['k']
    corners = mesh_corners(model_path)
    poses = sorted((json.loads(line) for line in (directory / 'identity_poses.jsonl').read_text().splitlines()),
                   key=lambda row: row['sim_s'])
    times = [row['sim_s'] for row in poses]

    def projection(stamp):
        sim = stamp[0] + stamp[1] / 1e9
        index = bisect_left(times, sim)
        nearby = poses[max(0, index - 1):index + 1]
        if not nearby:
            return None
        sample = min(nearby, key=lambda row: abs(row['sim_s'] - sim))
        age, values = abs(sample['sim_s'] - sim), sample['poses']
        if age > .15 or not all(name in values for name in (NAMES[0], NAMES[1], 'camera_link')):
            return None
        if np.linalg.norm(values['camera_link']['p']) > 1.:
            return None
        boxes = {name: project_box(corners, values[name], values[NAMES[0]], values['camera_link'],
                                 intrinsic, width, height) for name in NAMES[1:] if name in values}
        return {'projected_boxes': boxes, 'pose_age_sim_s': age,
                'panel_active': values.get('tracking_occluder', {}).get('p', [0, 0, -10])[2] > 0}

    checked, max_error = 0, 0.
    for stamp, evidence in truth.items():
        if not evidence.get('projected_boxes'):
            continue
        predicted = projection(stamp)
        if predicted is None:
            continue
        for name, box in evidence['projected_boxes'].items():
            rebuilt = predicted['projected_boxes'].get(name)
            if box is None and rebuilt is None:
                continue
            if box is None or rebuilt is None:
                raise ValueError('Reconstructed camera/model projection disagrees with archived evidence.')
            max_error = max(max_error, float(np.max(np.abs(np.array(box) - rebuilt))))
            checked += 1
    if checked < 10 or max_error > .01:
        raise ValueError(f'Calibration/model validation insufficient: {checked} boxes, error {max_error}px.')
    added = 0
    extended = dict(truth)
    for data in associations:
        stamp = data['stamp']['sec'], data['stamp']['nanosec']
        if stamp in extended:
            continue
        predicted = projection(stamp)
        if predicted is None:
            continue
        extended[stamp] = {'stamp': data['stamp'], 'phase': 'reconstructed',
                          'label': 'panel_occlusion_unscorable' if predicted['panel_active'] else 'unconfirmed',
                          'truth_source': 'archived_pose_reconstruction', **predicted}
        if predicted['panel_active']:
            extended[stamp].pop('projected_boxes')
        added += 1
    return extended, {'reconstructed_frames': added, 'calibration_checked_boxes': checked,
                      'calibration_max_error_px': max_error,
                      'limitation': 'Model-derived K validated against archived projections; bounding volumes, not instance masks.'}
