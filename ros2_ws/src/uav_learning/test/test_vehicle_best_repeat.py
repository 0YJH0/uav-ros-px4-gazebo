from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts'))
import repeat_best_vehicle as repeat


def test_selected_plan_preserves_scene_and_disables_unproven_controls():
    plan = repeat.make_plan(10)
    assert len(plan) == len({row['name'] for row in plan}) == 10
    assert all(row['overtaking'] and not row['crossing'] and row['gui'] for row in plan)
    assert all(row['vehicle_speed'] == .8 and row['occlusion_duration'] == 4 for row in plan)
    assert all(not row['recovery_competition_enabled'] and not row['smooth_recovery_setpoints']
               and row['predict_box_scale_velocity'] and row['detector_backend'] == 'torch' for row in plan)


def test_selected_plan_rejects_empty_batch():
    with pytest.raises(ValueError):
        repeat.make_plan(0)


def test_overtaking_failure_does_not_invent_missing_crossing_overlap(tmp_path, monkeypatch):
    report = {'occlusions': [{'start_wall_s': 10., 'end_wall_s': 14., 'entry_locked': False}],
              'events': [{'event': 'TRACK_TARGET_LOST', 'time_s': 11.},
                         {'event': 'TRACK_TARGET_LOST', 'time_s': 20.}]}
    identity = {'overtaking_observed': True, 'minimum_world_lateral_clearance_m': 1.45,
                'errors': ['crossing_pose_update_failed']}
    monkeypatch.setattr(repeat, 'completed_trial', lambda *args: {'success': False})
    monkeypatch.setattr(repeat, 'load_json', lambda path: {
        'report.json': report, 'identity_report.json': identity, 'supervisor.json': {}}[path.name])
    monkeypatch.setattr(repeat, 'failure_causes', lambda *args: [
        'insufficient_overlap_evidence', 'occlusion_entry_not_locked', 'crossing_pose_update_failed'])
    row = repeat.selected_row(tmp_path, {}, 1)
    assert row['outside_panel_losses'] == row['inside_panel_losses'] == 1
    assert row['criteria_failure_causes'] == ['occlusion_entry_not_locked', 'crossing_pose_update_failed']
    assert not row['success'] and row['scene_update_errors'] == 1


def test_missing_overtaking_evidence_is_a_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(repeat, 'completed_trial', lambda *args: {'success': False})
    monkeypatch.setattr(repeat, 'load_json', lambda *args: None)
    monkeypatch.setattr(repeat, 'failure_causes', lambda *args: ['missing_or_invalid_report'])
    row = repeat.selected_row(tmp_path, {}, 1)
    assert row['outside_panel_losses'] is None
    assert 'overtaking_not_observed' in row['criteria_failure_causes']
    assert 'overtaking_clearance_not_verified' in row['criteria_failure_causes']
