#!/usr/bin/env python3

import json
import random
import signal
import subprocess
import time
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    QoSProfile,
    ReliabilityPolicy,
    DurabilityPolicy,
    HistoryPolicy,
)

from std_msgs.msg import String


class BatchBenchmarkRunner(Node):

    def __init__(self):
        super().__init__('batch_benchmark_runner')

        self.declare_parameter('num_trials', 10)
        self.declare_parameter('seed', 20260920)

        self.declare_parameter('target_x_min', 14.0)
        self.declare_parameter('target_x_max', 18.0)
        self.declare_parameter('target_y_min', 14.0)
        self.declare_parameter('target_y_max', 19.0)
        self.declare_parameter('target_z', 2.5)

        self.declare_parameter('inter_trial_wait', 5.0)

        self.declare_parameter('approach_timeout', 130.0)
        self.declare_parameter(
            'approach_target_lost_timeout',
            1.2,
        )

        self.declare_parameter(
            'board_name',
            'red_target_board',
        )
        self.declare_parameter(
            'board_sdf',
            str(
                Path.home()
                / 'ROS2_manmade'
                / 'config'
                / 'red_target_board.sdf'
            ),
        )

        self.num_trials = int(
            self.get_parameter('num_trials').value
        )
        self.seed = int(
            self.get_parameter('seed').value
        )

        self.target_x_min = float(
            self.get_parameter('target_x_min').value
        )
        self.target_x_max = float(
            self.get_parameter('target_x_max').value
        )
        self.target_y_min = float(
            self.get_parameter('target_y_min').value
        )
        self.target_y_max = float(
            self.get_parameter('target_y_max').value
        )
        self.target_z = float(
            self.get_parameter('target_z').value
        )

        self.inter_trial_wait = float(
            self.get_parameter('inter_trial_wait').value
        )

        self.approach_timeout = float(
            self.get_parameter('approach_timeout').value
        )
        self.approach_target_lost_timeout = float(
            self.get_parameter(
                'approach_target_lost_timeout'
            ).value
        )

        self.board_name = str(
            self.get_parameter('board_name').value
        )
        self.board_sdf = str(
            self.get_parameter('board_sdf').value
        )

        self.trial_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self.trial_info_pub = self.create_publisher(
            String,
            '/benchmark/trial_info',
            self.trial_qos,
        )

        self.event_sub = self.create_subscription(
            String,
            '/mission/event',
            self.event_callback,
            10,
        )

        self.rng = random.Random(self.seed)

        self.schedule = []

        for trial_id in range(1, self.num_trials + 1):
            x = round(
                self.rng.uniform(
                    self.target_x_min,
                    self.target_x_max,
                ),
                2,
            )
            y = round(
                self.rng.uniform(
                    self.target_y_min,
                    self.target_y_max,
                ),
                2,
            )

            self.schedule.append(
                {
                    'trial_id': trial_id,
                    'seed': self.seed,
                    'target_x': x,
                    'target_y': y,
                    'target_z': self.target_z,
                }
            )

        self.current_index = -1
        self.current_trial = None

        self.mission_process = None
        self.waiting_for_mission_done = False

        self.next_trial_time = (
            time.monotonic() + 2.0
        )

        self.batch_complete = False

        self.ensure_target_exists()

        self.timer = self.create_timer(
            0.5,
            self.timer_callback,
        )

        self.get_logger().info(
            'Batch benchmark runner started.'
        )
        self.get_logger().info(
            f'Num trials : {self.num_trials}'
        )
        self.get_logger().info(
            f'Seed       : {self.seed}'
        )
        self.get_logger().info(
            'Target region: '
            f'x=[{self.target_x_min:.1f}, '
            f'{self.target_x_max:.1f}], '
            f'y=[{self.target_y_min:.1f}, '
            f'{self.target_y_max:.1f}], '
            f'z={self.target_z:.1f}'
        )
        self.get_logger().info(
            'Keep PX4, Agent, Camera Bridge, '
            'Perception and Benchmark Logger running.'
        )

    def run_command(self, command):
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            check=False,
        )

    def ensure_target_exists(self):
        command = [
            'gz',
            'service',
            '-s',
            '/world/default/create',
            '--reqtype',
            'gz.msgs.EntityFactory',
            '--reptype',
            'gz.msgs.Boolean',
            '--timeout',
            '2000',
            '--req',
            (
                f'sdf_filename: "{self.board_sdf}", '
                f'name: "{self.board_name}"'
            ),
        ]

        result = self.run_command(command)

        if result.returncode != 0:
            self.get_logger().warning(
                'Target create service returned non-zero. '
                'If the target already exists this may be harmless.'
            )

    def move_target(self, trial):
        request = (
            f'name: "{self.board_name}", '
            'position: {'
            f'x: {trial["target_x"]}, '
            f'y: {trial["target_y"]}, '
            f'z: {trial["target_z"]}'
            '}'
        )

        command = [
            'gz',
            'service',
            '-s',
            '/world/default/set_pose',
            '--reqtype',
            'gz.msgs.Pose',
            '--reptype',
            'gz.msgs.Boolean',
            '--timeout',
            '2000',
            '--req',
            request,
        ]

        result = self.run_command(command)

        if (
            result.returncode != 0
            or 'true' not in result.stdout.lower()
        ):
            self.get_logger().error(
                'Failed to move target.\n'
                f'stdout: {result.stdout}\n'
                f'stderr: {result.stderr}'
            )
            return False

        return True

    def publish_trial_info(self, trial):
        msg = String()
        msg.data = json.dumps(
            trial,
            ensure_ascii=False,
        )
        self.trial_info_pub.publish(msg)

    def start_mission(self):
        command = [
            'ros2',
            'run',
            'uav_learning',
            'px4_offboard_controller',
            '--ros-args',
            '-p',
            f'approach_timeout:={self.approach_timeout}',
            '-p',
            (
                'approach_target_lost_timeout:='
                f'{self.approach_target_lost_timeout}'
            ),
        ]

        self.mission_process = subprocess.Popen(
            command,
        )

        self.waiting_for_mission_done = True

    def stop_mission_process(self):
        if self.mission_process is None:
            return

        if self.mission_process.poll() is None:
            try:
                self.mission_process.send_signal(
                    signal.SIGINT
                )
                self.mission_process.wait(
                    timeout=5.0
                )
            except subprocess.TimeoutExpired:
                self.mission_process.terminate()

                try:
                    self.mission_process.wait(
                        timeout=3.0
                    )
                except subprocess.TimeoutExpired:
                    self.mission_process.kill()

        self.mission_process = None

    def start_next_trial(self):
        next_index = self.current_index + 1

        if next_index >= self.num_trials:
            self.batch_complete = True
            self.get_logger().info(
                '========================================'
            )
            self.get_logger().info(
                'BATCH BENCHMARK COMPLETE'
            )
            self.get_logger().info(
                f'Completed {self.num_trials} trials.'
            )
            self.get_logger().info(
                'Check ~/ROS2_manmade/results/benchmark.csv'
            )
            self.get_logger().info(
                '========================================'
            )
            return

        trial = self.schedule[next_index]

        self.get_logger().info(
            '========================================'
        )
        self.get_logger().info(
            f'STARTING TRIAL {trial["trial_id"]}'
            f' / {self.num_trials}'
        )
        self.get_logger().info(
            'Target: '
            f'({trial["target_x"]:.2f}, '
            f'{trial["target_y"]:.2f}, '
            f'{trial["target_z"]:.2f})'
        )

        if not self.move_target(trial):
            self.get_logger().error(
                'Aborting batch because target move failed.'
            )
            self.batch_complete = True
            return

        self.current_index = next_index
        self.current_trial = trial

        self.publish_trial_info(trial)

        # Give Gazebo / perception time to settle after moving target.
        time.sleep(1.0)

        self.start_mission()

    def event_callback(self, msg):
        event = msg.data.strip()

        if (
            event != 'MISSION_DONE'
            or not self.waiting_for_mission_done
        ):
            return

        trial_id = (
            self.current_trial['trial_id']
            if self.current_trial is not None
            else '?'
        )

        self.get_logger().info(
            f'Trial {trial_id} reported MISSION_DONE.'
        )

        self.waiting_for_mission_done = False
        self.stop_mission_process()

        self.next_trial_time = (
            time.monotonic()
            + self.inter_trial_wait
        )

    def timer_callback(self):
        if self.batch_complete:
            return

        if self.waiting_for_mission_done:
            if (
                self.mission_process is not None
                and self.mission_process.poll() is not None
            ):
                self.get_logger().error(
                    'Mission controller exited before MISSION_DONE. '
                    'Batch stopped for inspection.'
                )
                self.waiting_for_mission_done = False
                self.batch_complete = True

            return

        if time.monotonic() >= self.next_trial_time:
            self.start_next_trial()

    def destroy_node(self):
        self.stop_mission_process()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = BatchBenchmarkRunner()

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
