import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def summary(monkeypatch):
    scripts = Path(__file__).resolve().parents[4] / 'scripts'
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location('study_summary', scripts / 'summarize_vehicle_studies.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_no_follow_has_no_defined_conditional_visibility_but_remains_failed(summary, tmp_path):
    row = {'directory': str(tmp_path), 'success': False, 'safety_event': True,
           'landed_disarmed': True, 'follow_wall_s': 0., 'visibility': 0.}
    enriched = summary.enrich(row)
    assert enriched['success_indicator'] == 0
    assert enriched['visibility'] == 0
    assert enriched['visibility_when_follow_started'] is None


def test_inference_is_separate_from_total_processing_and_return_is_excluded(summary, tmp_path):
    samples = [{'state': 'APPROACH', 'wall_s': 10}, {'state': 'RETURN', 'wall_s': 20}]
    associations = [{'wall_s': 11, 'processing_s': .2, 'detector': {'full_frame_s': .1, 'roi_s': .03}},
                    {'wall_s': 21, 'detector': {'full_frame_s': .9}}]
    (tmp_path / 'samples.jsonl').write_text('\n'.join(json.dumps(row) for row in samples))
    (tmp_path / 'association.jsonl').write_text('\n'.join(json.dumps(row) for row in associations))
    row = {'directory': str(tmp_path), 'success': True, 'safety_event': False,
           'landed_disarmed': True, 'follow_wall_s': 10., 'visibility': .8}
    enriched = summary.enrich(row)
    assert enriched['inference_mean_s'] == pytest.approx(.13)
    assert enriched['visibility_when_follow_started'] == .8


def test_unrecovered_loss_is_counted_not_imputed_as_zero_latency(summary, tmp_path):
    events = [{'event': 'TRACK_TARGET_LOST', 'time_s': 1},
              {'event': 'TARGET_RECOVERED', 'time_s': 3},
              {'event': 'TRACK_TARGET_LOST', 'time_s': 5},
              {'event': 'MISSION_DONE', 'time_s': 20}]
    (tmp_path / 'report.json').write_text(json.dumps({'events': events}))
    row = {'directory': str(tmp_path), 'success': False, 'safety_event': False, 'landed_disarmed': True}
    enriched = summary.enrich(row)
    assert enriched['recovery_max_s'] == 2
    assert enriched['unrecovered_loss_episodes'] == 1


def test_schedule_classification_is_supplemental_and_never_changes_failed_verdict(summary, tmp_path):
    report = {'events': [{'event': 'TRACK_TARGET_LOST', 'time_s': 11},
                         {'event': 'TARGET_RECOVERED', 'time_s': 15},
                         {'event': 'TRACK_TARGET_LOST', 'time_s': 20},
                         {'event': 'TARGET_RECOVERED', 'time_s': 21}],
              'occlusions': [{'start_wall_s': 10, 'end_wall_s': 14, 'entry_locked': False}]}
    (tmp_path / 'report.json').write_text(json.dumps(report))
    row = {'directory': str(tmp_path), 'success': False, 'safety_event': False,
           'landed_disarmed': True, 'unplanned_losses': 2}
    enriched = summary.enrich(row)
    assert not enriched['success'] and enriched['unplanned_losses'] == 2
    assert enriched['unplanned_losses_by_panel_schedule'] == 1
    assert enriched['schedule_unplanned_recovery_mean_s'] == 1
