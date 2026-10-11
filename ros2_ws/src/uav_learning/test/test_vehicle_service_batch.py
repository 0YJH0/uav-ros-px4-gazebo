from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'scripts'))
import summarize_vehicle_service_batch as summary


def test_failed_service_calls_remain_in_latency_and_failure_statistics():
    rows = [{'success': True, 'duration_s': .001, 'reason': 'accepted'},
            {'success': False, 'duration_s': .5, 'reason': 'request_not_confirmed'}]
    result = summary.request_summary(rows)
    assert result['requests'] == 2 and result['failed'] == 1
    assert result['failed_reasons'] == {'request_not_confirmed': 1}
    assert result['mean_ms'] == pytest.approx(250.5)
    assert result['max_ms'] == 500


def test_empty_log_has_missing_latency_not_zero_latency():
    result = summary.request_summary([])
    assert result['requests'] == 0
    assert result['mean_ms'] is result['p95_ms'] is result['max_ms'] is None


def test_running_batch_cannot_be_reported_as_final(tmp_path, monkeypatch):
    monkeypatch.setattr(summary, 'load_json', lambda path: {'active_trial': 'overtaking_01'})
    with pytest.raises(RuntimeError, match='finish'):
        summary.analyze(tmp_path)


def test_interval_between_trials_cannot_be_reported_as_finished(tmp_path, monkeypatch):
    monkeypatch.setattr(summary, 'load_json', lambda path: {
        'active_trial': None, 'completed': False, 'interrupted': False, 'error': None})
    with pytest.raises(RuntimeError, match='finish'):
        summary.analyze(tmp_path)


def test_missing_request_logs_are_explicit_integrity_errors(tmp_path, monkeypatch):
    row = {'directory': str(tmp_path / 'trial'), 'name': 'trial', 'success': False,
           'flight_success': False, 'identity_independently_verified': False,
           'visibility': None, 'planned_recovery_s': None, 'outside_panel_losses': None,
           'scene_update_errors': 0, 'safety_event': True, 'criteria_failure_causes': ['missing_report']}
    data = {'study_summary.json': {'trials': [row]},
            'study_status.json': {'active_trial': None, 'planned': 10, 'attempted': 1,
                                  'completed': False, 'error': 'safety_stop'},
            'batch_protocol.json': {'reference': 'reference'}}
    monkeypatch.setattr(summary, 'load_json', lambda path: data.get(path.name))
    monkeypatch.setattr(summary, 'digest', lambda path: 'test-hash')
    result = summary.analyze(tmp_path)
    assert len(result['log_integrity_errors']) == 2
    assert all(not item['present'] for item in result['log_integrity_errors'])
    assert result['completed'] is False and result['strict_passes'] == 0
