import importlib.util
from collections import deque
import json
from io import StringIO
from pathlib import Path
from types import SimpleNamespace

import pytest


spec = importlib.util.spec_from_file_location(
    'vehicle_validation', Path(__file__).resolve().parents[4]
    / 'scripts/validate_vehicle_tracking.py')
validation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validation)

analysis_spec = importlib.util.spec_from_file_location(
    'association_analysis', Path(__file__).resolve().parents[4]
    / 'scripts/analyze_vehicle_association.py')
analysis = importlib.util.module_from_spec(analysis_spec)
analysis_spec.loader.exec_module(analysis)

control_spec = importlib.util.spec_from_file_location(
    'control_analysis', Path(__file__).resolve().parents[4]
    / 'scripts/analyze_vehicle_follow_control.py')
control_analysis = importlib.util.module_from_spec(control_spec)
control_spec.loader.exec_module(control_analysis)

comparison_spec = importlib.util.spec_from_file_location(
    'detector_comparison', Path(__file__).resolve().parents[4]
    / 'scripts/compare_vehicle_detectors.py')
comparison = importlib.util.module_from_spec(comparison_spec)
comparison_spec.loader.exec_module(comparison)


def test_model_comparison_uses_only_paired_raw_frames_in_requested_window(tmp_path):
    entries = [
        {'wall_s': 1.0, 'raw_image': '00001.0_raw.png'},
        {'wall_s': 2.0, 'raw_image': None},
        {'wall_s': 3.0, 'raw_image': '00003.0_raw.png'},
    ]
    (tmp_path / 'image_manifest.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in entries))
    assert comparison.raw_entries(tmp_path, 2.0, 4.0) == [entries[2]]


def test_follow_control_analysis_excludes_return_and_stale_navigation():
    row = {'wall_s': 2.0, 'state': 'TRACK', 'position_ned': [0, 4, -3],
           'navigation': {'heading_rad': 3.12, 'xy_valid': True, 'z_valid': True, 'wall_s': 1.9},
           'setpoint': {'yaw_rad': -3.12, 'wall_s': 1.9},
           'vehicle_ground_truth': {'x': 16, 'wall_s': 1.9}}
    stale = {**row, 'wall_s': 3.0, 'state': 'RECOVER'}
    rows = control_analysis.follow_window([
        {**row, 'state': 'APPROACH'}, row, stale,
        {**row, 'wall_s': 4.0, 'state': 'RETURN', 'position_ned': [0, 100, -3]},
        {**row, 'wall_s': 5.0, 'state': 'DONE'}])
    report = control_analysis.summarize(rows)
    assert report['sample_count'] == 2 and report['fresh_navigation_command_samples'] == 1
    assert report['yaw_command_lead_max_deg'] < 3
    assert report['forward_gap_start_m'] == report['forward_gap_end_m'] == 12
    assert report['maximum_uav_east_m'] == 4


def test_follow_control_analysis_handles_missing_or_invalid_evidence():
    row = {'wall_s': 2.0, 'state': 'TRACK',
           'navigation': {'heading_rad': float('nan'), 'xy_valid': True, 'z_valid': True, 'wall_s': 2.0},
           'setpoint': {'yaw_rad': 0.0, 'wall_s': 2.0}}
    report = control_analysis.summarize([row, {'wall_s': 2.1, 'state': 'RECOVER'}])
    assert report['fresh_navigation_command_samples'] == 0
    assert report['yaw_command_lead_max_deg'] is None
    assert report['forward_gap_end_m'] is None
    assert control_analysis.follow_window([{'state': 'APPROACH'}]) == []


def test_association_summary_separates_frame_and_candidate_failures(tmp_path):
    frames = [
        {'wall_s': 1.0, 'vehicle_detected': True, 'identity_confirmed': True,
         'reason': 'confirmed', 'mode': 'tracking', 'locked_track_id': 7,
         'processing_s': 0.1, 'candidates': []},
        {'wall_s': 2.0, 'vehicle_detected': True, 'identity_confirmed': False,
         'reason': 'all_candidates_rejected', 'mode': 'tracking', 'locked_track_id': 7,
         'processing_s': 0.2, 'candidates': [
             {'track_id': 7, 'accepted': False, 'rejection_reasons': ['center_gate', 'mahalanobis_gate']},
             {'track_id': 9, 'accepted': False, 'rejection_reasons': ['center_gate']}]},
        {'wall_s': 3.0, 'vehicle_detected': False, 'identity_confirmed': False,
         'reason': 'no_candidates', 'mode': 'tracking', 'candidates': []},
        {'wall_s': 20.0, 'vehicle_detected': True, 'identity_confirmed': True,
         'reason': 'confirmed', 'mode': 'reacquiring', 'locked_track_id': 19,
         'elapsed_since_confirmed_s': 19.0, 'candidates': []},
    ]
    (tmp_path / 'association.jsonl').write_text(''.join(json.dumps(frame) + '\n' for frame in frames))
    (tmp_path / 'samples.jsonl').write_text(''.join(json.dumps(sample) + '\n' for sample in [
        {'wall_s': 0.5, 'state': 'TAKEOFF'}, {'wall_s': 1.5, 'state': 'APPROACH'},
        {'wall_s': 3.5, 'state': 'RETURN'}]))
    report = analysis.analyze(tmp_path)
    window = report['approach_follow_window']
    assert window['frame_count'] == 2
    assert window['visible_but_unconfirmed_frames'] == 1
    assert window['no_vehicle_frames'] == 1
    assert window['candidate_rejection_counts']['center_gate'] == 2
    assert window['locked_id_rejection_counts']['center_gate'] == 1
    assert report['all_frames']['long_loss_reacquisitions'][0]['track_id'] == 19


def test_association_summary_handles_absent_approach_and_empty_timings(tmp_path):
    (tmp_path / 'association.jsonl').write_text('')
    (tmp_path / 'samples.jsonl').write_text('{"wall_s": 1.0, "state": "TAKEOFF"}\n')
    report = analysis.analyze(tmp_path)
    assert report['approach_follow_window']['start_wall_s'] is None
    assert report['all_frames']['processing_p95_s'] is None
    assert report['all_frames']['frame_interval_max_s'] is None


def test_association_summary_counts_confirmed_weak_evidence_and_bytetrack_gmc():
    frames = [
        {'wall_s': 1.0, 'vehicle_detected': True, 'identity_confirmed': False,
         'reason': 'pending_confirmation', 'camera_motion': {'bytetrack_reason': 'applied'},
         'candidates': [{'accepted': False, 'weak_idless_candidate': True}]},
        {'wall_s': 1.1, 'vehicle_detected': True, 'identity_confirmed': True,
         'reason': 'confirmed', 'camera_motion': {'bytetrack_reason': 'applied'},
         'candidates': [{'accepted': True, 'weak_idless_confirmed': True}]},
        {'wall_s': 1.2, 'vehicle_detected': True, 'identity_confirmed': True,
         'reason': 'confirmed', 'camera_motion': {'bytetrack_reason': 'warp_bounds'},
         'candidates': [{'accepted': True, 'low_confidence_continuation': True}]},
    ]
    report = analysis.summarize(frames)
    assert report['weak_idless_confirmed_frames'] == 1
    assert report['low_confidence_confirmed_frames'] == 1
    assert report['bytetrack_camera_motion_counts'] == {'applied': 2, 'warp_bounds': 1}


def test_association_summary_separates_roi_detection_from_identity():
    frames = [
        {'wall_s': 1.0, 'vehicle_detected': True, 'identity_confirmed': False,
         'reason': 'pending_confirmation',
         'detector': {'roi_reason': 'completed', 'full_frame_count': 0},
         'candidates': [{'accepted': False, 'detector_source': 'target_roi'}]},
        {'wall_s': 1.1, 'vehicle_detected': True, 'identity_confirmed': True,
         'reason': 'confirmed',
         'detector': {'roi_reason': 'completed', 'full_frame_count': 0},
         'candidates': [{'accepted': True, 'detector_source': 'target_roi'}]},
    ]
    summary = analysis.summarize(frames)
    assert summary['roi_only_vehicle_frames'] == 2
    assert summary['roi_confirmed_frames'] == 1
    assert summary['roi_reason_counts'] == {'completed': 2}


def test_follow_visibility_includes_recovery_and_stale_streams():
    recorder = SimpleNamespace(
        follow_started=True, state='TRACK', follow_wall_time=0.0,
        follow_visible_wall_time=0.0, last_follow_tick=0.0,
        last_target_time=0.0, target={'detected': True})
    recorder.follow_active = lambda: validation.ValidationRecorder.follow_active(recorder)
    validation.ValidationRecorder.accumulate_follow(recorder, 0.2)
    recorder.state = 'RECOVER'
    # Even a stale positive observation stops counting after half a second.
    validation.ValidationRecorder.accumulate_follow(recorder, 2.0)
    recorder.state = 'SEARCH'
    recorder.target = {'detected': False}
    validation.ValidationRecorder.accumulate_follow(recorder, 4.0)
    assert recorder.follow_wall_time == 4.0
    assert recorder.follow_visible_wall_time == 0.5
    recorder.state = 'RETURN'
    validation.ValidationRecorder.accumulate_follow(recorder, 6.0)
    assert recorder.follow_wall_time == 4.0


def test_recorder_saves_each_candidate_rejection_separately_from_target():
    recorder = SimpleNamespace(association_file=StringIO(), latest_association=None,
                               elapsed=lambda: 12.0)
    status = {'vehicle_detected': True, 'identity_confirmed': False,
              'candidates': [{'track_id': 52, 'reason': 'center_gate'}]}
    validation.ValidationRecorder.association_callback(
        recorder, SimpleNamespace(data=json.dumps(status)))
    saved = json.loads(recorder.association_file.getvalue())
    assert saved['wall_s'] == 12.0 and saved['vehicle_detected']
    assert not saved['identity_confirmed']
    assert saved['candidates'][0]['reason'] == 'center_gate'


def test_recorder_counts_search_based_tracking_recovery_once():
    recorder = SimpleNamespace(
        events=[], elapsed=lambda: 12.0,
        occlusions=[{'end_wall_s': 10.0, 'confirmed_recovery_s': None},
                    {'end_wall_s': None, 'confirmed_recovery_s': None}])
    validation.ValidationRecorder.event_callback(recorder, SimpleNamespace(data='TRACK_REACQUIRED'))
    assert recorder.occlusions[0]['confirmed_recovery_s'] == 2.0
    assert recorder.occlusions[1]['confirmed_recovery_s'] is None
    recorder.elapsed = lambda: 15.0
    validation.ValidationRecorder.event_callback(recorder, SimpleNamespace(data='TARGET_RECOVERED'))
    assert recorder.occlusions[0]['confirmed_recovery_s'] == 2.0


def test_recorder_captures_navigation_and_command_without_using_it_for_control():
    recorder = SimpleNamespace(position=None, home=None, elapsed=lambda: 12.0)
    position = SimpleNamespace(x=1.0, y=2.0, z=-3.0, heading=0.4,
                               vx=0.5, vy=0.6, vz=0.0, xy_valid=True, z_valid=True,
                               timestamp_sample=2_000_000, timestamp=2_010_000)
    validation.ValidationRecorder.position_callback(recorder, position)
    validation.ValidationRecorder.setpoint_callback(
        recorder, SimpleNamespace(position=[1.1, 2.1, -3.0], yaw=0.45))
    assert recorder.navigation['heading_rad'] == 0.4
    assert recorder.navigation['velocity_ned'] == [0.5, 0.6, 0.0]
    assert recorder.navigation['timestamp_sample_us'] == 2_000_000
    assert recorder.navigation['timestamp_us'] == 2_010_000
    assert recorder.setpoint['yaw_rad'] == 0.45 and recorder.setpoint['wall_s'] == 12.0


def test_recorder_serializes_actual_ros_setpoint_arrays():
    from rclpy.serialization import serialize_message, deserialize_message
    recorder = SimpleNamespace(elapsed=lambda: 12.0)
    message = validation.TrajectorySetpoint(position=[1.1, 2.1, -3.0], yaw=0.45)
    received = deserialize_message(serialize_message(message), validation.TrajectorySetpoint)
    validation.ValidationRecorder.setpoint_callback(recorder, received)
    saved = json.loads(json.dumps(recorder.setpoint, allow_nan=False))
    assert abs(saved['yaw_rad'] - 0.45) < 1e-6
    assert abs(saved['position_ned'][0] - 1.1) < 1e-6


def test_recorder_pairs_unannotated_frame_by_exact_camera_stamp(tmp_path):
    import cv2
    import numpy as np
    from cv_bridge import CvBridge
    bridge = CvBridge()
    recorder = SimpleNamespace(directory=tmp_path, bridge=bridge, raw_images=deque(maxlen=64),
                               state='TRACK', elapsed=lambda: 12.0, last_image=0.0)
    pixels = np.full((24, 32, 3), 123, np.uint8)
    raw = bridge.cv2_to_imgmsg(pixels, 'bgr8')
    raw.header.stamp.sec = 7
    validation.ValidationRecorder.raw_image_callback(recorder, raw)
    debug = bridge.cv2_to_imgmsg(np.zeros_like(pixels), 'bgr8')
    debug.header.stamp.sec = 7
    validation.ValidationRecorder.image_callback(recorder, debug)
    manifest = json.loads((tmp_path / 'image_manifest.jsonl').read_text())
    np.testing.assert_array_equal(cv2.imread(str(tmp_path / manifest['raw_image'])), pixels)
    assert manifest['stamp']['sec'] == 7
    recorder.last_image = 0.0
    debug.header.stamp.sec = 8
    validation.ValidationRecorder.image_callback(recorder, debug)
    manifest = json.loads((tmp_path / 'image_manifest.jsonl').read_text().splitlines()[-1])
    assert manifest['raw_image'] is None


def test_perfect_track_only_detection_cannot_hide_long_recovery(tmp_path):
    recorder = SimpleNamespace(
        directory=tmp_path, state='DONE', finished=False,
        track_observations=[{'detected': True, 'error_x': 0.0}],
        events=[{'event': 'TRACK_COMPLETE'}],
        vehicle_positions=[{'x': 0.0, 'y': 0.0}, {'x': 2.0, 'y': 0.0}],
        track_positions=[[0.0, 0.0, -3.0], [2.0, 0.0, -3.0]],
        follow_positions=[[0.0, 0.0, -3.0], [2.0, 0.0, -3.0]],
        position=[0.0, 0.0, 0.0], home=[0.0, 0.0, 0.0], landed=True,
        status={'arming_state': validation.VehicleStatus.ARMING_STATE_DISARMED},
        failsafe_observed=False, track_wall_time=90.0,
        follow_wall_time=100.0, follow_visible_wall_time=10.0,
        transitions=[], occlusions=[], relative_distances=[],
        elapsed=lambda: 120.0, accumulate_follow=lambda now: None,
        get_logger=lambda: SimpleNamespace(info=lambda text: None))
    validation.ValidationRecorder.finish(recorder)
    report = json.loads((tmp_path / 'report.json').read_text())
    assert report['track_detection_fraction'] == 1.0
    assert report['follow_time_visible_fraction'] == 0.1
    assert not report['passed']
    recorder.follow_visible_wall_time = recorder.follow_wall_time
    for index, position in enumerate(recorder.vehicle_positions):
        position['wall_s'] = 1.0 + index
    recorder.occlusions = [{'start_wall_s': 1.0, 'end_wall_s': 2.0,
                            'entry_locked': False, 'negative_observations': 1,
                            'recovery_s': 1.0, 'confirmed_recovery_s': 2.0}]
    validation.ValidationRecorder.finish(recorder)
    report = json.loads((tmp_path / 'report.json').read_text())
    assert report['follow_time_visible_fraction'] == 1.0
    assert not report['occlusion_recovery_passed'] and not report['passed']
    recorder.occlusions[0]['entry_locked'] = True
    validation.ValidationRecorder.finish(recorder)
    report = json.loads((tmp_path / 'report.json').read_text())
    assert report['occlusion_recovery_passed'] and report['passed']


@pytest.mark.parametrize('state,history,fresh,expected', [
    ('TRACK', [True, True, True], True, True),
    ('RECOVER', [True, True, True], True, False),
    ('TRACK', [False, True, True], True, False),
    ('TRACK', [True, True, True], False, False),
])
def test_occlusion_entry_requires_fresh_stable_lock(monkeypatch, state, history, fresh, expected):
    monkeypatch.setattr(validation.time, 'monotonic', lambda: 100.0)
    recorder = SimpleNamespace(state=state, target={'detected': True},
                               last_target_time=99.9 if fresh else 99.0,
                               confirmation_history=history, occlusions=[], elapsed=lambda: 10.0)
    validation.ValidationRecorder.occlusion_callback(
        recorder, SimpleNamespace(data=json.dumps({'active': True})))
    assert recorder.occlusions[0]['entry_locked'] == expected
    assert recorder.occlusions[0]['state_at_start'] == state


def test_offline_audit_cannot_call_recovery_before_occlusion_a_locked_entry(tmp_path):
    frames = [{'wall_s': t, 'vehicle_detected': True, 'identity_confirmed': True,
               'reason': 'confirmed', 'candidates': []} for t in [9.7, 9.8, 9.9]]
    (tmp_path / 'association.jsonl').write_text(''.join(json.dumps(f) + '\n' for f in frames))
    (tmp_path / 'samples.jsonl').write_text('')
    (tmp_path / 'report.json').write_text(json.dumps({
        'transitions': [{'time_s': 8.0, 'state': 'RECOVER'}],
        'occlusions': [{'start_wall_s': 10.0}], 'occlusion_recovery_passed': True}))
    audit = analysis.analyze(tmp_path)['occlusion_entry_audit'][0]
    assert audit['original_occlusion_recovery_passed']
    assert not audit['entry_locked_from_recorded_evidence']
