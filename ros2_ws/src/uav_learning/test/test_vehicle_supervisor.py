import importlib.util
from pathlib import Path
import subprocess
import shlex
from types import SimpleNamespace

import pytest


spec = importlib.util.spec_from_file_location(
    'vehicle_supervisor', Path(__file__).resolve().parents[4] / 'scripts/run_vehicle_tracking_validation.py')
supervisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(supervisor)


def test_torch_default_does_not_pass_empty_launch_argument():
    assert supervisor.backend_launch_argument(None) == ''


def test_backend_launch_path_is_one_shell_argument(tmp_path):
    path = tmp_path / 'backend artifacts'
    assert shlex.split(supervisor.backend_launch_argument(path)) == [
        'backend_artifacts:=' + str(path.resolve())]


def test_parameter_capture_uses_direct_discovery_and_retries_node_not_found(tmp_path):
    calls, now = [], [0.0]

    def run(args, **kwargs):
        calls.append(args[-1])
        if len(calls) == 1:
            return SimpleNamespace(returncode=1, stdout='', stderr='Node not found')
        name = args[-1].split()[-1]
        return SimpleNamespace(returncode=0, stderr='', stdout=f'{name}:\n  ros__parameters:\n    value: 1\n')

    captured, attempts = supervisor.capture_runtime_parameters(
        tmp_path, {}, 'exec ', run=run, clock=lambda: now[0],
        sleep=lambda delay: now.__setitem__(0, now[0] + delay))
    assert len(captured) == 3 and len(attempts) == 4
    assert not attempts[0]['ok'] and attempts[1]['ok']
    assert all('--no-daemon' in call and '--timeout 5' in call for call in calls)


def test_parameter_capture_deadline_retains_failed_attempts(tmp_path):
    now = [0.0]

    def run(args, **kwargs):
        now[0] += kwargs['timeout']
        raise subprocess.TimeoutExpired(args, kwargs['timeout'])

    with pytest.raises(RuntimeError, match='perception_node.*attempts='):
        supervisor.capture_runtime_parameters(tmp_path, {}, 'exec ', timeout=3,
            run=run, clock=lambda: now[0], sleep=lambda delay: now.__setitem__(0, now[0] + delay))
    assert now[0] == 3


def test_empty_parameter_response_is_not_accepted(tmp_path):
    now = [0.0]
    with pytest.raises(RuntimeError, match='empty parameter response'):
        supervisor.capture_runtime_parameters(tmp_path, {}, 'exec ', timeout=2,
            run=lambda *args, **kwargs: SimpleNamespace(returncode=0, stderr='',
                                                       stdout='/perception_node:\n  ros__parameters: {}'),
            clock=lambda: now[0], sleep=lambda delay: now.__setitem__(0, now[0] + delay))


def test_abort_stops_offboard_before_requesting_landing_and_waits_for_disarm():
    calls, now = [], [0.0]
    landed = supervisor.safety_land(
        lambda: calls.append('stop'), lambda: calls.append('land'),
        lambda: now[0] >= 4, bool, clock=lambda: now[0],
        sleep=lambda delay: now.__setitem__(0, now[0] + delay))
    assert calls == ['stop', 'land'] and landed and now[0] == 4


def test_abort_timeout_does_not_claim_safe_landing():
    now = [0.0]
    assert not supervisor.safety_land(lambda: None, lambda: 0, lambda: False, bool, timeout=3,
        clock=lambda: now[0], sleep=lambda delay: now.__setitem__(0, now[0] + delay))
    assert now[0] == 3


def test_rejected_landing_command_is_explicit_failure():
    with pytest.raises(RuntimeError, match='landing command failed'):
        supervisor.safety_land(lambda: None, lambda: 1, lambda: True, bool)


def test_detector_preflight_explicitly_uses_virtualenv_before_flight(tmp_path):
    calls = []

    def run(args, **kwargs):
        calls.append(args[-1])
        return SimpleNamespace(returncode=0, stderr='')

    executable = supervisor.detector_preflight(tmp_path, {}, 'exec ', run=run)
    assert executable == str(tmp_path / '.venv-yolo/bin/python')
    assert executable in calls[0] and 'ultralytics' in calls[0] and 'cv_bridge' in calls[0]


def test_detector_preflight_import_failure_is_not_ignored(tmp_path):
    with pytest.raises(RuntimeError, match='preflight failed.*ultralytics'):
        supervisor.detector_preflight(tmp_path, {}, 'exec ',
            run=lambda *args, **kwargs: SimpleNamespace(returncode=1, stderr='No module named ultralytics'))
def test_latched_failsafe_aborts_even_after_live_flag_clears():
    supervisor.check_sample_safety(None)
    supervisor.check_sample_safety({'status': {'failsafe': False}})
    with pytest.raises(RuntimeError, match='failsafe observed'):
        supervisor.check_sample_safety({'status': {'failsafe': True}})
    with pytest.raises(RuntimeError, match='failsafe observed'):
        supervisor.check_sample_safety({'status': {'failsafe': False}, 'failsafe_observed': True})


def test_sample_tail_read_ignores_partial_write_and_large_prefix(tmp_path):
    path = tmp_path / 'samples.jsonl'
    assert supervisor.read_latest_sample(path) is None
    path.write_text('x' * 200000 + '\n' + '{"wall_s": 1}\n' + '{"wall_s":')
    assert supervisor.read_latest_sample(path) == {'wall_s': 1}
