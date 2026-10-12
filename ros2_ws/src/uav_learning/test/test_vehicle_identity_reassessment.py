import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts'))
import reassess_vehicle_identity as audit


def write_json(path, value):
    path.write_text(json.dumps(value))


def write_rows(path, values):
    path.write_text(''.join(json.dumps(value) + '\n' for value in values))


@pytest.fixture
def trial(tmp_path):
    directory = tmp_path / 'trial'
    directory.mkdir()
    target, other = [0, 0, 100, 100], [200, 0, 260, 50]
    rows = []
    for phase, stamp in (('pre', 0), ('during', 2), ('post', 12)):
        for index in range(10):
            rows.append({'label': 'tracked_vehicle' if phase != 'post' else 'overlap_unscorable',
                         'scores': {}, 'sim_s': stamp + index * .1, 'wall_s': stamp + index * .1,
                         'phase': phase, 'accepted_box': target,
                         'projected_boxes': {'tracked_vehicle': target, 'crossing_vehicle': other},
                         'relative_longitudinal_m': -7 + index * 1.6,
                         'world_lateral_clearance_m': 1.2})
    write_rows(directory / 'identity_observations.jsonl', rows)
    write_rows(directory / 'crossing_events.jsonl', [
        {'event': 'overtaking_started', 'sim_s': 1}, {'event': 'overtaking_completed', 'sim_s': 10}])
    write_json(directory / 'identity_report.json', {
        'errors': [], 'traffic_scenario': 'overtaking', 'distractor_color': 'red',
        'identity_independently_verified': False, 'phase_counts': {'post': {'overlap_unscorable': 10}}})
    write_json(directory / 'report.json', {
        'passed': True, 'follow_time_visible_fraction': .91, 'failsafe_observed': False})
    (directory / 'flight.ulg').write_bytes(b'retained-log-fixture')
    write_json(directory / 'validation_summary.json', {
        'task_passed': True, 'coverage_percent': 91., 'maneuver_observed': True,
        'ulog_safety': {'armed_failsafe_observations': 0, 'armed_offboard_lost_observations': 0,
                        'ulog_dropout_events': 0},
        'ulog_sha256': hashlib.sha256(b'retained-log-fixture').hexdigest(),
        'scene_requests': {'total': 2, 'failures': 0, 'receipt_errors': 0, 'sequence_errors': []}})
    write_json(directory / 'supervisor.json', {
        'error': None, 'interventions': [], 'landed_disarmed_before_shutdown': True,
        'parameters_verified': True, 'autonomous_passed': False})
    for client in ('scene', 'traffic'):
        write_rows(directory / (client + '_service.jsonl'), [
            {'client': client, 'sequence': 1, 'success': True,
             'binding_result': True, 'response_data': True}])
    return directory


def test_reassessment_preserves_inputs_and_uses_new_directory(trial):
    before = {path.name: path.read_bytes() for path in trial.iterdir()}
    output = trial.parent / 'reassessment'
    result = audit.reassess(trial, output)
    assert result['reassessed_identity_verified']
    assert result['strict_joint_passed']
    assert result['onboard_accepted_boxes_before'] == result['onboard_accepted_boxes_after'] == 30
    assert result['coverage_percent'] == 91.
    assert result['changed_observations'] == 10
    assert result['new_flight'] is False
    assert {path.name: path.read_bytes() for path in trial.iterdir()} == before
    assert (output / 'evaluation_sources/scripts/reassess_vehicle_identity.py').is_file()
    with pytest.raises(ValueError, match='new directory'):
        audit.reassess(trial, output)
    with pytest.raises(ValueError, match='outside'):
        audit.reassess(trial, trial / 'nested')
    with pytest.raises(ValueError):
        audit.reassess(trial, trial)


def test_masked_and_missing_evidence_not_reclassified():
    base = {'accepted_box': [0, 0, 10, 10], 'projected_boxes': {'tracked_vehicle': [0, 0, 10, 10]},
            'scores': {'retained': .3}}
    rows = [dict(base, label=label) for label in audit.MASKED_LABELS]
    rows += [{'label': 'projection_unscorable'},
             {'label': 'overlap_unscorable', 'projected_boxes': base['projected_boxes']}]
    result = audit.reclassify(rows)
    for old, new in zip(rows, result):
        if old['label'] in audit.MASKED_LABELS:
            assert new['label'] == old['label']
            assert new.get('scores') == old.get('scores')
            assert new['reassessment_status'] == 'preserved_masked_or_unmatched'
        else:
            assert new['label'] == 'projection_unscorable'
            assert new['reason'] == 'missing_frozen_geometry'
        assert new['original_label'] == old['label']
    assert all('identity_evaluation_version' not in row for row in result)


@pytest.mark.parametrize('missing', ['accepted_box', 'projected_boxes'])
def test_old_correct_label_without_frozen_geometry_cannot_prove_identity(trial, missing):
    rows = audit.load_rows(trial / 'identity_observations.jsonl')
    for row in rows:
        if row['phase'] == 'pre':
            del row[missing]
    write_rows(trial / 'identity_observations.jsonl', rows)
    result = audit.reassess(trial, trial.parent / 'missing_geometry')
    assert not result['reassessed_identity_verified']
    assert result['reassessed_phase_counts']['pre'] == {'projection_unscorable': 10}
    assert result['label_changes']['tracked_vehicle -> projection_unscorable'] == 10
    assert not result['strict_joint_passed']


def test_input_mutation_during_reads_does_not_leave_valid_reports(trial, monkeypatch):
    original_load = audit.load_rows

    def load_and_mutate(path):
        rows = original_load(path)
        if path.name == 'identity_observations.jsonl':
            report = trial / 'report.json'
            report.write_text(report.read_text() + '\n')
        return rows

    monkeypatch.setattr(audit, 'load_rows', load_and_mutate)
    output = trial.parent / 'changed_during_read'
    with pytest.raises(RuntimeError, match='Trial input changed'):
        audit.reassess(trial, output)
    assert not (output / 'comparison.json').exists()
    assert not (output / 'identity_report.json').exists()


def test_legacy_scenario_evidence_fallback_requires_complete_geometry(trial):
    validation = audit.load_json(trial / 'validation_summary.json')
    del validation['maneuver_observed']
    write_json(trial / 'validation_summary.json', validation)
    original = audit.load_json(trial / 'identity_report.json')
    original.update(traffic_started=True, traffic_completed=True, overtaking_observed=True,
                    minimum_world_lateral_clearance_m=1.2)
    write_json(trial / 'identity_report.json', original)
    result = audit.reassess(trial, trial.parent / 'legacy_complete')
    assert result['joint_check_status']['scenario'] == 'pass'
    assert result['strict_joint_passed']
    del original['minimum_world_lateral_clearance_m']
    write_json(trial / 'identity_report.json', original)
    result = audit.reassess(trial, trial.parent / 'legacy_incomplete')
    assert result['joint_check_status']['scenario'] == 'unknown'
    assert not result['strict_joint_passed']


def test_wrong_car_still_fails_despite_post_confirmation(trial):
    rows = audit.load_rows(trial / 'identity_observations.jsonl')
    wrong = dict(rows[-1], accepted_box=[200, 0, 260, 50], label='crossing_vehicle')
    write_rows(trial / 'identity_observations.jsonl', rows + [wrong])
    result = audit.reassess(trial, trial.parent / 'wrong')
    assert not result['reassessed_identity_verified']
    assert not result['strict_joint_passed']
    assert result['joint_check_status']['identity'] == 'fail'
    assert result['reassessed_phase_counts']['post']['crossing_vehicle'] == 1


def test_missing_geometry_cannot_erase_previously_recorded_wrong_identity(trial):
    rows = audit.load_rows(trial / 'identity_observations.jsonl')
    rows.append({'label': 'crossing_vehicle', 'phase': 'post', 'sim_s': 15, 'scores': {}})
    write_rows(trial / 'identity_observations.jsonl', rows)
    output = trial.parent / 'unreassessed_wrong'
    result = audit.reassess(trial, output)
    assert result['reassessed_phase_counts']['post']['tracked_vehicle'] == 10
    assert not result['reassessed_identity_verified']
    assert not result['strict_joint_passed']
    assert 'unreassessed_wrong_identity_evidence' in audit.load_json(output / 'identity_report.json')['errors']


def test_task_failure_cannot_be_repaired_by_identity(trial):
    report = audit.load_json(trial / 'report.json')
    report.update(passed=False, follow_time_visible_fraction=.746)
    write_json(trial / 'report.json', report)
    validation = audit.load_json(trial / 'validation_summary.json')
    validation.update(task_passed=False, coverage_percent=74.6)
    write_json(trial / 'validation_summary.json', validation)
    result = audit.reassess(trial, trial.parent / 'task_failed')
    assert result['reassessed_identity_verified']
    assert result['joint_check_status']['task'] == 'fail'
    assert not result['strict_joint_passed']
    assert result['coverage_percent'] == 74.6


@pytest.mark.parametrize('missing', ['supervisor.json', 'validation_summary.json', 'flight.ulg'])
def test_missing_safety_or_supervision_is_unknown_not_passed(trial, missing):
    (trial / missing).unlink()
    result = audit.reassess(trial, trial.parent / 'missing')
    assert not result['strict_joint_passed']
    assert 'unknown' in result['joint_check_status'].values()


def test_missing_service_sequences_are_explicit_unknown(trial):
    write_rows(trial / 'scene_service.jsonl', [
        {'client': 'scene', 'sequence': 5, 'success': True, 'binding_result': True, 'response_data': True}])
    result = audit.reassess(trial, trial.parent / 'missing_receipts')
    assert result['service_receipt_audit']['scene']['missing_sequences'] == [1, 2, 3, 4]
    assert result['joint_check_status']['services'] == 'unknown'
    assert not result['strict_joint_passed']


def test_missing_service_response_is_unknown_not_success(trial):
    write_rows(trial / 'scene_service.jsonl', [
        {'client': 'scene', 'sequence': 1, 'success': True, 'binding_result': True}])
    result = audit.reassess(trial, trial.parent / 'missing_response')
    assert result['service_receipt_audit']['scene']['unknown_receipts'] == 1
    assert result['joint_check_status']['services'] == 'unknown'
    assert not result['strict_joint_passed']
