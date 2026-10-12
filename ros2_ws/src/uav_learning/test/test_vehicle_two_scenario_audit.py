import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def audit(monkeypatch):
    scripts = Path(__file__).resolve().parents[4] / 'scripts'
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location('two_scenario_audit_tests', scripts / 'audit_two_vehicle_scenarios.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_lines(path, rows):
    path.write_text(''.join(json.dumps(row) + '\n' for row in rows))


def receipts(client, numbers=(1, 2)):
    return [{'client': client, 'sequence': number, 'success': True,
             'binding_result': True, 'response_data': True} for number in numbers]


def test_native_receipts_require_complete_sequences_from_one(audit, tmp_path):
    write_lines(tmp_path / 'scene_service.jsonl', receipts('scene', (2, 3)))
    write_lines(tmp_path / 'traffic_service.jsonl', receipts('traffic'))
    result = audit.service_evidence(tmp_path)
    assert not result['passed']
    assert result['failures'] == 0
    assert result['client_sequences']['scene']['missing'] == [1]


@pytest.mark.parametrize('numbers', [(1, 1), (2, 1), (1, 3), (True,), ('1',)])
def test_duplicate_reordered_missing_invalid_sequences_fail(audit, tmp_path, numbers):
    write_lines(tmp_path / 'scene_service.jsonl', receipts('scene', numbers))
    write_lines(tmp_path / 'traffic_service.jsonl', receipts('traffic'))
    assert not audit.service_evidence(tmp_path)['passed']


def test_nominal_receipts_pass(audit, tmp_path):
    write_lines(tmp_path / 'scene_service.jsonl', receipts('scene'))
    write_lines(tmp_path / 'traffic_service.jsonl', receipts('traffic'))
    result = audit.service_evidence(tmp_path)
    assert result['passed'] and result['total'] == 4


@pytest.mark.parametrize('field', ['binding_result', 'response_data'])
def test_claimed_success_without_both_native_booleans_fails(audit, tmp_path, field):
    records = receipts('scene')
    records[0][field] = False
    write_lines(tmp_path / 'scene_service.jsonl', records)
    write_lines(tmp_path / 'traffic_service.jsonl', receipts('traffic'))
    result = audit.service_evidence(tmp_path)
    assert not result['passed'] and result['receipt_errors'] == 1


def test_missing_or_malformed_client_log_is_not_zero_errors(audit, tmp_path):
    write_lines(tmp_path / 'scene_service.jsonl', receipts('scene'))
    assert not audit.service_evidence(tmp_path)['passed']
    (tmp_path / 'traffic_service.jsonl').write_text('{broken\n')
    result = audit.service_evidence(tmp_path)
    assert not result['passed']
    assert result['files']['traffic_service.jsonl']['malformed_lines'] == [1]


def test_two_files_cannot_impersonate_one_client(audit, tmp_path):
    write_lines(tmp_path / 'scene_service.jsonl', receipts('scene'))
    write_lines(tmp_path / 'traffic_service.jsonl', receipts('scene', (3, 4)))
    assert not audit.service_evidence(tmp_path)['passed']


def test_fixed_left_geometry_does_not_require_lane_change_phases(audit):
    identity = {'traffic_started': True, 'traffic_completed': True,
                'overtaking_observed': True, 'minimum_world_lateral_clearance_m': .51}
    assert audit.scenario_evidence(identity, 'overtaking')[0]
    assert not audit.scenario_evidence(identity, 'lane_change_overtaking')[0]


def test_lane_change_uses_horizontal_phase_evidence_not_negative_lateral_clearance(audit):
    identity = {'traffic_started': True, 'traffic_completed': True,
                'minimum_world_lateral_clearance_m': -1.7,
                'lane_change': {'maneuver_observed': True}}
    assert audit.scenario_evidence(identity, 'lane_change_overtaking')[0]
    assert not audit.scenario_evidence(identity, 'overtaking')[0]


def test_fixed_left_requires_sufficient_clearance_and_complete_maneuver(audit):
    identity = {'traffic_started': True, 'traffic_completed': True,
                'overtaking_observed': True, 'minimum_world_lateral_clearance_m': .49}
    assert not audit.scenario_evidence(identity, 'overtaking')[0]
    identity['minimum_world_lateral_clearance_m'] = 1
    identity['traffic_completed'] = False
    assert not audit.scenario_evidence(identity, 'overtaking')[0]


def test_missing_recovery_is_censored_not_zero_or_later_episode(audit):
    report = {'wall_duration_s': 40., 'events': [
        {'time_s': 1., 'event': 'TRACK_TARGET_LOST'},
        {'time_s': 11., 'event': 'RECOVERY_TIMEOUT'},
        {'time_s': 15., 'event': 'TRACK_TARGET_LOST'},
        {'time_s': 17., 'event': 'TRACK_REACQUIRED'},
        {'time_s': 25., 'event': 'TRACK_TARGET_LOST'},
        {'time_s': 30., 'event': 'MISSION_DONE'},
        {'time_s': 35., 'event': 'TARGET_RECOVERED'},
    ]}
    episodes = audit.recovery_episodes(report)
    assert episodes[0]['censored'] and episodes[0]['recovery_timeout']
    assert episodes[0]['duration_s'] is None and episodes[0]['censor_lower_bound_s'] == 14
    assert episodes[1]['duration_s'] == 2
    assert episodes[2]['censored'] and episodes[2]['censor_lower_bound_s'] == 5


def test_temporal_panel_classification_does_not_require_entry_lock(audit):
    report = {'events': [{'time_s': 12, 'event': 'TRACK_TARGET_LOST'},
                         {'time_s': 16, 'event': 'TRACK_REACQUIRED'}],
              'occlusions': [{'start_wall_s': 10, 'end_wall_s': 14, 'entry_locked': False}]}
    assert audit.recovery_episodes(report)[0]['planned_occlusion']


def test_sample_statistics_missing_not_zero_and_worst_direction(audit):
    result = audit.distribution([None, 1, 3, float('nan')], worst='min')
    assert result['count'] == 2 and result['mean'] == 2
    assert result['sample_std'] == pytest.approx(2 ** .5)
    assert result['worst'] == 1 and result['max'] == 3
    assert audit.distribution([1])['sample_std'] is None
    assert audit.distribution([])['mean'] is None


def test_failed_attempts_in_success_denominator_unlaunched_separate(audit):
    plan = [{'name': str(index)} for index in range(10)]
    rows = [{'attempted': True, 'completed': True, 'task_passed': True,
             'identity_verified': True, 'strict_joint_passed': True, 'coverage_percent': 90},
            {'attempted': True, 'completed': False, 'task_passed': False,
             'identity_verified': False, 'strict_joint_passed': False, 'coverage_percent': None}]
    result = audit.group_summary(plan, rows)
    assert result['attempted'] == 2 and result['not_launched'] == 8
    assert result['strict_success_rate'] == .5
    assert result['metrics']['coverage_percent']['count'] == 1
    assert result['metrics']['strict_joint_passed']['sample_std'] == pytest.approx(.5 ** .5)


def test_censored_episodes_not_omitted_from_group(audit):
    episode = {'planned_occlusion': False, 'censored': True,
               'recovery_timeout': True, 'duration_s': None, 'censor_lower_bound_s': 18}
    result = audit.group_summary([{}], [{'attempted': True, 'recovery_episodes': [episode]}])
    pooled = result['pooled_unplanned_recovery']
    assert pooled['count'] == 0 and pooled['mean'] is None
    assert pooled['censored_episodes'] == pooled['timeout_episodes'] == 1
    assert pooled['censor_lower_bounds_s'] == [18]


def test_runtime_px4_calibration_not_mislabeled_as_frozen_control_change(audit):
    result = audit.parameter_differences(
        {'COM_FLIGHT_UUID': 1, 'CAL_GYRO0_XOFF': .1, 'MPC_XY_P': .9},
        {'COM_FLIGHT_UUID': 2, 'CAL_GYRO0_XOFF': .2, 'MPC_XY_P': 1.})
    assert set(result['bookkeeping_differences']) == {'COM_FLIGHT_UUID'}
    assert set(result['calibration_differences']) == {'CAL_GYRO0_XOFF'}
    assert set(result['other_parameter_differences']) == {'MPC_XY_P'}


def test_batch_summary_keeps_unlaunched_and_started_without_audit(audit, tmp_path, monkeypatch):
    monkeypatch.setattr(audit, 'plot_summary', lambda *args: False)
    plan = [{'name': name, 'group': 'left_overtaking', 'traffic_scenario': 'overtaking'}
            for name in ('left_01', 'left_02')]
    audit.write_json(tmp_path / 'plan.json', plan)
    audit.write_json(tmp_path / 'attempts/left_01.json', {'state': 'started'})
    result = audit.summarize_batch(tmp_path)
    assert result['attempted'] == 1 and not result['batch_complete']
    assert result['trials'][0]['failure_reasons'] == ['audit_not_available', 'attempt_not_completed:started']
    assert result['trials'][1]['attempt_state'] == 'not_launched'
    assert (tmp_path / 'FINAL_REPORT.md').is_file()


def test_interrupted_attempt_cannot_inherit_passed_audit(audit, tmp_path, monkeypatch):
    monkeypatch.setattr(audit, 'plot_summary', lambda *args: False)
    audit.write_json(tmp_path / 'plan.json', [{'name': 'run', 'group': 'lane_change',
                                              'traffic_scenario': 'lane_change_overtaking'}])
    audit.write_json(tmp_path / 'attempts/run.json', {'state': 'interrupted', 'returncode': 0})
    audit.write_json(tmp_path / 'run/batch_audit.json', {'name': 'run', 'group': 'lane_change',
        'attempted': True, 'completed': True, 'strict_joint_passed': True, 'failure_reasons': []})
    result = audit.summarize_batch(tmp_path)
    assert not result['trials'][0]['strict_joint_passed']
    assert result['groups']['lane_change']['completed'] == 0


def test_nonzero_supervisor_exit_remains_failed(audit, tmp_path):
    audit.write_json(tmp_path / 'attempts/run.json', {'state': 'completed', 'returncode': 1})
    result = audit.audit_trial(tmp_path, tmp_path / 'run', {'traffic_scenario': 'overtaking'})
    assert 'supervisor_exit_not_zero:1' in result['failure_reasons']


def test_null_or_wrong_json_container_falls_back(audit, tmp_path):
    path = tmp_path / 'value.json'
    path.write_text('null')
    assert audit.read_json(path, {}) == {}
    path.write_text('[]')
    assert audit.read_json(path, {}) == {}


def test_missing_trial_fails_closed_not_safe(audit, tmp_path):
    trial = tmp_path / 'trial'
    result = audit.audit_trial(tmp_path, trial, {'traffic_scenario': 'overtaking'})
    assert not result['strict_joint_passed'] and not result['safe_to_continue']
    assert result['ulog_safety'] is None and result['safety_event_observations'] is None
    assert result['coverage_percent'] is None and result['scene_request_failures'] is None
    assert 'missing_or_invalid_report' in result['failure_reasons']
    assert 'ulog_safety_evidence_missing' in result['failure_reasons']


def test_immutable_archive_hash_mismatch_is_integrity_failure(audit, tmp_path):
    trial = tmp_path / 'trial'
    trial.mkdir()
    model = tmp_path / 'model.pt'
    model.write_bytes(b'model')
    audit.write_json(trial / 'implementation_snapshot.json', {
        'source_sha256': {'source.py': 'wrong'}, 'model_path': str(model),
        'model_sha256': audit.digest(model), 'scenario': {'traffic_scenario': 'overtaking'}})
    (trial / 'executed_sources').mkdir()
    (trial / 'executed_sources/source.py').write_text('actual')
    result = audit.integrity_evidence(tmp_path, trial, {'traffic_scenario': 'overtaking'}, None)
    assert not result['passed']
    assert 'source_archive_mismatch:source.py' in result['errors']


@pytest.mark.parametrize('mutation', ['artifact', 'missing_ir', 'interpreter'])
def test_openvino_requires_exact_frozen_artifacts_and_tested_interpreter(audit, tmp_path, mutation):
    trial, artifacts = tmp_path / 'trial', tmp_path / 'ir'
    trial.mkdir()
    artifacts.mkdir()
    model = tmp_path / 'model.pt'
    model.write_bytes(b'model')
    (tmp_path / 'source.py').write_text('source')
    for size in (960, 640):
        for suffix in ('xml', 'bin'):
            (artifacts / f'detector_{size}.{suffix}').write_text('runtime')
    audit.write_json(artifacts / 'manifest.json', {'precision': 'FP32', 'weight_sha256': audit.digest(model)})
    hashes = {path.name: audit.digest(path) for path in artifacts.iterdir()}
    sources = {'source.py': audit.digest(tmp_path / 'source.py'), 'model.pt': audit.digest(model)}
    sources.update({'ir/' + key: value for key, value in hashes.items()})
    for relative in sources:
        archive = tmp_path / 'frozen_files' / relative
        archive.parent.mkdir(parents=True, exist_ok=True)
        archive.write_bytes((tmp_path / relative).read_bytes())
    scenario = {'traffic_scenario': 'overtaking', 'detector_backend': 'openvino',
                'backend_artifacts': str(artifacts)}
    snapshot = {'source_sha256': {'source.py': sources['source.py']},
                'model_path': str(model), 'model_sha256': audit.digest(model),
                'backend_artifact_sha256': hashes, 'scenario': scenario}
    audit.write_json(tmp_path / 'freeze_manifest.json', {'source_sha256': sources, 'model_path': str(model)})
    audit.write_json(tmp_path / 'batch_protocol.json', {'backend_runtime': {'interpreter': '/tested/python'}})
    audit.write_json(trial / 'supervisor.json', {'perception_python': '/tested/python'})
    audit.write_json(trial / 'runtime_parameters.json', {
        'perception_node': {'model_path': str(model), 'overlap_candidate_recovery': True,
                           'bounded_scale_prediction': True, 'overlap_confirmation_continuity': True,
                           'target_reacquire_timeout': 10.},
        'px4_offboard_controller': {'recovery_timeout': 10., 'recovery_max_distance': 4., 'recovery_max_speed': .8},
        'vehicle_scene': {'traffic_scenario': 'overtaking', 'distractor_color': 'red',
                          'parked_vehicle_y': -4.4, 'vehicle_speed': .8,
                          'occlusion_start': 15., 'occlusion_duration': 4.}})
    audit.write_json(trial / 'implementation_snapshot.json', snapshot)
    assert audit.integrity_evidence(tmp_path, trial, scenario, None)['passed']
    if mutation == 'artifact':
        (artifacts / 'detector_640.bin').write_text('changed')
    elif mutation == 'missing_ir':
        snapshot['backend_artifact_sha256'].pop('detector_640.bin')
        audit.write_json(trial / 'implementation_snapshot.json', snapshot)
    else:
        audit.write_json(trial / 'supervisor.json', {'perception_python': '/other/python'})
    assert not audit.integrity_evidence(tmp_path, trial, scenario, None)['passed']
