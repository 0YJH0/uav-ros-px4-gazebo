import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[4] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('ulog_audit_tests', SCRIPTS / 'audit_vehicle_ulog.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


@pytest.fixture
def example(tmp_path, monkeypatch):
    rootfs = tmp_path / 'actual_rootfs'
    source = rootfs / 'log/sess001/log001.ulg'
    source.parent.mkdir(parents=True)
    source.write_bytes(b'example log')
    study = tmp_path / 'study'
    trial = study / 'crossing_01'
    trial.mkdir(parents=True)
    (trial / 'px4.log').write_text('Opened full log file: ./log/sess001/log001.ulg\n')
    audit.write_json(study / 'study_summary.json', {
        'trials': [{'name': 'crossing_01', 'directory': str(trial)}]})
    monkeypatch.setattr(audit, 'ULog', lambda *args, **kwargs: SimpleNamespace(
        initial_parameters={'COM_OF_LOSS_T': 1.0}, changed_parameters=[], dropouts=[]))
    return rootfs, source, study, trial


def test_explicit_real_rootfs_archives_session_named_log(example):
    rootfs, source, study, trial = example
    result = audit.audit_studies(study, rootfs=rootfs)
    assert result['available_logs'] == result['attempted_logs'] == 1
    assert (trial / 'flight.ulg').read_bytes() == source.read_bytes()
    assert result['rootfs'] == str(rootfs)
    assert result['trials'][0]['source_available']


def test_retained_archive_is_auditable_without_original_source(example):
    rootfs, source, study, _ = example
    original = audit.audit_studies(study, rootfs=rootfs)
    source.unlink()
    result = audit.audit_studies(study, rootfs=rootfs)
    assert result['available_logs'] == 1
    assert not result['trials'][0]['source_available']
    assert result['trials'][0]['ulog_sha256'] == original['trials'][0]['ulog_sha256']


def test_modified_archive_without_source_is_rejected(example):
    rootfs, source, study, trial = example
    audit.audit_studies(study, rootfs=rootfs)
    source.unlink()
    (trial / 'flight.ulg').write_bytes(b'changed')
    with pytest.raises(RuntimeError, match='Previously audited ULog changed'):
        audit.audit_studies(study, rootfs=rootfs)


def test_differing_archive_is_never_overwritten(example):
    rootfs, _, study, trial = example
    (trial / 'flight.ulg').write_bytes(b'other archive')
    with pytest.raises(RuntimeError, match='refusing overwrite'):
        audit.audit_studies(study, rootfs=rootfs)
    assert (trial / 'flight.ulg').read_bytes() == b'other archive'


def test_missing_log_stays_in_denominator(example):
    rootfs, source, study, _ = example
    source.unlink()
    result = audit.audit_studies(study, rootfs=rootfs)
    assert result['available_logs'] == 0 and result['attempted_logs'] == 1


@pytest.mark.parametrize('path', ['../secret.ulg', '/tmp/secret.ulg', 'sess/../../secret.ulg'])
def test_console_log_cannot_escape_rootfs(tmp_path, path):
    with pytest.raises(RuntimeError, match='Unsafe ULog path'):
        audit.log_source(tmp_path, 'Opened full log file: ./log/' + path)


def test_symlink_log_escape_is_rejected(tmp_path):
    rootfs = tmp_path / 'rootfs'
    (rootfs / 'log').mkdir(parents=True)
    (rootfs / 'log/outside').symlink_to(tmp_path / 'elsewhere')
    with pytest.raises(RuntimeError, match='Unsafe ULog path'):
        audit.log_source(rootfs, 'Opened full log file: ./log/outside/data.ulg')
