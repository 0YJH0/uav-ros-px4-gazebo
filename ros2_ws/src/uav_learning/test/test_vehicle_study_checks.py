import importlib.util
from pathlib import Path
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[4] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('study_checks_tests', SCRIPTS / 'vehicle_study_checks.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def valid_report():
    return {'completed': True, 'track_complete_event': True, 'landed': True,
            'disarmed': True, 'passed': True, 'failsafe_observed': False,
            'follow_time_visible_fraction': 0.85, 'track_detection_fraction': 0.9,
            'vehicle_travel_m': 20., 'drone_track_travel_m': 15.,
            'final_home_horizontal_error_m': 0.5, 'occlusions': [],
            'occlusion_recovery_passed': True}


def test_failure_causes_do_not_conflate_missing_identity_with_wrong_car():
    causes = checks.failure_causes(valid_report(), None)
    assert causes == ['missing_or_invalid_identity_report']


def test_missing_report_is_not_success():
    causes = checks.failure_causes(None, None)
    assert 'missing_or_invalid_report' in causes
    assert 'missing_or_invalid_identity_report' in causes


def test_zero_wrong_car_without_overlap_is_not_verified_identity():
    identity = {'identity_independently_verified': False, 'overlap_observations': 0,
                'phase_counts': {'pre': {'tracked_vehicle': 20}, 'post': {'tracked_vehicle': 20}},
                'matched_truth_fraction': 1., 'wrong_identity_observations': 0, 'errors': []}
    assert checks.failure_causes(valid_report(), identity) == ['insufficient_overlap_evidence']


def test_failsafe_and_unlocked_occlusion_are_both_reported():
    report = {**valid_report(), 'passed': False, 'failsafe_observed': True,
              'occlusions': [{'entry_locked': False}], 'occlusion_recovery_passed': False}
    assert checks.failure_causes(report, {'identity_independently_verified': True}) == [
        'px4_failsafe_observed', 'occlusion_entry_not_locked']


@pytest.fixture
def study(tmp_path):
    runtime = tmp_path / 'runtime'
    source_name = 'ros2_ws/src/uav_learning/uav_learning/node.py'
    source = runtime / source_name
    installed = runtime / 'ros2_ws/install/uav_learning/lib/python3.12/site-packages/uav_learning/node.py'
    for path in (source, installed):
        path.parent.mkdir(parents=True)
        path.write_text('unchanged')
    model = runtime / 'yolo11s.pt'
    model.write_bytes(b'model')
    manifest = {'source_sha256': {source_name: checks.digest(source), 'yolo11s.pt': checks.digest(model)}}
    checks.write_json(tmp_path / 'freeze_manifest.json', manifest)
    checks.write_json(tmp_path / 'repeat_provenance.json', {'runtime': str(runtime)})
    plan = [{'name': 'crossing_01'}]
    checks.write_json(tmp_path / 'plan.json', plan)
    checks.write_json(tmp_path / 'study_status.json', {'attempted': 1, 'planned': 1, 'completed': True})
    trial = tmp_path / 'crossing_01'
    trial.mkdir()
    checks.write_json(trial / 'report.json', valid_report())
    checks.write_json(trial / 'identity_report.json', {'identity_independently_verified': True})
    checks.write_json(trial / 'supervisor.json', {
        'autonomous_passed': True, 'freeze_verified': True, 'parameters_verified': True})
    checks.write_json(trial / 'runtime_parameters.json', {})
    checks.write_json(trial / 'implementation_snapshot.json', {
        'source_sha256': {source_name: checks.digest(source)}, 'model_sha256': checks.digest(model)})
    (trial / 'flight.ulg').write_bytes(b'log')
    checks.write_json(tmp_path / 'px4_parameter_audit.json', {'trials': [{
        'directory': str(trial), 'available': True, 'ulog_sha256': checks.digest(trial / 'flight.ulg')}]})
    (tmp_path / 'crossing_01_supervisor.log').write_text('Started px4: PID 123\n')
    checks.write_json(tmp_path / 'study_summary.json', {
        'trials': [{'name': 'crossing_01', 'directory': str(trial), 'success': True}]})
    return tmp_path


def test_valid_complete_study_has_no_integrity_errors(study):
    result = checks.inspect_study(study)
    assert result['evidence_complete'] and result['all_attempts_finished']
    assert result['strict_passes'] == result['unique_px4_starts'] == 1


def test_failed_flight_with_complete_evidence_is_not_integrity_failure(study):
    report = {**valid_report(), 'passed': False, 'follow_time_visible_fraction': 0.7}
    checks.write_json(study / 'crossing_01/report.json', report)
    checks.write_json(study / 'crossing_01/supervisor.json', {
        'autonomous_passed': False, 'freeze_verified': True, 'parameters_verified': True})
    summary = checks.load_json(study / 'study_summary.json')
    summary['trials'][0]['success'] = False
    checks.write_json(study / 'study_summary.json', summary)
    result = checks.inspect_study(study)
    assert result['evidence_complete'] and result['strict_passes'] == 0
    assert result['failure_counts']['confirmed_coverage_below_0_8'] == 1


@pytest.mark.parametrize('name,error', [
    ('crossing_01/flight.ulg', 'ulog_missing_or_hash_mismatch'),
    ('runtime/ros2_ws/src/uav_learning/uav_learning/node.py', 'frozen_source_mismatch'),
    ('runtime/ros2_ws/install/uav_learning/lib/python3.12/site-packages/uav_learning/node.py',
     'installed_module_mismatch'),
])
def test_corrupt_evidence_cannot_pass(study, name, error):
    (study / name).write_bytes(b'changed')
    result = checks.inspect_study(study)
    assert not result['evidence_complete']
    assert any(row.startswith(error) for row in result['integrity_errors'])


def test_incomplete_batch_stays_explicitly_incomplete(study):
    checks.write_json(study / 'study_status.json', {'attempted': 1, 'planned': 1, 'completed': False})
    result = checks.inspect_study(study)
    assert not result['all_attempts_finished'] and not result['evidence_complete']
    assert 'batch_incomplete' in result['integrity_errors']
    assert result['attempt_evidence_complete']


def test_stopped_ab_study_checks_frozen_files_and_postrun_installed_archive(study):
    import shutil
    shutil.copytree(study / 'runtime', study / 'frozen_files')
    shutil.copytree(study / 'runtime/ros2_ws/install/uav_learning/lib/python3.12/site-packages/uav_learning',
                    study / 'installed_snapshot')
    helper = study / 'reporting_helpers/runner.py'
    helper.parent.mkdir()
    helper.write_text('executed version')
    checks.write_json(study / 'ab_protocol.json', {'helper_sha256': {'runner.py': checks.digest(helper)}})
    checks.write_json(study / 'study_status.json', {'attempted': 1, 'planned': 1, 'completed': False,
                                                  'error': 'safety_stop'})
    result = checks.inspect_study(study)
    assert result['integrity_errors'] == ['batch_incomplete']
    assert result['attempt_evidence_complete'] and not result['evidence_complete']
    helper.write_text('changed')
    assert not checks.inspect_study(study)['attempt_evidence_complete']


def test_success_count_disagreement_is_rejected(study):
    summary = checks.load_json(study / 'study_summary.json')
    summary['trials'][0]['success'] = False
    checks.write_json(study / 'study_summary.json', summary)
    assert 'summary_success_mismatch:crossing_01' in checks.inspect_study(study)['integrity_errors']


def test_supervisor_exit_is_not_success_even_if_flight_report_passed(study):
    summary = checks.load_json(study / 'study_summary.json')
    summary['trials'][0].update(returncode=1, success=False)
    checks.write_json(study / 'study_summary.json', summary)
    result = checks.inspect_study(study)
    assert result['evidence_complete'] and result['flight_passes'] == 0
    assert result['failure_counts']['supervisor_exit_1'] == 1


@pytest.mark.parametrize('field,value', [('error', 'audit failed'), ('interrupted', True),
                                        ('active_trial', 'crossing_01')])
def test_completed_flag_does_not_hide_interruption_or_error(study, field, value):
    status = checks.load_json(study / 'study_status.json')
    status[field] = value
    checks.write_json(study / 'study_status.json', status)
    assert not checks.inspect_study(study)['all_attempts_finished']


def test_archived_helpers_are_checked_independently_of_live_development(study):
    helper = study / 'reporting_helpers/old_helper.py'
    helper.parent.mkdir()
    helper.write_text('old version')
    provenance = checks.load_json(study / 'repeat_provenance.json')
    provenance['reporting_helper_sha256'] = {'scripts/old_helper.py': checks.digest(helper)}
    checks.write_json(study / 'repeat_provenance.json', provenance)
    assert checks.inspect_study(study)['evidence_complete']
    helper.write_text('modified')
    assert 'archived_helper_mismatch:scripts/old_helper.py' in checks.inspect_study(study)['integrity_errors']
