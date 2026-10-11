import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[4] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('frozen_repeat', SCRIPTS / 'repeat_frozen_crossing.py')
repeat = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repeat)


def test_crossing_repeat_plan_never_changes_reference_scene():
    plan = repeat.make_plan(10)
    assert len(plan) == 10 and len({row['name'] for row in plan}) == 10
    assert all(row['crossing'] and row['vehicle_speed'] == 0.8 and
               row['occlusion_start'] == 15 and row['occlusion_duration'] == 4 for row in plan)


def test_empty_repeat_plan_is_rejected():
    with pytest.raises(ValueError):
        repeat.make_plan(0)


def test_installed_frozen_node_mismatch_is_rejected(tmp_path):
    source = tmp_path / 'ros2_ws/src/uav_learning/uav_learning'
    installed = tmp_path / 'ros2_ws/install/uav_learning/lib/python3.12/site-packages/uav_learning'
    source.mkdir(parents=True)
    installed.mkdir(parents=True)
    (source / 'node.py').write_text('original')
    (installed / 'node.py').write_text('original')
    repeat.verify_installed(tmp_path)
    (installed / 'node.py').write_text('changed')
    with pytest.raises(RuntimeError, match='node.py'):
        repeat.verify_installed(tmp_path)


def test_compiled_rootfs_is_used_instead_of_runtime_copy(tmp_path, monkeypatch):
    rootfs = tmp_path / 'PX4-Autopilot/build/px4_sitl_default/rootfs'
    rootfs.mkdir(parents=True)
    (rootfs.parent / 'etc').mkdir()
    monkeypatch.setattr(repeat.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(
        stdout='other strings\n' + str(rootfs) + '\n'))
    assert repeat.compiled_px4_rootfs(tmp_path / 'archive/bin/px4') == rootfs


def test_unknown_compiled_rootfs_fails_before_flight(monkeypatch):
    monkeypatch.setattr(repeat.subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(stdout='unknown'))
    with pytest.raises(RuntimeError, match='refusing to guess'):
        repeat.compiled_px4_rootfs(Path('binary'))


def test_compiled_rootfs_assets_must_match_reference(tmp_path):
    rootfs = tmp_path / 'PX4-Autopilot/build/px4_sitl_default/rootfs'
    rootfs.mkdir(parents=True)
    name = 'PX4-Autopilot/build/px4_sitl_default/etc/config'
    path = tmp_path / name
    path.parent.mkdir()
    path.write_text('frozen')
    manifest = {'source_sha256': {name: repeat.digest(path)}}
    repeat.verify_shared_px4(rootfs, manifest)
    path.write_text('changed')
    with pytest.raises(RuntimeError, match='differ from the reference'):
        repeat.verify_shared_px4(rootfs, manifest)


@pytest.fixture
def prepared_batch(tmp_path, monkeypatch):
    directory = tmp_path / 'study'
    directory.mkdir()
    runtime = directory / 'runtime'
    rootfs = tmp_path / 'actual/PX4-Autopilot/build/px4_sitl_default/rootfs'
    for name in ('PX4-Autopilot/build/px4_sitl_default/rootfs/gz_env.sh',
                 'PX4-Autopilot/build/px4_sitl_default/bin/px4-alias.sh'):
        path = runtime / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('bootstrap')
    repeat.write_json(directory / 'plan.json', repeat.make_plan(1))
    repeat.write_json(directory / 'repeat_provenance.json', {
        'runtime': str(runtime), 'px4_rootfs': str(rootfs)})
    monkeypatch.setattr(sys, 'argv', ['repeat', '--reference', str(tmp_path / 'reference'),
                                    '--output', str(directory), '--count', '1', '--prepared'])
    monkeypatch.setattr(repeat, 'verify', lambda directory: runtime)
    monkeypatch.setattr(repeat.signal, 'signal', lambda *args: None)
    monkeypatch.setattr(repeat, 'publish_summary', lambda directory, plan, rows:
                        repeat.write_json(directory / 'study_summary.json', {'trials': rows}))
    monkeypatch.setattr(repeat, 'trial_row', lambda target, trial: {
        'name': trial['name'], 'directory': str(target), 'success': False,
        'failure_reasons': [], 'visibility': 0.7, 'unplanned_losses': 1})
    monkeypatch.setattr(repeat, 'inspect_study', lambda directory: {
        'failure_counts': {'confirmed_coverage_below_0_8': 1}, 'trials': []})
    monkeypatch.setattr(repeat.subprocess, 'run', lambda *args, **kwargs:
                        SimpleNamespace(returncode=1))
    return directory, rootfs


def test_finished_failed_attempt_is_counted_and_uses_actual_rootfs(prepared_batch, monkeypatch):
    directory, rootfs = prepared_batch
    monkeypatch.setattr(repeat.subprocess, 'Popen', lambda *args, **kwargs:
                        SimpleNamespace(poll=lambda: 0, returncode=1))
    audits = []
    monkeypatch.setattr(repeat, 'audit_studies', lambda directory, rootfs: audits.append(rootfs))
    repeat.main()
    status = repeat.load_json(directory / 'study_status.json')
    assert status['completed'] and status['attempted'] == status['planned'] == 1
    assert not status['error'] and status['active_trial'] is None
    assert audits == [rootfs]
    assert repeat.load_json(directory / 'study_summary.json')['trials'][0]['returncode'] == 1
    assert (directory / 'completion_check.json').is_file()
    assert (directory / 'failure_analysis.json').is_file()


def test_audit_error_keeps_attempt_and_never_marks_batch_complete(prepared_batch, monkeypatch):
    directory, _ = prepared_batch
    monkeypatch.setattr(repeat.subprocess, 'Popen', lambda *args, **kwargs:
                        SimpleNamespace(poll=lambda: 0, returncode=0))

    def failed_audit(*args, **kwargs):
        raise RuntimeError('archive mismatch')

    monkeypatch.setattr(repeat, 'audit_studies', failed_audit)
    with pytest.raises(RuntimeError, match='archive mismatch'):
        repeat.main()
    status = repeat.load_json(directory / 'study_status.json')
    assert not status['completed'] and status['attempted'] == 1
    assert status['error'] == 'archive mismatch'
    assert len(repeat.load_json(directory / 'study_summary.json')['trials']) == 1


def test_exception_waits_for_supervisor_safety_cleanup(prepared_batch, monkeypatch):
    directory, _ = prepared_batch
    actions = []
    child = SimpleNamespace(poll=lambda: None, send_signal=lambda sig: actions.append(sig),
                            wait=lambda: actions.append('wait'))
    monkeypatch.setattr(repeat.subprocess, 'Popen', lambda *args, **kwargs: child)

    def failed_wait(*args):
        raise RuntimeError('poll loop failed')

    monkeypatch.setattr(repeat.time, 'sleep', failed_wait)
    with pytest.raises(RuntimeError, match='poll loop failed'):
        repeat.main()
    assert actions == [repeat.signal.SIGINT, 'wait']
    status = repeat.load_json(directory / 'study_status.json')
    assert not status['completed'] and status['active_trial'] is None
    assert status['attempted'] == 1
    assert status['error'] == 'poll loop failed'
    row = repeat.load_json(directory / 'study_summary.json')['trials'][0]
    assert not row['success'] and 'batch_error:poll loop failed' in row['failure_reasons']


def test_launch_failure_is_preserved_in_denominator(prepared_batch, monkeypatch):
    directory, _ = prepared_batch

    def failed_launch(*args, **kwargs):
        raise OSError('launch unavailable')

    monkeypatch.setattr(repeat.subprocess, 'Popen', failed_launch)
    with pytest.raises(OSError, match='launch unavailable'):
        repeat.main()
    status = repeat.load_json(directory / 'study_status.json')
    assert not status['completed'] and status['attempted'] == 1
    row = repeat.load_json(directory / 'study_summary.json')['trials'][0]
    assert not row['success'] and row['returncode'] is None
    assert 'batch_error:launch unavailable' in row['failure_reasons']
