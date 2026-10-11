import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def runner(monkeypatch):
    scripts = Path(__file__).resolve().parents[4] / 'scripts'
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location('competition_study', scripts / 'repeat_vehicle_competition.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_paired_plan_changes_only_feature_switch_and_balances_order(runner):
    plan = runner.make_plan(5)
    assert len(plan) == 10 and len({item['name'] for item in plan}) == 10
    assert sum(item['recovery_competition_enabled'] for item in plan) == 5
    for a, b in zip(plan[::2], plan[1::2]):
        assert a['pair'] == b['pair']
        assert a['recovery_competition_enabled'] != b['recovery_competition_enabled']
        excluded = {'name', 'group', 'recovery_competition_enabled'}
        assert {k: v for k, v in a.items() if k not in excluded} == {k: v for k, v in b.items() if k not in excluded}
    with pytest.raises(ValueError):
        runner.make_plan(0)


def test_paired_summary_retains_failed_trials_and_missing_pairs(runner):
    from summarize_vehicle_competition import paired_summary
    plan = runner.make_plan(2)
    rows = [{**plan[0], 'visibility': .8, 'success': False, 'safety_event': False},
            {**plan[1], 'visibility': .7, 'success': False, 'safety_event': True},
            {**plan[2], 'visibility': None, 'success': False, 'safety_event': True}]
    report = paired_summary(rows, plan)
    assert report['paired_metrics']['visibility']['mean_delta'] == pytest.approx(-.1)
    assert report['paired_metrics']['visibility']['missing_pairs'] == 1
    assert report['safety_event_trials'] == 2 and report['attempted'] == 3


def test_latency_scale_plan_changes_only_one_variable_and_balances_order(runner):
    plan = runner.make_latency_scale_plan(3)
    assert len(plan) == 9
    for group in ('baseline', 'scale_hold', 'openvino'):
        assert sum(trial['group'] == group for trial in plan) == 3
    reference = plan[0]
    excluded = {'name', 'pair', 'group'}
    for trial in plan:
        changed = {key for key in reference if key not in excluded and reference[key] != trial[key]}
        assert changed == ({'predict_box_scale_velocity'} if trial['group'] == 'scale_hold' else
                           {'detector_backend'} if trial['group'] == 'openvino' else set())


def test_interpreter_path_preserves_virtual_environment_symlink(runner, tmp_path):
    system = tmp_path / 'system_python'
    system.write_text('placeholder')
    venv = tmp_path / 'venv_python'
    venv.symlink_to(system)
    assert runner.preserve_interpreter_path(venv) == str(venv)
    assert runner.preserve_interpreter_path(venv) != str(venv.resolve())
