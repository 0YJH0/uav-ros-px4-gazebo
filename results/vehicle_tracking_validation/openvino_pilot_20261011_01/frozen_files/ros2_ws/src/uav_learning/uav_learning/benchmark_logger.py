#!/usr/bin/env python3

import csv
import json
import math
from pathlib import Path
from statistics import mean

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile,
    ReliabilityPolicy,
    DurabilityPolicy,
    HistoryPolicy,
)

from std_msgs.msg import String
from px4_msgs.msg import VehicleLocalPosition
from uav_interfaces.msg import TargetDetection


class BenchmarkLogger(Node):

    def __init__(self):
        super().__init__('benchmark_logger')

        self.declare_parameter(
            'results_dir',
            str(Path.home() / 'ROS2_manmade' / 'results'),
        )
        self.declare_parameter('image_width', 960.0)

        self.results_dir = Path(
            self.get_parameter('results_dir').value
        )
        self.image_width = float(
            self.get_parameter('image_width').value
        )

        self.results_dir.mkdir(
            parents=True,
            exist_ok=True,
        )
        self.csv_path = self.results_dir / 'benchmark.csv'

        self.px4_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self.trial_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self.state_sub = self.create_subscription(
            String,
            '/mission/state',
            self.state_callback,
            10,
        )

        self.event_sub = self.create_subscription(
            String,
            '/mission/event',
            self.event_callback,
            10,
        )

        self.target_sub = self.create_subscription(
            TargetDetection,
            '/perception/target',
            self.target_callback,
            10,
        )

        self.position_sub = self.create_subscription(
            VehicleLocalPosition,
            '/fmu/out/vehicle_local_position_v1',
            self.position_callback,
            self.px4_qos,
        )

        self.trial_info_sub = self.create_subscription(
            String,
            '/benchmark/trial_info',
            self.trial_info_callback,
            self.trial_qos,
        )

        self.trial_info = {}
        self.reset_run()

        self.get_logger().info(
            'Batch-capable benchmark logger started.'
        )
        self.get_logger().info(
            f'Results: {self.csv_path}'
        )

    def reset_run(self):
        self.run_started = False
        self.run_finished = False

        self.run_start_time = None
        self.run_end_time = None

        self.current_state = None
        self.state_enter_time = None
        self.state_start_times = {}
        self.state_durations = {}

        self.approach_success = False
        self.failure_reason = ''

        self.target_lost_count = 0
        self.approach_reacquire_count = 0

        self.approach_abs_pixel_errors = []
        self.approach_area_values = []

        self.approach_start_area = None
        self.approach_final_area = None

        self.home_x = None
        self.home_y = None
        self.home_z = None

        self.last_x = None
        self.last_y = None
        self.last_z = None

        self.latest_x = None
        self.latest_y = None
        self.latest_z = None

        self.trajectory_length_3d = 0.0

    def now_s(self):
        return self.get_clock().now().nanoseconds / 1e9

    @staticmethod
    def percentile(values, percentile):
        if not values:
            return float('nan')

        data = sorted(values)

        if len(data) == 1:
            return float(data[0])

        rank = percentile / 100.0 * (len(data) - 1)
        lower = int(math.floor(rank))
        upper = int(math.ceil(rank))

        if lower == upper:
            return float(data[lower])

        fraction = rank - lower

        return float(
            data[lower]
            + fraction * (data[upper] - data[lower])
        )

    def trial_info_callback(self, msg):
        try:
            info = json.loads(msg.data)
        except json.JSONDecodeError:
            self.get_logger().warning(
                f'Invalid trial_info JSON: {msg.data}'
            )
            return

        if self.run_started and not self.run_finished:
            self.get_logger().warning(
                'Received new trial_info before current run finished.'
            )

        self.trial_info = info
        self.reset_run()

        self.get_logger().info(
            'Prepared trial '
            f"{self.trial_info.get('trial_id', '?')} | "
            f"target=("
            f"{self.trial_info.get('target_x', '?')}, "
            f"{self.trial_info.get('target_y', '?')}, "
            f"{self.trial_info.get('target_z', '?')})"
        )

    def state_callback(self, msg):
        new_state = msg.data.strip()

        if not new_state:
            return

        now = self.now_s()

        if not self.run_started:
            self.run_started = True
            self.run_start_time = now
            self.get_logger().info(
                f'Run started in state {new_state}.'
            )

        if new_state == self.current_state:
            return

        previous_state = self.current_state

        if (
            previous_state is not None
            and self.state_enter_time is not None
        ):
            duration = now - self.state_enter_time
            self.state_durations[previous_state] = (
                self.state_durations.get(previous_state, 0.0)
                + duration
            )

        if (
            previous_state == 'APPROACH'
            and new_state == 'SEARCH'
        ):
            self.approach_reacquire_count += 1

        self.current_state = new_state
        self.state_enter_time = now

        if new_state not in self.state_start_times:
            self.state_start_times[new_state] = now

        self.get_logger().info(
            f'STATE: {previous_state} -> {new_state}'
        )

        if (
            new_state == 'DONE'
            and not self.run_finished
        ):
            self.finish_run()

    def event_callback(self, msg):
        event = msg.data.strip()

        if not event:
            return

        self.get_logger().info(
            f'EVENT: {event}'
        )

        if event == 'APPROACH_SUCCESS':
            self.approach_success = True

        elif event == 'SEARCH_TIMEOUT':
            self.failure_reason = 'SEARCH_TIMEOUT'

        elif event == 'APPROACH_TIMEOUT':
            self.failure_reason = 'APPROACH_TIMEOUT'

        elif event == 'APPROACH_TARGET_LOST':
            # Count controller-declared losses only.
            # This avoids double counting single-frame detector dropouts.
            self.target_lost_count += 1

    def target_callback(self, msg):
        if (
            self.current_state != 'APPROACH'
            or not bool(msg.detected)
        ):
            return

        pixel_error = (
            abs(float(msg.center_u_norm))
            * self.image_width
            / 2.0
        )

        self.approach_abs_pixel_errors.append(
            pixel_error
        )

        area = float(msg.area_ratio)
        self.approach_area_values.append(area)

        if self.approach_start_area is None:
            self.approach_start_area = area

        self.approach_final_area = area

    def position_callback(self, msg):
        if not msg.xy_valid or not msg.z_valid:
            return

        x = float(msg.x)
        y = float(msg.y)
        z = float(msg.z)

        if not self.run_started:
            return

        if self.home_x is None:
            self.home_x = x
            self.home_y = y
            self.home_z = z

        if self.last_x is not None:
            dx = x - self.last_x
            dy = y - self.last_y
            dz = z - self.last_z

            ds = math.sqrt(
                dx * dx + dy * dy + dz * dz
            )

            if ds < 5.0:
                self.trajectory_length_3d += ds

        self.last_x = x
        self.last_y = y
        self.last_z = z

        self.latest_x = x
        self.latest_y = y
        self.latest_z = z

    def finish_run(self):
        if self.run_finished:
            return

        self.run_finished = True
        self.run_end_time = self.now_s()

        if (
            self.current_state is not None
            and self.state_enter_time is not None
        ):
            self.state_durations[self.current_state] = (
                self.state_durations.get(
                    self.current_state,
                    0.0,
                )
                + (
                    self.run_end_time
                    - self.state_enter_time
                )
            )

        mission_time = (
            self.run_end_time - self.run_start_time
            if self.run_start_time is not None
            else float('nan')
        )

        search_time = self.state_durations.get(
            'SEARCH',
            0.0,
        )
        detect_time = self.state_durations.get(
            'DETECT',
            0.0,
        )
        approach_time = self.state_durations.get(
            'APPROACH',
            0.0,
        )

        acquisition_time = float('nan')

        if (
            'SEARCH' in self.state_start_times
            and 'DETECT' in self.state_start_times
        ):
            acquisition_time = (
                self.state_start_times['DETECT']
                - self.state_start_times['SEARCH']
            )

        mean_pixel_error = (
            mean(self.approach_abs_pixel_errors)
            if self.approach_abs_pixel_errors
            else float('nan')
        )

        p95_pixel_error = self.percentile(
            self.approach_abs_pixel_errors,
            95.0,
        )

        final_home_error = float('nan')

        if (
            self.home_x is not None
            and self.latest_x is not None
        ):
            dx = self.latest_x - self.home_x
            dy = self.latest_y - self.home_y
            final_home_error = math.sqrt(
                dx * dx + dy * dy
            )

        mission_success = bool(
            self.approach_success
        )

        if (
            not mission_success
            and not self.failure_reason
        ):
            self.failure_reason = 'MISSION_INCOMPLETE'

        row = {
            'trial_id': self.trial_info.get('trial_id', ''),
            'seed': self.trial_info.get('seed', ''),
            'target_x': self.trial_info.get('target_x', ''),
            'target_y': self.trial_info.get('target_y', ''),
            'target_z': self.trial_info.get('target_z', ''),
            'timestamp_s': f'{self.run_end_time:.3f}',
            'mission_success': int(mission_success),
            'failure_reason': self.failure_reason,
            'mission_time_s': f'{mission_time:.3f}',
            'search_time_s': f'{search_time:.3f}',
            'target_acquisition_time_s': (
                f'{acquisition_time:.3f}'
            ),
            'detect_time_s': f'{detect_time:.3f}',
            'approach_time_s': f'{approach_time:.3f}',
            'mean_abs_pixel_error_px': (
                f'{mean_pixel_error:.3f}'
            ),
            'p95_abs_pixel_error_px': (
                f'{p95_pixel_error:.3f}'
            ),
            'target_lost_count': self.target_lost_count,
            'approach_reacquire_count': (
                self.approach_reacquire_count
            ),
            'approach_start_area_ratio': (
                ''
                if self.approach_start_area is None
                else f'{self.approach_start_area:.6f}'
            ),
            'approach_final_area_ratio': (
                ''
                if self.approach_final_area is None
                else f'{self.approach_final_area:.6f}'
            ),
            'trajectory_length_3d_m': (
                f'{self.trajectory_length_3d:.3f}'
            ),
            'final_home_error_m': (
                f'{final_home_error:.3f}'
            ),
        }

        write_header = not self.csv_path.exists()

        with self.csv_path.open(
            'a',
            newline='',
            encoding='utf-8',
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=list(row.keys()),
            )

            if write_header:
                writer.writeheader()

            writer.writerow(row)

        self.get_logger().info(
            '========================================'
        )
        self.get_logger().info(
            'BENCHMARK RUN COMPLETE'
        )
        self.get_logger().info(
            f"Trial                : "
            f"{self.trial_info.get('trial_id', '?')}"
        )
        self.get_logger().info(
            f'Mission success      : {mission_success}'
        )
        self.get_logger().info(
            f'Mission time         : {mission_time:.2f} s'
        )
        self.get_logger().info(
            f'Search time          : {search_time:.2f} s'
        )
        self.get_logger().info(
            f'Acquisition time     : {acquisition_time:.2f} s'
        )
        self.get_logger().info(
            f'Approach time        : {approach_time:.2f} s'
        )
        self.get_logger().info(
            f'Mean pixel error     : {mean_pixel_error:.2f} px'
        )
        self.get_logger().info(
            f'P95 pixel error      : {p95_pixel_error:.2f} px'
        )
        self.get_logger().info(
            f'Target lost count    : {self.target_lost_count}'
        )
        self.get_logger().info(
            f'Reacquire count      : {self.approach_reacquire_count}'
        )
        self.get_logger().info(
            f'Trajectory length    : '
            f'{self.trajectory_length_3d:.2f} m'
        )
        self.get_logger().info(
            f'Final home error     : {final_home_error:.3f} m'
        )
        self.get_logger().info(
            f'CSV                  : {self.csv_path}'
        )
        self.get_logger().info(
            '========================================'
        )


def main(args=None):
    rclpy.init(args=args)
    node = BenchmarkLogger()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
