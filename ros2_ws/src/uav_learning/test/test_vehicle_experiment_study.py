import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    'vehicle_study', Path(__file__).resolve().parents[4] / 'scripts/vehicle_experiment_study.py')
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)


def test_frozen_parameters_match_baseline_and_keep_ten_second_limit():
    expected = study.declared_parameters(study.ROOT)
    assert expected['px4_offboard_controller']['recovery_timeout'] == 10.0
    assert expected['perception_node']['confidence_threshold'] == 0.25
    captured = {node: dict(values) for node, values in expected.items()}
    captured['vehicle_scene']['occlusion_enabled'] = True
    scene = {'vehicle_speed': 0.8, 'occlusion_start': 15.0, 'occlusion_duration': 4.0}
    study.verify_parameters(captured, scene, expected)
    captured['px4_offboard_controller']['recovery_timeout'] = 12.0
    with pytest.raises(RuntimeError, match='blind_motion_budget'):
        study.verify_parameters(captured, scene, expected)


def test_group_changes_only_scene_parameters():
    expected = study.declared_parameters(study.ROOT)
    captured = {node: dict(values) for node, values in expected.items()}
    captured['vehicle_scene']['occlusion_enabled'] = True
    scenario = {'vehicle_speed': 1.6, 'occlusion_start': 15.0, 'occlusion_duration': 6.0}
    captured['vehicle_scene'].update(scenario)
    study.verify_parameters(captured, scenario, expected)
    captured['perception_node']['confidence_threshold'] = 0.1
    with pytest.raises(RuntimeError, match='confidence_threshold'):
        study.verify_parameters(captured, scenario, expected)


def test_freeze_drift_is_rejected(tmp_path):
    source = tmp_path / 'source.py'
    source.write_text('original')
    manifest = tmp_path / 'freeze.json'
    manifest.write_text(json.dumps({'source_sha256': {'source.py': study.digest(source)},
                                   'package_versions': {}}))
    study.verify_freeze(tmp_path, manifest)
    source.write_text('changed')
    with pytest.raises(RuntimeError, match='source.py'):
        study.verify_freeze(tmp_path, manifest)


def test_failed_attempt_stays_in_success_denominator_and_metric_summary():
    rows = [{'name': 'one', 'success': True, 'visibility': 0.9, 'safety_event': False, 'interventions': 0},
            {'name': 'two', 'success': False, 'visibility': 0.3, 'safety_event': True, 'interventions': 1},
            {'name': 'three', 'success': False, 'visibility': None, 'safety_event': True, 'interventions': 0}]
    report = study.summarize(rows, 10)
    assert report['attempted'] == 3 and report['not_attempted'] == 7
    assert report['success_rate'] == 1/3 and report['failures'] == 2
    metric = report['metrics']['visibility']
    assert metric['n'] == 2 and metric['missing'] == 1
    assert metric['mean'] == 0.6 and metric['worst_trials'] == ['two']
    assert report['safety_event_trials'] == 2


def test_planned_occlusion_excludes_only_one_loss_not_all_nearby_losses():
    events = [{'event': 'TRACK_TARGET_LOST', 'time_s': 8},
              {'event': 'TRACK_TARGET_LOST', 'time_s': 11},
              {'event': 'TARGET_RECOVERED', 'time_s': 12},
              {'event': 'TRACK_TARGET_LOST', 'time_s': 13},
              {'event': 'TRACK_REACQUIRED', 'time_s': 21}]
    occlusions = [{'start_wall_s': 10, 'end_wall_s': 14, 'entry_locked': True}]
    total, planned, unplanned, recoveries = study.loss_counts(events, occlusions)
    assert (total, planned, unplanned) == (3, 1, 2)
    assert recoveries == [4, 8]
    occlusions[0]['entry_locked'] = False
    assert study.loss_counts(events, occlusions)[:3] == (3, 0, 3)


def test_missing_report_is_failed_not_silently_removed(tmp_path):
    trial = {'name': 'broken', 'group': 'baseline'}
    row = study.trial_row(tmp_path, trial)
    assert not row['success'] and row['visibility'] is None
    assert 'missing_or_invalid_report' in row['failure_reasons']


def test_blind_audit_ends_at_timeout_not_later_visual_reacquisition():
    events = [{'event': 'TRACK_OBSERVATION_GAP', 'time_s': 0},
              {'event': 'RECOVERY_TIMEOUT', 'time_s': 10},
              {'event': 'TRACK_REACQUIRED', 'time_s': 20}]
    sample = {'wall_s': 1, 'state': 'RECOVER', 'position_ned': [0, 0, -3],
              'setpoint': {'position_ned': [2, 0, -3]}}
    duration, distance = study.blind_audit([sample], events)
    assert duration == 10 and distance == 2


def test_plan_runs_baseline_before_stress_groups():
    plan = study.make_plan(True)
    assert len(plan) == 30
    assert all(trial['group'] == 'baseline' for trial in plan[:10])
    assert len({trial['name'] for trial in plan}) == len(plan)


def test_new_freeze_excludes_generated_test_caches_but_keeps_implementation(tmp_path, monkeypatch):
    root, output = tmp_path / 'root', tmp_path / 'study'
    output.mkdir()
    paths = ['ros2_ws/src/uav_learning/uav_learning/source.py',
             'ros2_ws/src/uav_learning/.pytest_cache/v/cache/nodeids',
             'ros2_ws/src/uav_learning/.ruff_cache/cache',
             'PX4-Autopilot/build/px4_sitl_default/bin/px4', 'model.pt']
    paths += ['scripts/' + name for name in ('run_vehicle_tracking_validation.py',
        'validate_vehicle_tracking.py', 'vehicle_experiment_study.py', 'px4_env.sh',
        'analyze_vehicle_association.py', 'vehicle_crossing_validation.py')]
    for name in paths:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('test')
    monkeypatch.setattr(study, 'declared_parameters', lambda root: {})
    monkeypatch.setattr(study.importlib.metadata, 'version', lambda name: 'test')
    manifest = study.freeze(root, output, root / 'model.pt')
    assert 'ros2_ws/src/uav_learning/uav_learning/source.py' in manifest['source_sha256']
    assert not any('.pytest_cache' in name or '.ruff_cache' in name for name in manifest['source_sha256'])


def test_pilot_is_three_independent_development_checks_not_a_repeated_study():
    plan = study.make_pilot_plan()
    assert len(plan) == 3 and [row['vehicle_speed'] for row in plan] == [0.8, 1.6, 0.8]
    assert [row['crossing'] for row in plan] == [False, False, True]
    assert all('pilot' in row['name'] for row in plan)
