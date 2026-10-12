"""The repeat harness must preserve every attempt and the selected flight protocol."""

import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[4] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import repeat_two_vehicle_scenarios as repeat


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def reference_fixture(tmp_path):
    root, reference = tmp_path / 'root', tmp_path / 'reference'
    root.mkdir()
    model, code = root / 'yolo11s.pt', root / 'perception.py'
    model.write_bytes(b'local-model')
    code.write_text('frozen code')
    snapshot = {
        'source_sha256': {'perception.py': repeat.digest(code)},
        'model_path': str(model), 'model_sha256': repeat.digest(model),
        'scenario': repeat.make_plan(1, True)[1]}
    parameters = {
        'perception_node': {'overlap_candidate_recovery': True,
                            'bounded_scale_prediction': True,
                            'overlap_confirmation_continuity': True},
        'px4_offboard_controller': {'recovery_timeout': 10.}}
    write(reference / 'implementation_snapshot.json', snapshot)
    write(reference / 'runtime_parameters.json', parameters)
    return root, reference, snapshot, parameters


def test_plan_has_twenty_distinct_alternating_attempts():
    plan = repeat.make_plan()
    assert len(plan) == len({row['name'] for row in plan}) == 20
    assert [row['name'] for row in plan[:4]] == [
        'left_overtaking_01', 'lane_change_01', 'left_overtaking_02', 'lane_change_02']
    assert sum(row['overtaking'] for row in plan) == 10
    assert sum(row['lane_change_overtaking'] for row in plan) == 10
    for row in plan:
        assert row['distractor_color'] == 'red'
        assert row['parked_vehicle_y'] == -4.4
        assert row['vehicle_speed'] == .8
        assert row['occlusion_start'] == 15.
        assert row['occlusion_duration'] == 4.
        assert row['overlap_confirmation_continuity'] is True
        assert row['recovery_competition_enabled'] is False
        assert row['gui'] is False


@pytest.mark.parametrize('count', [0, -1])
def test_reject_empty_plan(count):
    with pytest.raises(ValueError):
        repeat.make_plan(count)


@pytest.mark.parametrize('index,flag', [(0, '--overtaking'), (1, '--lane-change-overtaking')])
def test_command_selects_exact_scene_and_runtime(tmp_path, index, flag):
    command = repeat.command_for(tmp_path, tmp_path / 'batch', repeat.make_plan(1)[index], '/model.pt')
    assert flag in command
    assert command[command.index('--distractor-color') + 1] == 'red'
    assert command[command.index('--parked-y') + 1] == '-4.4'
    assert command[command.index('--detector-backend') + 1] == 'torch'
    assert command[command.index('--model-path') + 1] == '/model.pt'
    assert '--gui' not in command
    assert '--no-overlap-confirmation-continuity' not in command
    assert '--hold-box-scale' not in command
    assert '--recovery-competition' not in command


def test_gui_protocol_explicit_and_identical_for_both_scenes(tmp_path):
    for trial in repeat.make_plan(1, gui=True):
        command = repeat.command_for(tmp_path, tmp_path / 'batch', trial, '/model.pt')
        assert '--gui' in command and '--gui-config' in command


def test_openvino_plan_and_command_include_real_runtime(tmp_path):
    artifacts = str(tmp_path / 'ir')
    python = tmp_path / '.venv-backend/bin/python'
    plan = repeat.make_plan(10, detector_backend='openvino', backend_artifacts=artifacts)
    assert len(plan) == 20
    for trial in plan:
        assert trial['detector_backend'] == 'openvino'
        assert trial['backend_artifacts'] == artifacts
        command = repeat.command_for(tmp_path, tmp_path / 'batch', trial, '/model.pt', python)
        assert command[command.index('--backend-artifacts') + 1] == artifacts
        assert command[command.index('--perception-python') + 1] == str(python)


def test_openvino_reference_is_checked_against_selected_backend(tmp_path):
    root, reference, snapshot, parameters = reference_fixture(tmp_path)
    plan = repeat.make_plan(1, detector_backend='openvino', backend_artifacts='/ir')
    snapshot['scenario'].update(detector_backend='openvino', backend_artifacts='/ir')
    write(reference / 'implementation_snapshot.json', snapshot)
    assert repeat.verify_reference(root, reference, plan) == (snapshot, parameters)
    plan[0]['backend_artifacts'] = '/other-ir'
    with pytest.raises(RuntimeError, match='Reference scenario differs'):
        repeat.verify_reference(root, reference, plan)


@pytest.mark.parametrize('strict,safe', [(False, True), (True, False)])
def test_failed_or_unsafe_pilot_cannot_promote(monkeypatch, tmp_path, strict, safe):
    reference = tmp_path / 'lane_change_pilot'
    write(tmp_path / 'plan.json', [{'name': reference.name, 'detector_backend': 'openvino'}])
    monkeypatch.setattr(repeat, 'verify_freeze', lambda *args: None)
    monkeypatch.setitem(sys.modules, 'audit_two_vehicle_scenarios', SimpleNamespace(
        audit_trial=lambda *a: {'strict_joint_passed': strict, 'safe_to_continue': safe}))
    with pytest.raises(RuntimeError, match='did not pass strict'):
        repeat.verify_openvino_pilot(tmp_path, reference)


def test_reference_can_differ_only_by_scene_and_gui(tmp_path):
    root, reference, snapshot, parameters = reference_fixture(tmp_path)
    assert repeat.verify_reference(root, reference) == (snapshot, parameters)


@pytest.mark.parametrize('key,value', [('vehicle_speed', 1.), ('distractor_color', 'blue'),
                                      ('overlap_confirmation_continuity', False),
                                      ('detector_backend', 'openvino')])
def test_reference_parameter_drift_rejected(tmp_path, key, value):
    root, reference, snapshot, _ = reference_fixture(tmp_path)
    snapshot['scenario'][key] = value
    write(reference / 'implementation_snapshot.json', snapshot)
    with pytest.raises(RuntimeError, match='Reference scenario differs'):
        repeat.verify_reference(root, reference)


@pytest.mark.parametrize('key', ['overlap_candidate_recovery', 'bounded_scale_prediction',
                                 'overlap_confirmation_continuity'])
def test_all_selected_fixes_required(tmp_path, key):
    root, reference, _, parameters = reference_fixture(tmp_path)
    parameters['perception_node'][key] = False
    write(reference / 'runtime_parameters.json', parameters)
    with pytest.raises(RuntimeError, match='Required reference improvement'):
        repeat.verify_reference(root, reference)


def test_blind_limit_cannot_be_extended(tmp_path):
    root, reference, _, parameters = reference_fixture(tmp_path)
    parameters['px4_offboard_controller']['recovery_timeout'] = 15.
    write(reference / 'runtime_parameters.json', parameters)
    with pytest.raises(RuntimeError, match='10 second'):
        repeat.verify_reference(root, reference)


@pytest.mark.parametrize('filename', ['perception.py', 'yolo11s.pt'])
def test_reference_code_or_model_drift_rejected(tmp_path, filename):
    root, reference, _, _ = reference_fixture(tmp_path)
    (root / filename).write_text('changed')
    with pytest.raises(RuntimeError, match='implementation differs'):
        repeat.verify_reference(root, reference)


def test_resume_preserves_completed_failed_and_started_attempts(tmp_path):
    plan = repeat.make_plan(2)
    for row, state in zip(plan, ('completed', 'interrupted', 'started')):
        write(tmp_path / 'attempts' / (row['name'] + '.json'), {
            'name': row['name'], 'state': state, 'returncode': 1})
    found = repeat.existing_attempts(tmp_path, plan)
    assert set(found) == {row['name'] for row in plan[:3]}
    assert [row['name'] for row in plan if row['name'] not in found] == ['lane_change_02']


def test_unledgered_existing_trial_not_silently_replaced(tmp_path):
    plan = repeat.make_plan(1)
    (tmp_path / plan[0]['name']).mkdir()
    with pytest.raises(RuntimeError, match='without attempt ledger'):
        repeat.existing_attempts(tmp_path, plan)


def test_unknown_or_corrupted_attempt_rejected(tmp_path):
    write(tmp_path / 'attempts' / 'other.json', {'name': 'other'})
    with pytest.raises(RuntimeError, match='Invalid attempt ledger'):
        repeat.existing_attempts(tmp_path, repeat.make_plan(1))


def test_process_check_fails_closed(monkeypatch):
    class Result:
        returncode = 2
    monkeypatch.setattr(repeat.subprocess, 'run', lambda *a, **kw: Result())
    with pytest.raises(RuntimeError, match='Cannot inspect'):
        repeat.assert_no_simulation()


def test_live_simulation_blocks_launch(monkeypatch):
    class Result:
        returncode = 0
    monkeypatch.setattr(repeat.subprocess, 'run', lambda *a, **kw: Result())
    with pytest.raises(RuntimeError, match='Existing simulation'):
        repeat.assert_no_simulation()


def test_archive_retains_source_and_fails_on_changed_ulog(tmp_path):
    trial = repeat.make_plan(1)[0]
    target = tmp_path / trial['name']
    target.mkdir()
    (tmp_path / 'frozen_files').mkdir()
    rootfs = tmp_path / 'rootfs'
    source = rootfs / 'log/2026-10-11/00_00_00.ulg'
    source.parent.mkdir(parents=True)
    source.write_bytes(b'original-flight')
    (target / 'px4.log').write_text('Opened full log file: ./log/2026-10-11/00_00_00.ulg\n')
    snapshot = {'source_sha256': {'file.py': 'sha'}, 'model_sha256': 'model'}
    write(target / 'implementation_snapshot.json', snapshot)
    write(tmp_path / 'freeze_manifest.json', {'source_sha256': {'file.py': 'sha'}})
    protocol = {'px4_rootfs': str(rootfs), 'model_sha256': 'model'}
    repeat.archive_trial(tmp_path, trial, protocol)
    assert (target / 'executed_sources').resolve() == tmp_path / 'frozen_files'
    assert (target / 'flight.ulg').read_bytes() == b'original-flight'
    source.write_bytes(b'changed-flight')
    with pytest.raises(RuntimeError, match='refusing overwrite'):
        repeat.archive_trial(tmp_path, trial, protocol)
    assert (target / 'flight.ulg').read_bytes() == b'original-flight'


def test_archive_must_match_frozen_source(tmp_path):
    trial = repeat.make_plan(1)[0]
    write(tmp_path / trial['name'] / 'implementation_snapshot.json', {
        'source_sha256': {'file.py': 'new'}, 'model_sha256': 'model'})
    write(tmp_path / 'freeze_manifest.json', {'source_sha256': {'file.py': 'old'}})
    with pytest.raises(RuntimeError, match='Executed source/model differs'):
        repeat.archive_trial(tmp_path, trial, {'model_sha256': 'model'})


def mock_batch(monkeypatch, tmp_path, safe=True, resume=False):
    directory, reference = tmp_path / 'batch', tmp_path / 'reference'
    plan = repeat.make_plan(1)
    protocol = {'reference': str(reference), 'model_path': '/model.pt'}

    def prepare(directory, reference, count, gui):
        (directory / 'attempts').mkdir(parents=True)
        write(directory / 'plan.json', plan)
        write(directory / 'freeze_manifest.json', {'source_sha256': {}})

    if resume:
        prepare(directory, reference, 1, False)
    monkeypatch.setattr(repeat, 'prepare', prepare)
    monkeypatch.setattr(repeat, 'verify', lambda directory: protocol)
    monkeypatch.setattr(repeat, 'assert_no_simulation', lambda: None)
    monkeypatch.setattr(repeat, 'archive_trial', lambda *a: None)
    monkeypatch.setattr(repeat.time, 'sleep', lambda _: None)
    monkeypatch.setattr(repeat.signal, 'signal', lambda *a: None)
    launched = []

    class Process:
        def __init__(self, command, **kwargs):
            launched.append(command)
            self.returncode = 1 if len(launched) == 1 else 0

        def poll(self):
            return self.returncode

    monkeypatch.setattr(repeat.subprocess, 'Popen', Process)
    monkeypatch.setitem(sys.modules, 'audit_two_vehicle_scenarios', SimpleNamespace(
        audit_trial=lambda *a: {'safe_to_continue': safe}, summarize_batch=lambda *a: {}))
    monkeypatch.setattr(sys, 'argv', ['repeat', '--reference', str(reference),
                                    '--output', str(directory), '--count', '1']
                       + (['--resume'] if resume else []))
    return directory, plan, launched


def test_ordinary_failure_is_retained_and_next_scene_runs(monkeypatch, tmp_path):
    directory, plan, launched = mock_batch(monkeypatch, tmp_path)
    assert repeat.main() == 0
    attempts = repeat.existing_attempts(directory, plan)
    assert len(launched) == len(attempts) == 2
    assert attempts[plan[0]['name']]['returncode'] == 1
    assert attempts[plan[1]['name']]['returncode'] == 0
    assert repeat.load_json(directory / 'study_status.json')['completed'] is True


def test_safety_stop_never_launches_second_scene(monkeypatch, tmp_path):
    directory, plan, launched = mock_batch(monkeypatch, tmp_path, safe=False)
    assert repeat.main() == 2
    assert len(launched) == 1
    assert len(repeat.existing_attempts(directory, plan)) == 1
    assert repeat.load_json(directory / 'study_status.json')['completed'] is False


def test_resume_only_launches_unattempted_scenario(monkeypatch, tmp_path):
    directory, plan, launched = mock_batch(monkeypatch, tmp_path, resume=True)
    write(directory / 'attempts' / (plan[0]['name'] + '.json'), {
        'name': plan[0]['name'], 'state': 'started'})
    assert repeat.main() == 2
    attempts = repeat.existing_attempts(directory, plan)
    assert len(launched) == 1
    assert attempts[plan[0]['name']]['state'] == 'interrupted'
    assert attempts[plan[0]['name']]['returncode'] is None
    assert attempts[plan[1]['name']]['state'] == 'completed'
    assert repeat.load_json(directory / 'study_status.json')['completed'] is False
