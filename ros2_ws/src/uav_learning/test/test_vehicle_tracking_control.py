import math
from types import SimpleNamespace

import numpy as np
import pytest
import rclpy
from rclpy.parameter import Parameter

from uav_interfaces.msg import TargetDetection
from uav_learning.vehicle_target_lock import VehicleTargetLock
from uav_learning.px4_offboard_controller import PX4OffboardController, MissionState


def candidate(track_id, cx, cy=0.5, size=0.1):
    return (track_id, size**2 * 1e6, 0.9,
            (cx - size / 2) * 1000, (cy - size / 2) * 1000,
            (cx + size / 2) * 1000, (cy + size / 2) * 1000)


def associate(lock, candidates, now, histograms=None):
    if histograms is None:
        histograms = [np.array([[1.0], [0.0], [0.0]], np.float32)] * len(candidates)
    return lock.select(candidates, histograms, 1000, 1000, now)


def test_predicts_moving_target_after_occlusion_and_id_change():
    lock = VehicleTargetLock()
    for index in range(20):
        assert associate(lock, [candidate(1, 0.25 + index * 0.01)], index * 0.2)
    # Four seconds hidden, then a moved target outside its old bounding box.
    for now in (4.0, 5.0, 6.0, 7.0):
        assert associate(lock, [], now) is None
    assert associate(lock, [candidate(9, 0.65)], 8.0) is None
    assert associate(lock, [candidate(9, 0.66)], 8.2) is None
    assert associate(lock, [candidate(9, 0.67)], 8.4)[0] == 9


def test_initial_acquisition_requires_central_vehicle_and_consecutive_frames():
    lock = VehicleTargetLock(acquisition_center_gate=0.35,
                             acquisition_confirm_frames=3)
    assert associate(lock, [candidate(99, 0.8, size=0.2)], 0.0) is None
    assert lock.last_seen is None
    for tick in range(3):
        selected = associate(lock, [candidate(1, 0.5), candidate(99, 0.8, size=0.2)],
                             0.2 + tick * 0.1)
        assert (selected is not None) == (tick == 2)
    assert lock.target_id == 1


def test_same_id_distractor_is_rejected_by_geometry_and_appearance():
    lock = VehicleTargetLock()
    assert associate(lock, [candidate(1, 0.3)], 0)
    assert associate(lock, [candidate(1, 0.7)], 0.2) is None
    blue = np.array([[0.0], [1.0], [0.0]], np.float32)
    assert associate(lock, [candidate(1, 0.3)], 0.4, [blue]) is None
    assert lock.target_id == 1


def test_similar_vehicles_at_crossing_do_not_force_identity_switch():
    lock = VehicleTargetLock()
    associate(lock, [candidate(1, 0.5)], 0)
    assert associate(lock, [candidate(2, 0.49), candidate(3, 0.51)], 1.0) is None
    assert lock.target_id == 1


def test_stale_view_requires_confirmation_instead_of_acquiring_largest_car():
    lock = VehicleTargetLock(recovery_timeout=2.0)
    associate(lock, [candidate(1, 0.5)], 0)
    assert associate(lock, [candidate(2, 0.5)], 3.0) is None
    assert lock.target_id == 1


@pytest.mark.parametrize('new_id', [1, 9, None])
def test_visual_reassociation_remains_possible_after_long_loss(new_id):
    lock = VehicleTargetLock()
    for tick in range(20):
        associate(lock, [candidate(1, 0.25 + tick * 0.01)], tick * 0.2)
    # The old prediction would be outside the frame after this gap.
    for tick in range(3):
        selected = associate(lock, [candidate(new_id, 0.6)], 30.0 + tick * 0.1)
        assert lock.mode == 'reacquiring'
        assert (selected is not None) == (tick == 2)
        assert lock.diagnostics[0]['mahalanobis_distance'] is None
    assert lock.last_seen > 30.0 and lock.reference is not None
    assert np.allclose(lock.filter.statePost[4:], 0)
    assert associate(lock, [candidate(new_id, 0.6)], 30.3) is not None
    assert lock.mode == 'tracking'


def test_long_loss_does_not_allow_wrong_appearance_or_ambiguous_cars():
    lock = VehicleTargetLock()
    associate(lock, [candidate(1, 0.5)], 0)
    blue = np.array([[0.0], [1.0], [0.0]], np.float32)
    assert associate(lock, [candidate(9, 0.5)], 20, [blue]) is None
    assert lock.diagnostics[0]['reason'] == 'appearance_gate'
    assert associate(lock, [candidate(2, 0.49), candidate(3, 0.51)], 20.1) is None
    assert all(d['reason'] == 'ambiguous_candidates' for d in lock.diagnostics)
    assert lock.target_id == 1


def test_diagnostics_include_all_failed_gates_and_actual_metrics():
    lock = VehicleTargetLock()
    associate(lock, [candidate(1, 0.3)], 0)
    blue = np.array([[0.0], [1.0], [0.0]], np.float32)
    assert associate(lock, [candidate(1, 0.7, size=0.4)], 0.2, [blue]) is None
    entry = lock.diagnostics[0]
    assert set(entry['rejection_reasons']) == {
        'center_gate', 'scale_gate', 'appearance_gate', 'mahalanobis_gate'}
    assert entry['center_error'] > entry['center_gate']
    assert entry['log_scale_error'] > entry['log_scale_gate']
    assert entry['appearance_similarity'] < entry['appearance_gate']
    assert entry['mahalanobis_distance'] > entry['mahalanobis_gate']


def test_long_reassociation_without_appearance_has_an_explicit_reason():
    lock = VehicleTargetLock()
    associate(lock, [candidate(1, 0.5)], 0, [None])
    assert associate(lock, [candidate(1, 0.5)], 20, [None]) is None
    assert lock.diagnostics[0]['reason'] == 'appearance_missing'


def test_long_reassociation_requires_spatially_consistent_consecutive_frames():
    lock = VehicleTargetLock()
    associate(lock, [candidate(1, 0.5)], 0)
    assert associate(lock, [candidate(9, 0.5)], 20) is None
    assert associate(lock, [candidate(9, 0.7)], 20.1) is None
    assert lock.pending_count == 1
    assert associate(lock, [candidate(9, 0.7)], 21) is None
    assert lock.pending_count == 1
    assert associate(lock, [], 21.1) is None
    assert lock.pending_count == 0


def test_idless_detection_can_continue_without_becoming_a_new_identity():
    lock = VehicleTargetLock()
    associate(lock, [candidate(1, 0.5)], 0)
    assert associate(lock, [candidate(None, 0.501)], 0.1)
    assert lock.target_id == 1
    assert associate(lock, [candidate(2, 0.502)], 0.2)


def test_pending_recovery_accepts_id_assignment_but_not_alternating_known_ids():
    lock = VehicleTargetLock()
    associate(lock, [candidate(1, 0.5)], 0.0)
    assert associate(lock, [candidate(None, 0.5)], 20.0) is None
    assert associate(lock, [candidate(9, 0.5)], 20.1) is None
    assert associate(lock, [candidate(9, 0.5)], 20.2) is not None
    assert lock.target_id == 9
    assert associate(lock, [candidate(10, 0.5)], 40.0) is None
    assert associate(lock, [candidate(11, 0.5)], 40.1) is None
    assert lock.pending_count == 1


@pytest.fixture
def controller(monkeypatch):
    rclpy.init()
    node = PX4OffboardController()
    node.timer.cancel()
    node.set_parameters([
        Parameter('tracking_enabled', value=True),
        Parameter('approach_forward_speed', value=2.0),
        Parameter('approach_slow_speed', value=0.6),
        Parameter('approach_max_setpoint_lead', value=1.5),
        Parameter('observation_gap_timeout', value=0.0),
    ])
    node.approach_forward_speed = 2.0
    node.approach_slow_speed = 0.6
    node.approach_max_setpoint_lead = 1.5
    node.local_position = SimpleNamespace(x=0.0, y=0.0, z=-3.0,
                                         heading=0.0, vx=0.8, vy=0.0,
                                         xy_valid=True, z_valid=True)
    node.home_x, node.home_y, node.takeoff_z = 0.0, 0.0, -3.0
    node.target_z = -3.0
    clock = [100.0]
    events = []
    monkeypatch.setattr(node, 'now_s', lambda: clock[0])
    node.last_position_msg_time = clock[0]
    monkeypatch.setattr(node, 'publish_offboard_stream', lambda: None)
    monkeypatch.setattr(node, 'publish_mission_state', lambda: None)
    monkeypatch.setattr(node, 'publish_mission_event', events.append)
    yield node, clock, events
    node.destroy_node()
    rclpy.shutdown()


def observe(node, detected=True, ex=0.0, area=0.02, confidence=0.0):
    msg = TargetDetection()
    msg.detected = detected
    msg.center_u_norm = ex
    msg.area_ratio = area
    msg.confidence = confidence
    node.target_detection_callback(msg)


@pytest.mark.parametrize('previously_tracking', [False, True])
def test_search_reconfirmation_resumes_the_correct_mission_phase(controller, previously_tracking):
    node, clock, events = controller
    if previously_tracking:
        node.transition_to(MissionState.TRACK)
        node.tracking_elapsed = 12.0
        node.range_feedforward = 0.8
        # A completed first approach must not abort a recovered TRACK.
        node.approach_deadline = 50.0
    deadline = node.tracking_deadline
    node.transition_to(MissionState.SEARCH)
    node.transition_to(MissionState.DETECT)
    clock[0] += node.detect_confirm_duration + 0.1
    node.last_position_msg_time = clock[0]
    for _ in range(node.detection_window):
        observe(node, area=0.01)
    node.timer_callback()
    assert node.state == (MissionState.TRACK if previously_tracking else MissionState.APPROACH)
    if previously_tracking:
        assert node.tracking_deadline == deadline
        assert node.tracking_elapsed == 12.0 and node.range_feedforward == 0.8
        assert 'TRACK_REACQUIRED' in events
        node.timer_callback()
        assert node.state == MissionState.TRACK and node.target_x > 0
    else:
        assert 'TRACK_REACQUIRED' not in events


def test_stable_history_does_not_resume_on_a_current_negative_frame(controller):
    node, clock, events = controller
    node.transition_to(MissionState.TRACK)
    node.transition_to(MissionState.DETECT)
    clock[0] += node.detect_confirm_duration + 0.1
    for _ in range(node.detection_window):
        observe(node)
    observe(node, detected=False)
    assert node.stable_detection()
    node.timer_callback()
    assert node.state == MissionState.SEARCH
    assert 'TRACK_REACQUIRED' not in events


def test_off_center_target_moves_forward_laterally_and_turns(controller):
    node, _, _ = controller
    node.transition_to(MissionState.APPROACH)
    observe(node, ex=0.25, area=0.01)
    node.timer_callback()
    assert node.state == MissionState.APPROACH
    assert node.target_x > 0 and node.target_y > 0 and node.target_yaw > 0
    assert math.hypot(node.target_x, node.target_y) <= 1.5


def test_track_at_desired_area_keeps_cruising(controller):
    node, _, _ = controller
    node.transition_to(MissionState.TRACK)
    node.range_feedforward = 0.8
    observe(node)
    node.timer_callback()
    assert node.target_x > 0 and node.tracking_elapsed == 0.1


def test_track_too_close_brakes_or_backs_up(controller):
    node, _, _ = controller
    node.transition_to(MissionState.TRACK)
    node.range_feedforward = 0.8
    observe(node, area=0.05)
    node.timer_callback()
    assert -0.061 <= node.target_x < 0


def test_extreme_image_error_stops_translation(controller):
    node, _, _ = controller
    node.transition_to(MissionState.APPROACH)
    observe(node, ex=0.95, area=0.01)
    node.timer_callback()
    assert node.target_x == 0 and node.target_y == 0 and node.target_yaw > 0


def test_repeated_frame_converges_to_fixed_bearing_instead_of_integrating_error(controller):
    node, clock, _ = controller
    node.transition_to(MissionState.TRACK)
    observe(node, ex=0.3)
    bearing = math.atan(0.3 * math.tan(1.204 / 2))
    assert node.observation_bearing == pytest.approx(bearing)
    for _ in range(40):
        clock[0] += 0.01
        node.local_position.heading = node.target_yaw
        node.local_position_callback(node.local_position)
        node.visual_follow(tracking=True)
        assert 0 < node.target_yaw <= bearing
        assert node.observation_bearing == pytest.approx(bearing)
    assert node.target_yaw > 0.95 * bearing


def test_lateral_correction_accounts_for_rotation_since_observation(controller):
    node, _, _ = controller
    node.transition_to(MissionState.TRACK)
    node.range_feedforward = 0.8
    observe(node, ex=0.3)
    heading = node.observation_bearing
    node.local_position.heading = heading
    node.target_yaw = heading
    node.target_x = node.target_y = 0
    node.visual_follow(tracking=True)
    lateral = -node.target_x * math.sin(heading) + node.target_y * math.cos(heading)
    assert abs(lateral) < 1e-8
    assert node.target_yaw == pytest.approx(heading)


def test_bearing_servo_takes_short_path_across_pi_and_obeys_yaw_limits(controller):
    node, _, _ = controller
    node.transition_to(MissionState.TRACK)
    heading = math.pi - 0.02
    node.local_position.heading = node.target_yaw = heading
    observe(node, ex=0.3)
    assert -math.pi <= node.observation_bearing < 0
    node.visual_follow(tracking=True)
    step = node.wrap_pi(node.target_yaw - heading)
    assert 0 < step <= node.approach_max_yaw_rate * node.TIMER_PERIOD
    node.target_yaw = node.wrap_pi(heading + 0.34)
    node.visual_follow(tracking=True)
    assert abs(node.wrap_pi(node.target_yaw - heading)) <= 0.35


def test_yaw_deadband_does_not_rotate_for_small_image_noise(controller):
    node, _, _ = controller
    node.transition_to(MissionState.TRACK)
    node.local_position.heading = node.target_yaw = 0.2
    observe(node, ex=0.03)
    node.visual_follow(tracking=True)
    assert node.observation_bearing > 0.2
    assert node.observation_yaw_target == pytest.approx(0.2)
    assert node.target_yaw == pytest.approx(0.2)


def test_yaw_deadband_does_not_discard_small_lateral_error(controller):
    node, _, _ = controller
    node.transition_to(MissionState.TRACK)
    node.range_feedforward = 0.8
    observe(node, ex=0.04)
    node.visual_follow(tracking=True)
    assert node.target_yaw == 0
    assert node.target_y > 0 and node.target_x > 0


def test_frozen_bearing_cannot_keep_following_after_camera_stream_goes_stale(controller):
    node, clock, _ = controller
    node.transition_to(MissionState.TRACK)
    observe(node, ex=0.3)
    node.visual_follow(tracking=True)
    yaw = node.target_yaw
    clock[0] += 0.6
    node.local_position_callback(node.local_position)
    assert node.visual_follow(tracking=True) is False
    assert node.target_x == node.target_y == 0 and node.target_yaw == yaw
    assert node.last_motion == (0.0, 0.0)


@pytest.mark.parametrize('invalid', ['stale_navigation', 'invalid_navigation', 'nan_area'])
def test_invalid_visual_control_never_counts_effective_track_time(controller, invalid):
    node, clock, _ = controller
    node.transition_to(MissionState.TRACK)
    if invalid == 'stale_navigation':
        node.last_position_msg_time = clock[0] - 0.6
    elif invalid == 'invalid_navigation':
        node.local_position.xy_valid = False
    observe(node, area=float('nan') if invalid == 'nan_area' else 0.02)
    node.timer_callback()
    assert node.tracking_elapsed == 0
    assert node.last_motion == (0.0, 0.0) and node.target_x == 0


def test_bottom_clipped_box_cannot_integrate_or_accelerate_forward(controller):
    node, _, _ = controller
    node.transition_to(MissionState.TRACK)
    node.range_feedforward = 0.8
    node.last_motion = (0.8, 0.0)
    observe(node, area=0.007)
    box = node.latest_detection
    box.center_v_norm = 0.85
    box.center_v = 499.5
    box.bbox_y = 459.
    box.bbox_height = 81.
    assert node.visual_follow(tracking=True)
    assert node.range_feedforward == 0.8
    assert 0 < node.last_motion[0] < 0.8
    assert node.framing_diagnostic['edge']
    assert node.target_z == -3.0


def test_unclipped_low_target_uses_vertical_feedback_and_smooth_speed(controller):
    node, _, _ = controller
    node.transition_to(MissionState.TRACK)
    node.range_feedforward = 0.8
    node.last_motion = (0.8, 0.)
    observe(node)
    node.latest_detection.center_v_norm = 0.70
    node.visual_follow(tracking=True)
    assert node.last_motion[0] == pytest.approx(0.74)
    assert node.range_feedforward == 0.8
    node.last_motion = (0., 0.)
    observe(node, area=0.01)
    node.visual_follow(tracking=True)
    assert node.last_motion[0] == pytest.approx(0.06)


def test_upper_clipped_target_uses_bounded_catchup_without_area_learning(controller):
    node, _, _ = controller
    node.transition_to(MissionState.TRACK)
    node.range_feedforward = 0.8
    node.last_motion = (0.8, 0.)
    observe(node, area=0.007)
    box = node.latest_detection
    box.center_v_norm, box.center_v = -0.85, 40.5
    box.bbox_y, box.bbox_height = 0., 81.
    assert node.visual_follow(tracking=True)
    assert node.range_feedforward == 0.8
    assert node.last_motion[0] == pytest.approx(0.86)
    assert node.framing_diagnostic['edge'] and node.framing_diagnostic['vertical_error'] < 0
    assert node.target_z == -3.0


def test_unclipped_upper_target_catchup_retains_speed_cap(controller):
    node, _, _ = controller
    node.transition_to(MissionState.TRACK)
    node.range_feedforward = node.approach_forward_speed
    node.last_motion = (node.approach_forward_speed, 0.)
    observe(node, area=0.02)
    node.latest_detection.center_v_norm = -0.70
    assert node.visual_follow(tracking=True)
    assert node.last_motion[0] <= node.approach_forward_speed
    assert node.framing_diagnostic['vertical_error'] == pytest.approx(-0.18)


def test_nan_vertical_coordinate_holds_without_counting_track_time(controller):
    node, _, _ = controller
    node.transition_to(MissionState.TRACK)
    observe(node)
    node.latest_detection.center_v_norm = float('nan')
    node.timer_callback()
    assert node.tracking_elapsed == 0 and node.last_motion == (0., 0.)


def test_follow_speed_slew_and_integral_use_px4_sample_time(controller):
    node, clock, _ = controller
    node.transition_to(MissionState.TRACK)
    node.local_position.timestamp_sample = 1_000_000
    node.last_follow_sample_us = 960_000
    observe(node, area=0.01)
    node.visual_follow(tracking=True)
    assert node.framing_diagnostic['motion_step_s'] == pytest.approx(0.04)
    assert node.last_motion[0] == pytest.approx(0.6 * 0.04)
    assert node.target_x == pytest.approx(node.last_motion[0] * 0.04)
    assert node.range_feedforward == pytest.approx(20.0 * 0.01 * 0.04)
    before = (node.target_x, node.target_y, node.target_yaw, node.range_feedforward)
    assert node.visual_follow(tracking=True)
    assert (node.target_x, node.target_y, node.target_yaw, node.range_feedforward) == before
    clock[0] += 0.1
    node.local_position.timestamp_sample += 40_000
    node.local_position_callback(node.local_position)
    observe(node, area=0.01)
    node.visual_follow(tracking=True)
    assert node.last_motion[0] == pytest.approx(0.6 * 0.08)


@pytest.mark.parametrize('stamp', [500_000, 2_000_000])
def test_px4_clock_reset_or_large_jump_holds_without_integrating(controller, stamp):
    node, _, _ = controller
    node.transition_to(MissionState.TRACK)
    node.last_follow_sample_us = 1_000_000
    node.local_position.timestamp_sample = stamp
    node.target_x = 1.0
    node.last_motion = (0.8, 0.)
    observe(node)
    assert not node.visual_follow(tracking=True)
    assert node.target_x == 0 and node.last_motion == (0., 0.)
    assert node.follow_clock_reason == 'clock_jump'


def test_slow_simulation_never_extends_wall_blind_timeout(controller):
    node, clock, events = controller
    node.local_position.timestamp_sample = 1_000_000
    enter_recovery(node)
    start = node.recovery_started_at
    for _ in range(50):
        clock[0] += 0.2
        node.local_position.timestamp_sample += 20_000
        node.local_position_callback(node.local_position)
        observe(node, detected=False)
        node.timer_callback()
    clock[0] = start + 10.1
    node.timer_callback()
    assert node.state == MissionState.SEARCH and 'RECOVERY_TIMEOUT' in events
    assert node.target_x == node.local_position.x


def sim_clock(node, seconds):
    microseconds = round(seconds * 1e6)
    node.motion_clock_callback(SimpleNamespace(clock=SimpleNamespace(
        sec=microseconds // 1_000_000, nanosec=(microseconds % 1_000_000) * 1000)))


def test_sim_follow_uses_gazebo_clock_not_dds_timestamp_corrections(controller):
    node, _, _ = controller
    node.set_parameters([Parameter('tracking_use_sim_clock', value=True)])
    node.transition_to(MissionState.TRACK)
    node.local_position.timestamp_sample = 8_000_000
    node.last_follow_sample_us = 1_000_000
    node.last_follow_sim_us = 1_000_000
    sim_clock(node, 1.04)
    observe(node, area=0.01)
    assert node.visual_follow(tracking=True)
    assert node.last_motion[0] == pytest.approx(0.024)
    assert node.framing_diagnostic['motion_step_s'] == pytest.approx(0.04)
    assert node.framing_diagnostic['clock_source'] == 'gazebo_clock'


def test_missing_or_stale_gazebo_clock_holds_then_can_resume(controller):
    node, clock, _ = controller
    node.set_parameters([Parameter('tracking_use_sim_clock', value=True)])
    node.transition_to(MissionState.TRACK)
    node.last_motion = (0.8, 0.)
    node.target_x = 1.
    observe(node)
    assert not node.visual_follow(tracking=True)
    assert node.target_x == 0 and node.last_motion == (0., 0.)
    sim_clock(node, 1.)
    assert node.visual_follow(tracking=True)
    clock[0] += 0.6
    node.local_position_callback(node.local_position)
    observe(node)
    assert not node.visual_follow(tracking=True)
    assert node.follow_clock_reason == 'stale_sim_clock'
    sim_clock(node, 1.04)
    assert node.visual_follow(tracking=True)


def test_gazebo_clock_reset_holds_and_recovers_on_next_step(controller):
    node, _, _ = controller
    node.set_parameters([Parameter('tracking_use_sim_clock', value=True)])
    node.transition_to(MissionState.TRACK)
    node.last_follow_sim_us = 5_000_000
    sim_clock(node, 1.)
    observe(node)
    assert not node.visual_follow(tracking=True)
    assert node.follow_clock_reason == 'clock_jump'
    sim_clock(node, 1.04)
    assert node.visual_follow(tracking=True)


def test_gazebo_slow_clock_never_extends_wall_blind_timeout(controller):
    node, clock, events = controller
    node.set_parameters([Parameter('tracking_use_sim_clock', value=True)])
    sim_clock(node, 1.)
    enter_recovery(node)
    start = node.recovery_started_at
    for index in range(51):
        clock[0] = start + index * 0.2
        sim_clock(node, 1. + index * 0.02)
        node.local_position_callback(node.local_position)
        observe(node, detected=False)
        node.timer_callback()
    assert node.state == MissionState.SEARCH and 'RECOVERY_TIMEOUT' in events
    assert node.target_x == node.local_position.x


def test_delayed_camera_and_slow_yaw_response_do_not_sustain_oscillation(controller):
    # Delayed planar feedback stub, not an airframe or a camera calibration.
    node, clock, _ = controller
    node.transition_to(MissionState.TRACK)
    node.local_position.heading = node.target_yaw = 0.3
    history, errors = [0.3] * 4, []
    for tick in range(160):
        clock[0] = 100.0 + tick * 0.1
        node.local_position_callback(node.local_position)
        if tick % 2 == 0:
            ex = math.tan(-history[-4]) / math.tan(1.204 / 2)
            observe(node, ex=ex)
        node.visual_follow(tracking=True)
        node.local_position.heading = node.wrap_pi(node.local_position.heading +
            node.wrap_pi(node.target_yaw - node.local_position.heading) * 0.1 / 0.8)
        history.append(node.local_position.heading)
        errors.append(abs(node.local_position.heading))
    assert max(errors[-40:]) < 0.06


def enter_recovery(node):
    node.transition_to(MissionState.TRACK)
    observe(node, area=0.01)
    node.visual_follow(tracking=True)
    observe(node, detected=False)
    node.timer_callback()
    assert node.state == MissionState.RECOVER


def test_occlusion_recovery_moves_bounded_and_resumes_after_three_real_hits(controller):
    node, clock, events = controller
    enter_recovery(node)
    clock[0] += 0.1
    node.timer_callback()
    assert 0 < node.target_x <= 0.08
    assert node.tracking_elapsed == 0
    for index in range(3):
        clock[0] += 0.1
        node.local_position_callback(node.local_position)
        observe(node)
        node.timer_callback()
        assert node.state == (MissionState.TRACK if index == 2 else MissionState.RECOVER)
    assert 'TARGET_RECOVERED' in events


def test_missing_camera_stream_holds_instead_of_blind_follow(controller):
    node, clock, _ = controller
    enter_recovery(node)
    clock[0] += 0.6
    node.timer_callback()
    assert node.target_x == 0 and node.target_y == 0


def test_recovery_distance_and_lead_are_bounded(controller):
    node, clock, _ = controller
    enter_recovery(node)
    for index in range(99):
        clock[0] += 0.1
        node.local_position_callback(node.local_position)
        observe(node, detected=False)
        node.timer_callback()
        assert node.target_x <= 4.0 + 1e-6
        node.local_position.x = node.target_x
        node.local_position.y = node.target_y
    assert node.state == MissionState.RECOVER


def test_recovery_timeout_stops_then_searches(controller):
    node, clock, events = controller
    enter_recovery(node)
    clock[0] += 10.1
    node.timer_callback()
    assert node.state == MissionState.SEARCH
    assert node.target_x == 0 and 'RECOVERY_TIMEOUT' in events


def test_controller_never_subscribes_to_unconfirmed_vehicle_candidates(controller):
    node, _, _ = controller
    topics = {subscription.topic_name for subscription in node.subscriptions}
    assert '/perception/target' in topics
    assert '/perception/vehicles' not in topics
    assert '/perception/association' not in topics


def test_invalid_position_never_allows_recovery_motion(controller):
    node, clock, _ = controller
    enter_recovery(node)
    node.local_position.xy_valid = False
    clock[0] += 0.1
    node.timer_callback()
    assert node.target_x == 0


def test_stale_navigation_holds_even_with_fresh_camera(controller):
    node, clock, _ = controller
    enter_recovery(node)
    clock[0] += 0.6
    observe(node, detected=False)
    node.timer_callback()
    assert node.target_x == 0


def test_approach_deadline_is_not_reset_by_recovery(controller):
    node, clock, _ = controller
    node.transition_to(MissionState.APPROACH)
    deadline = node.approach_deadline
    node.transition_to(MissionState.RECOVER)
    clock[0] += 5.0
    node.transition_to(MissionState.APPROACH)
    assert node.approach_deadline == deadline


def test_positive_flicker_does_not_extend_recovery_deadline(controller):
    node, clock, _ = controller
    enter_recovery(node)
    for index in range(11):
        clock[0] += 1.0
        observe(node, detected=index % 2 == 0)
        node.timer_callback()
    assert node.state == MissionState.SEARCH


def start_debounced_gap(node):
    node.set_parameters([Parameter('observation_gap_timeout', value=0.5)])
    node.transition_to(MissionState.TRACK)
    node.range_feedforward = 0.8
    observe(node)
    node.visual_follow(tracking=True)
    observe(node, detected=False)
    node.timer_callback()


def test_short_gap_does_not_leave_track_or_count_prediction_as_tracking(controller):
    node, clock, events = controller
    start_debounced_gap(node)
    assert node.state == MissionState.TRACK and node.tracking_elapsed == 0
    assert 'TRACK_OBSERVATION_GAP' in events and 'TRACK_TARGET_LOST' not in events
    assert 0 < node.target_x <= 1.5
    for index in range(3):
        clock[0] += 0.1
        node.local_position_callback(node.local_position)
        observe(node)
        node.timer_callback()
        assert node.state == MissionState.TRACK
        assert node.tracking_elapsed == (0.1 if index == 2 else 0)
    assert 'OBSERVATION_GAP_CLEARED' in events
    assert node.recovery_started_at is None


def test_duplicate_sim_clock_counts_visible_track_without_integrating(controller):
    node, _, _ = controller
    node.set_parameters([Parameter('tracking_use_sim_clock', value=True)])
    node.transition_to(MissionState.TRACK)
    sim_clock(node, 1.)
    observe(node)
    node.timer_callback()
    before = (node.target_x, node.target_y, node.target_yaw, node.range_feedforward)
    node.timer_callback()
    assert node.tracking_elapsed == pytest.approx(0.2)
    assert (node.target_x, node.target_y, node.target_yaw, node.range_feedforward) == before


@pytest.mark.parametrize('confidence,elapsed,cleared', [
    (0.8, 0.4, True), (0.5, 0.4, True), (0.49, 0.4, False),
    (float('nan'), 0.4, False), (0.8, 0.51, False),
])
def test_short_identity_confirmed_return_avoids_extra_controller_delay(
        controller, confidence, elapsed, cleared):
    node, clock, events = controller
    start_debounced_gap(node)
    started = node.recovery_started_at
    clock[0] += elapsed
    node.local_position_callback(node.local_position)
    observe(node, confidence=confidence)
    node.timer_callback()
    assert ('OBSERVATION_GAP_CLEARED' in events) == cleared
    if cleared:
        assert node.recovery_started_at is None
        assert node.tracking_elapsed == pytest.approx(0.1)
        assert 'TRACK_TARGET_LOST' not in events
    else:
        assert node.recovery_started_at == started
        assert node.recovery_positive_count == 1
        assert node.tracking_elapsed == 0


def test_strong_return_after_entering_recover_still_needs_three_frames(controller):
    node, clock, events = controller
    start_debounced_gap(node)
    clock[0] += 0.6
    node.local_position_callback(node.local_position)
    observe(node, detected=False)
    node.timer_callback()
    assert node.state == MissionState.RECOVER
    for index in range(3):
        clock[0] += 0.1
        node.local_position_callback(node.local_position)
        observe(node, confidence=0.9)
        node.timer_callback()
        assert node.state == (MissionState.TRACK if index == 2 else MissionState.RECOVER)
    assert 'TARGET_RECOVERED' in events


@pytest.mark.parametrize('smooth', [False, True])
def test_debounce_does_not_extend_ten_second_blind_limit_or_reset_confirmations(controller, smooth):
    node, clock, events = controller
    node.set_parameters([Parameter('smooth_recovery_setpoints', value=smooth)])
    start_debounced_gap(node)
    started = node.recovery_started_at
    clock[0] += 0.4
    node.local_position_callback(node.local_position)
    observe(node)
    node.timer_callback()
    clock[0] += 0.11
    node.local_position_callback(node.local_position)
    observe(node)
    node.timer_callback()
    assert node.state == MissionState.RECOVER and node.recovery_positive_count == 2
    assert node.recovery_started_at == started
    clock[0] = started + 10.0
    node.local_position_callback(node.local_position)
    observe(node, detected=False)
    node.timer_callback()
    assert node.state == MissionState.SEARCH and 'RECOVERY_TIMEOUT' in events
    assert node.target_x == node.local_position.x


@pytest.mark.parametrize('smooth', [False, True])
def test_debounce_and_recovery_share_four_meter_displacement_budget(controller, smooth):
    node, clock, _ = controller
    node.set_parameters([Parameter('smooth_recovery_setpoints', value=smooth)])
    start_debounced_gap(node)
    origin = node.recovery_origin
    for _ in range(99):
        clock[0] += 0.1
        node.local_position_callback(node.local_position)
        observe(node, detected=False)
        node.timer_callback()
        assert node.recovery_origin == origin
        assert math.hypot(node.target_x - origin[0], node.target_y - origin[1]) <= 4.0 + 1e-6
        node.local_position.x, node.local_position.y = node.target_x, node.target_y
    assert node.state == MissionState.RECOVER


def test_recovery_transition_and_pending_return_preserve_bounded_position_lead(controller):
    node, clock, _ = controller
    node.set_parameters([Parameter('smooth_recovery_setpoints', value=True)])
    start_debounced_gap(node)
    node.target_x = .7
    node.last_motion = (.8, 0.)
    before = node.target_x
    clock[0] += .6
    node.local_position_callback(node.local_position)
    observe(node, detected=False)
    node.timer_callback()
    assert node.state == MissionState.RECOVER and node.target_x == before
    for tick in range(3):
        clock[0] += .1
        node.local_position_callback(node.local_position)
        observe(node, confidence=.9)
        node.timer_callback()
        assert node.target_x >= before
        before = node.target_x
    assert node.state == MissionState.TRACK


def test_pending_short_return_does_not_pull_position_goal_back(controller):
    node, clock, _ = controller
    node.set_parameters([Parameter('smooth_recovery_setpoints', value=True)])
    start_debounced_gap(node)
    node.target_x = .7
    node.last_motion = (.8, 0.)
    clock[0] += .2
    node.local_position_callback(node.local_position)
    observe(node, confidence=.3)
    node.timer_callback()
    assert node.recovery_positive_count == 1 and node.target_x >= .7
    assert node.tracking_elapsed == 0


@pytest.mark.parametrize('invalid', ['camera', 'navigation'])
def test_entering_recovery_hard_stops_invalid_input_on_first_tick(controller, invalid):
    node, clock, _ = controller
    node.set_parameters([Parameter('smooth_recovery_setpoints', value=True)])
    node.transition_to(MissionState.TRACK)
    observe(node, detected=False)
    node.target_x = .7
    node.last_motion = (.8, 0.)
    if invalid == 'camera':
        node.last_detection_msg_time = clock[0] - .6
    else:
        node.last_position_msg_time = clock[0] - .6
    node.timer_callback()
    assert node.state == MissionState.RECOVER
    assert node.target_x == node.local_position.x and node.last_motion == (0., 0.)


def test_recovery_slew_respects_speed_and_shared_displacement_caps(controller):
    node, clock, _ = controller
    node.set_parameters([Parameter('smooth_recovery_setpoints', value=True)])
    start_debounced_gap(node)
    node.recovery_motion = (.8, 0.)
    node.last_motion = (.8, 0.)
    previous = .8
    for tick in range(1, 20):
        clock[0] = 100 + tick * .1
        node.local_position_callback(node.local_position)
        observe(node, detected=False)
        node.advance_recovery_prediction(tick * .1)
        speed = math.hypot(*node.last_motion)
        assert speed <= .8
        assert abs(speed-previous) <= .6 * .1 + 1e-6
        assert math.hypot(node.target_x-node.recovery_origin[0],
                          node.target_y-node.recovery_origin[1]) <= 4
        previous = speed


def test_duplicate_recovery_clock_keeps_goal_but_never_extends_deadline(controller):
    node, clock, _ = controller
    node.set_parameters([Parameter('smooth_recovery_setpoints', value=True)])
    node.set_parameters([Parameter('tracking_use_sim_clock', value=True)])
    sim_clock(node, 1.)
    start_debounced_gap(node)
    node.target_x = .7
    node.last_follow_sim_us = node.sim_motion_clock_us
    node.advance_recovery_prediction(.1)
    assert node.target_x == .7 and node.follow_clock_reason == 'duplicate_sample'
    clock[0] = node.recovery_started_at + 10.0
    node.local_position_callback(node.local_position)
    observe(node, detected=False)
    sim_clock(node, 1.)
    node.timer_callback()
    assert node.state == MissionState.SEARCH and node.target_x == node.local_position.x


@pytest.mark.parametrize('invalid', ['camera', 'navigation', 'position'])
@pytest.mark.parametrize('smooth', [False, True])
def test_debounce_holds_when_stream_or_navigation_is_not_valid(controller, invalid, smooth):
    node, clock, _ = controller
    node.set_parameters([Parameter('smooth_recovery_setpoints', value=smooth)])
    start_debounced_gap(node)
    clock[0] += 0.4
    if invalid != 'camera':
        observe(node, detected=False)
    if invalid == 'camera':
        node.last_detection_msg_time = clock[0] - 0.6
        node.local_position_callback(node.local_position)
    elif invalid == 'navigation':
        node.last_position_msg_time = clock[0] - 0.6
    else:
        node.local_position.xy_valid = False
    node.timer_callback()
    assert node.state == MissionState.TRACK
    assert node.target_x == node.local_position.x and node.tracking_elapsed == 0


def test_moving_target_lock_and_controller_recover_together(controller):
    # Deterministic feedback stub, not PX4/Gazebo flight or calibrated ranging.
    node, clock, events = controller
    node.transition_to(MissionState.TRACK)
    node.range_feedforward = 0.8
    lock = VehicleTargetLock()
    car_x, car_y = 10.0, 0.5
    states = []
    for tick in range(300):
        elapsed = tick * 0.1
        clock[0] = 100.0 + elapsed
        node.local_position_callback(node.local_position)
        dx, dy = car_x - node.local_position.x, car_y - node.local_position.y
        distance = math.hypot(dx, dy)
        bearing = node.wrap_pi(math.atan2(dy, dx) - node.local_position.heading)
        ex = math.tan(bearing) / math.tan(0.6)
        size = math.sqrt(2.0 / distance**2)
        hidden = 6.0 <= elapsed < 10.0
        detections = [] if hidden else [candidate(
            1 if elapsed < 10.0 else 9, 0.5 + ex / 2, size=size)]
        if tick > 0:
            detections.append(candidate(99, 0.9, size=0.2))
        selected = associate(lock, detections, elapsed)
        observe(node, detected=selected is not None, ex=ex, area=size**2)
        node.timer_callback()
        states.append(node.state)
        assert node.state in (MissionState.TRACK, MissionState.RECOVER)
        assert lock.target_id != 99
        p = node.local_position
        p.vx, p.vy = 2 * (node.target_x - p.x), 2 * (node.target_y - p.y)
        p.x, p.y = p.x + p.vx * 0.1, p.y + p.vy * 0.1
        p.heading = node.wrap_pi(p.heading + max(-0.035, min(
            0.035, node.wrap_pi(node.target_yaw - p.heading))))
        car_x += 0.08
    assert MissionState.RECOVER in states
    assert node.state == MissionState.TRACK
    assert events.count('TARGET_RECOVERED') == 1
    assert lock.target_id == 9
    assert node.local_position.x > 20.0
    assert 8.0 < car_x - node.local_position.x < 13.0
