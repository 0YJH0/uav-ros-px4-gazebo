#!/usr/bin/env python3
"""Run one frozen OpenVINO pilot and gate subsequent repeats on strict evidence."""

import argparse
import copy
from pathlib import Path
import shutil
import signal
import subprocess

from audit_two_vehicle_scenarios import audit_trial, summarize_batch
from repeat_two_vehicle_scenarios import (
    ROOT, archive_trial, assert_no_simulation, backend_runtime,
    command_for, compiled_px4_rootfs, digest, make_plan, now,
    verify_installation, verify_reference,
)
from vehicle_experiment_study import freeze, load_json, verify_freeze, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--backend-artifacts', type=Path, required=True)
    parser.add_argument('--perception-python', type=Path, required=True)
    parser.add_argument('--equivalence-report', type=Path, required=True)
    args = parser.parse_args()
    directory, reference = args.output.resolve(), args.reference.resolve()
    artifacts = args.backend_artifacts.resolve()
    if directory.exists():
        raise RuntimeError('A new pilot directory is required; failed pilots are retained.')
    snapshot, parameters = verify_reference(ROOT, reference)
    verify_installation(ROOT)
    assert_no_simulation()
    model = Path(snapshot['model_path'])
    equivalence = load_json(args.equivalence_report)
    if (not equivalence or equivalence.get('passed') is not True
            or equivalence.get('model_sha256') != digest(model)
            or equivalence.get('backend_manifest_sha256') != digest(artifacts / 'manifest.json')):
        raise RuntimeError('Numerical equivalence must pass for these exact artifacts first.')
    runtime = backend_runtime(args.perception_python)
    scenario = make_plan(1, False, 'openvino', str(artifacts))[1]
    scenario['name'] = 'lane_change_pilot'
    directory.mkdir(parents=True)
    (directory / 'attempts').mkdir()
    frozen = freeze(ROOT, directory, model, artifacts)
    frozen['declared_parameters'] = copy.deepcopy(parameters)
    frozen['declared_parameters']['perception_node'].update(
        detector_backend='openvino', backend_artifacts=str(artifacts))
    helpers = ('repeat_two_vehicle_scenarios.py', 'audit_two_vehicle_scenarios.py',
               'run_openvino_vehicle_pilot.py', 'export_vehicle_openvino.py',
               'check_vehicle_backend_equivalence.py', 'compare_vehicle_backends.py',
               'repeat_frozen_crossing.py', 'audit_vehicle_ulog.py',
               'repeat_best_vehicle.py', 'vehicle_study_checks.py')
    for name in helpers:
        relative = 'scripts/' + name
        frozen['source_sha256'][relative] = digest(ROOT / relative)
        target = directory / 'frozen_files' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    write_json(directory / 'freeze_manifest.json', frozen)
    write_json(directory / 'plan.json', [scenario])
    protocol = {
        'created_utc': now(), 'phase': 'pilot', 'planned': 1,
        'reference': str(reference), 'pilot_excluded_from_repeat_statistics': True,
        'detector_backend': 'openvino', 'backend_artifacts': str(artifacts),
        'backend_runtime': runtime, 'model_path': str(model),
        'model_sha256': digest(model), 'gui': False,
        'px4_rootfs': str(compiled_px4_rootfs(ROOT / 'PX4-Autopilot/build/px4_sitl_default/bin/px4')),
        'freeze_manifest_sha256': digest(directory / 'freeze_manifest.json'),
        'equivalence_report_sha256': digest(args.equivalence_report),
        'baseline_runtime_parameters_sha256': digest(reference / 'runtime_parameters.json'),
        'promotion_gate': 'Only strict_joint_passed AND safe_to_continue permits batch validation.'}
    write_json(directory / 'batch_protocol.json', protocol)
    shutil.copy2(args.equivalence_report, directory / 'equivalence_report.json')
    command = command_for(ROOT, directory, scenario, str(model), runtime['interpreter'])
    ledger = {'name': scenario['name'], 'group': scenario['group'], 'state': 'started',
              'started_utc': now(), 'command': command,
              'freeze_manifest_sha256': protocol['freeze_manifest_sha256']}
    ledger_path = directory / 'attempts' / (scenario['name'] + '.json')
    write_json(ledger_path, ledger)
    process, interrupted = None, False

    def stop(signum, frame):
        nonlocal interrupted
        interrupted = True
        if process is not None and process.poll() is None:
            process.send_signal(signal.SIGINT)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    with (directory / 'pilot_supervisor.log').open('x') as stream:
        process = subprocess.Popen(command, cwd=ROOT, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        code = process.wait()
    ledger.update(state='interrupted' if interrupted else 'completed',
                  returncode=code, finished_utc=now())
    try:
        archive_trial(directory, scenario, protocol)
    except Exception as exc:
        ledger['archive_error'] = str(exc)
    write_json(ledger_path, ledger)
    audit = audit_trial(ROOT, directory / scenario['name'], scenario, frozen['source_sha256'])
    summarize_batch(directory)
    verify_freeze(ROOT, directory / 'freeze_manifest.json')
    verify_installation(ROOT)
    assert_no_simulation()
    runtime_unchanged = backend_runtime(args.perception_python) == runtime
    passed = bool(audit['strict_joint_passed'] and audit['safe_to_continue']
                  and runtime_unchanged and not ledger.get('archive_error'))
    write_json(directory / 'PILOT_GATE.json', {
        'passed': passed, 'trial': scenario['name'], 'strict_joint_passed': audit['strict_joint_passed'],
        'safe_to_continue': audit['safe_to_continue'], 'runtime_unchanged': runtime_unchanged,
        'batch_audit_sha256': digest(directory / scenario['name'] / 'batch_audit.json'),
        'failure_reasons': audit['failure_reasons']})
    print({'pilot_passed': passed, 'coverage_percent': audit['coverage_percent'],
           'failure_reasons': audit['failure_reasons']}, flush=True)
    return 0 if passed else 2


if __name__ == '__main__':
    raise SystemExit(main())
