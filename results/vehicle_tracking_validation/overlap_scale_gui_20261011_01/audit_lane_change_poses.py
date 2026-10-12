#!/usr/bin/env python3
"""Audit completed Gazebo pose logs without using perception associations."""

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import sys

import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path('/home/yjh/ROS2_manmade')
sys.path.insert(0, str(ROOT / 'scripts'))
from vehicle_crossing_validation import mesh_corners
from vehicle_lane_change import (START, LEFT_END, PASS_END, END, PHASES,
                                 lane_change_evidence, lane_change_geometry,
                                 lane_change_phase)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    parser.add_argument('--vehicle-speed', type=float, default=.8)
    args = parser.parse_args()
    if not math.isfinite(args.vehicle_speed) or args.vehicle_speed <= 0:
        parser.error('vehicle speed must be positive and finite')
    directory = args.run_directory.resolve()
    supervisor_file = directory / 'supervisor.json'
    if not supervisor_file.exists():
        parser.error('supervisor.json is absent; wait for complete simulator shutdown')
    supervisor = json.loads(supervisor_file.read_text())
    exit_codes = supervisor.get('process_exit_codes', {})
    if not exit_codes or any(code is None for code in exit_codes.values()):
        parser.error('supervisor has not recorded completed process exits')
    source = directory / 'identity_poses.jsonl'
    initial_stat = source.stat()
    model = ROOT / 'ros2_ws/src/uav_learning/config/models/tracking_car/model.sdf'
    corners = mesh_corners(model)
    measurements, plotted, phase_ranges = [], [], {}
    minimum_horizontal, minimum_road = None, None
    overhead = {name: {'observations': 0, 'minimum_reference_to_roof_vertical_m': None,
                      'minimum_context': None}
                for name in ('tracked_vehicle', 'crossing_vehicle', 'parked_vehicle')}
    total_rows, skipped_rows = 0, 0
    first_pair, last_pair = None, None
    previous_plot_motion = -math.inf
    with source.open() as stream:
        for line in stream:
            if not line.strip():
                continue
            total_rows += 1
            record = json.loads(line)
            sim_s, poses = float(record['sim_s']), record['poses']
            drone = poses.get('x500_perception_0')
            if drone is not None:
                for name, item in overhead.items():
                    if name not in poses:
                        continue
                    body = Rotation.from_quat(poses[name]['q']).apply(corners) + poses[name]['p']
                    lower, upper = body.min(0), body.max(0)
                    if np.all(np.asarray(drone['p'][:2]) >= lower[:2]) and np.all(
                            np.asarray(drone['p'][:2]) <= upper[:2]):
                        item['observations'] += 1
                        vertical = float(drone['p'][2] - upper[2])
                        if (item['minimum_reference_to_roof_vertical_m'] is None
                                or vertical < item['minimum_reference_to_roof_vertical_m']):
                            item['minimum_reference_to_roof_vertical_m'] = vertical
                            item['minimum_context'] = {
                                'sim_s': sim_s, 'uav_reference_position': drone['p'],
                                'car_position': poses[name]['p'], 'roof_world_z_m': float(upper[2]),
                            }
            if not all(name in poses for name in ('tracked_vehicle', 'crossing_vehicle')):
                skipped_rows += 1
                continue
            target, other = poses['tracked_vehicle'], poses['crossing_vehicle']
            motion = max(0.0, (target['p'][0] - 16.0) / args.vehicle_speed)
            phase = lane_change_phase(motion)
            geometry = lane_change_geometry(corners, target, other)
            row = {'sim_s': sim_s, 'motion_time': motion, 'maneuver_phase': phase, **geometry}
            measurements.append(row)
            context = {'sim_s': sim_s, 'motion_time': motion, 'maneuver_phase': phase,
                       'target_position': target['p'], 'distractor_position': other['p'],
                       'uav_reference_position': drone['p'] if drone else None, **geometry}
            first_pair = first_pair or context
            last_pair = context
            if (minimum_horizontal is None or geometry['world_horizontal_clearance_m']
                    < minimum_horizontal['world_horizontal_clearance_m']):
                minimum_horizontal = context
            if minimum_road is None or geometry['distractor_road_margin_m'] < minimum_road['distractor_road_margin_m']:
                minimum_road = context
            bounds = phase_ranges.setdefault(phase, {
                'first_sim_s': sim_s, 'last_sim_s': sim_s, 'first_motion_s': motion,
                'last_motion_s': motion, 'relative_x_min_m': math.inf, 'relative_x_max_m': -math.inf,
                'lane_y_min_m': math.inf, 'lane_y_max_m': -math.inf,
            })
            bounds['last_sim_s'], bounds['last_motion_s'] = sim_s, motion
            bounds['relative_x_min_m'] = min(bounds['relative_x_min_m'], geometry['relative_longitudinal_m'])
            bounds['relative_x_max_m'] = max(bounds['relative_x_max_m'], geometry['relative_longitudinal_m'])
            bounds['lane_y_min_m'] = min(bounds['lane_y_min_m'], geometry['distractor_lane_y_m'])
            bounds['lane_y_max_m'] = max(bounds['lane_y_max_m'], geometry['distractor_lane_y_m'])
            if motion - previous_plot_motion >= .03:
                plotted.append({**row, 'target_x': target['p'][0], 'target_y': target['p'][1],
                                'other_x': other['p'][0], 'other_y': other['p'][1]})
                previous_plot_motion = motion
    final_stat = source.stat()
    if (initial_stat.st_size, initial_stat.st_mtime_ns) != (final_stat.st_size, final_stat.st_mtime_ns):
        raise RuntimeError('Pose log changed during audit; no complete report was generated')
    if not measurements:
        raise RuntimeError('No matched target/distractor pose pairs')
    evidence = lane_change_evidence(measurements)
    result = {
        'audit': 'full_gazebo_pose_geometry',
        'source': str(source.relative_to(ROOT)), 'source_sha256': sha256(source),
        'geometry_helper_sha256': sha256(ROOT / 'scripts/vehicle_lane_change.py'),
        'audit_script_sha256': sha256(Path(__file__).resolve()),
        'vehicle_speed_m_s': args.vehicle_speed, 'total_pose_records': total_rows,
        'measured_pose_pairs': len(measurements), 'skipped_missing_car_pairs': skipped_rows,
        'supervisor_autonomous_passed': supervisor.get('autonomous_passed'),
        'phase_ranges': phase_ranges, 'scenario_evidence': evidence,
        'minimum_horizontal_clearance_context': minimum_horizontal,
        'minimum_road_margin_context': minimum_road,
        'first_pair': first_pair, 'last_pair': last_pair,
        'uav_reference_over_car_aabb': overhead,
        'limitations': [
            'Uses every logged Gazebo pose message, not perception association samples.',
            'Pose samples do not prove continuous-time clearance between samples.',
            'Separating-axis gap is a conservative horizontal mesh-box separation bound.',
            'Maneuver phase is derived from measured target X and the configured target speed.',
            'UAV vertical check uses its model reference point over each car world-axis-aligned XY box.',
            'UAV arms, rotors, body size, and full 3D collision volumes are not checked.',
            'This geometry audit does not certify target identity or replace flight safety auditing.',
        ],
    }
    output = directory / 'full_pose_geometry_audit.json'
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')

    os.environ.setdefault('MPLCONFIGDIR', '/tmp/uav-lane-change-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(3, 1, figsize=(13, 10), gridspec_kw={'height_ratios': [1.4, 1, 1]})
    x = np.array([row['motion_time'] for row in plotted])
    axes[0].plot([row['target_x'] for row in plotted], [row['target_y'] for row in plotted],
                 color='#942928', linewidth=2, label='Original red target')
    axes[0].plot([row['other_x'] for row in plotted], [row['other_y'] for row in plotted],
                 color='#e04b44', linestyle='--', linewidth=2, label='Red overtaking distractor')
    for y in (-6, -2, 2, 6):
        axes[0].axhline(y, color='#a0a0a0', linestyle='--' if abs(y) == 2 else '-', linewidth=.8)
    for boundary, label in ((START, 'Left lane change'), (LEFT_END, 'Pass'),
                            (PASS_END, 'Merge center'), (END, 'Ahead follow')):
        selected = min(plotted, key=lambda row: abs(row['motion_time'] - boundary))
        axes[0].scatter(selected['other_x'], selected['other_y'], color='#252525', s=25, zorder=5)
        axes[0].annotate(label, (selected['other_x'], selected['other_y']),
                         xytext=(0, 14 if selected['other_y'] < 1 else -24),
                         textcoords='offset points', ha='center', fontsize=8)
    axes[0].set_ylim(-6.6, 6.6)
    axes[0].set(xlabel='World X (m)', ylabel='World Y (m)', title='Measured Gazebo vehicle trajectories')
    axes[0].legend(loc='lower right')
    axes[1].plot(x, [row['relative_longitudinal_m'] for row in plotted], color='#176b87')
    axes[1].axhline(0, color='#666666', linewidth=.8)
    axes[1].set(ylabel='Distractor - target X (m)', xlabel='Vehicle motion time (simulation s)')
    axes[2].plot(x, [row['world_horizontal_clearance_m'] for row in plotted],
                 color='#347a3c', label='Conservative body clearance')
    axes[2].plot(x, [row['distractor_road_margin_m'] for row in plotted],
                 color='#916525', label='Road-barrier inner-edge margin')
    axes[2].axhline(.5, color='#777777', linewidth=.8, linestyle=':')
    axes[2].set(ylabel='Distance (m)', xlabel='Vehicle motion time (simulation s)')
    axes[2].legend(loc='upper right')
    for ax in axes:
        ax.grid(alpha=.15)
    for ax in axes[1:]:
        for boundary in (START, LEFT_END, PASS_END, END):
            ax.axvline(boundary, color='#bbbbbb', linewidth=.8, linestyle='--')
    fig.suptitle('Red lane-change overtaking: complete pose-log audit', fontsize=14)
    fig.tight_layout()
    plot = directory / 'lane_change_trajectory.png'
    fig.savefig(plot, dpi=160)
    plt.close(fig)
    print(json.dumps({'output': str(output), 'plot': str(plot),
                      'scenario_evidence': evidence, 'overhead_checks': overhead}, indent=2))


if __name__ == '__main__':
    main()
