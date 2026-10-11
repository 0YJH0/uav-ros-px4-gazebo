#!/usr/bin/env python3
"""Archive finished PX4 ULogs and audit recorded parameters with the binary parser."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil

from pyulog import ULog

from vehicle_experiment_study import ROOT, digest, load_json, write_json


def normalize(values):
    return {key: value if not isinstance(value, float) or math.isfinite(value) else str(value)
            for key, value in values.items()}


def log_source(rootfs, text):
    match = re.search(r'Opened full log file:\s+\./log/([^\s]+\.ulg)', text)
    if not match:
        return None
    relative = Path(match.group(1))
    log_root = (Path(rootfs) / 'log').resolve()
    source = (log_root / relative).resolve()
    if relative.is_absolute() or '..' in relative.parts or not source.is_relative_to(log_root):
        raise RuntimeError('Unsafe ULog path in PX4 console output.')
    return source


def audit_studies(study, crossing=None, rootfs=None):
    study = Path(study).resolve()
    roots = [study] + ([Path(crossing).resolve()] if crossing else [])
    observations, reference = [], None
    rootfs = Path(rootfs) if rootfs is not None else ROOT / 'PX4-Autopilot/build/px4_sitl_default/rootfs'
    previous = load_json(study / 'px4_parameter_audit.json') or {}
    known_hashes = {row['directory']: row.get('ulog_sha256')
                    for row in previous.get('trials', []) if row.get('available')}
    for directory in roots:
        summary = load_json(directory / 'study_summary.json')
        if not summary:
            continue
        for trial in summary['trials']:
            trial_dir = Path(trial['directory'])
            text = (trial_dir / 'px4.log').read_text(errors='replace') if (trial_dir / 'px4.log').exists() else ''
            result = {'name': trial['name'], 'directory': str(trial_dir), 'available': False}
            source = log_source(rootfs, text)
            destination = trial_dir / 'flight.ulg'
            source_available = source is not None and source.is_file()
            if source_available or destination.is_file():
                checksum = digest(source if source_available else destination)
                expected = known_hashes.get(str(trial_dir))
                if expected and checksum != expected:
                    raise RuntimeError('Previously audited ULog changed: ' + str(destination))
                if destination.exists() and digest(destination) != checksum:
                    raise RuntimeError('Existing archived ULog differs; refusing overwrite: '+str(destination))
                if not destination.exists():
                    shutil.copy2(source, destination)
                ulog = ULog(str(destination), message_name_filter_list=[])
                parameters = normalize(ulog.initial_parameters)
                fingerprint = hashlib.sha256(json.dumps(parameters, sort_keys=True).encode()).hexdigest()
                if reference is None:
                    reference = parameters
                differing = {key: {'reference': reference.get(key), 'observed': parameters.get(key)}
                             for key in reference.keys() | parameters.keys()
                             if reference.get(key) != parameters.get(key)}
                counters = {key: value for key, value in differing.items()
                            if key in ('COM_FLIGHT_UUID', 'LND_FLIGHT_T_LO', 'LND_FLIGHT_T_HI')}
                calibration = {key: value for key, value in differing.items() if key.startswith('CAL_')}
                other = {key: value for key, value in differing.items() if key not in counters and key not in calibration}
                changes = [{'timestamp_us': stamp, 'name': key, 'value': normalize({key: value})[key]}
                           for stamp, key, value in ulog.changed_parameters]
                result.update(available=True, ulog_sha256=checksum,
                              source_available=source_available,
                              source_path=str(source) if source is not None else None,
                              recorded_initial_parameters=len(parameters),
                              initial_parameter_sha256=fingerprint,
                              differences_from_first_attempt=differing, bookkeeping_differences=counters,
                              calibration_differences=calibration, other_parameter_differences=other,
                              parameter_updates_after_header=changes,
                              dropout_events=len(ulog.dropouts))
                write_json(trial_dir / 'px4_recorded_parameters.json', {
                    'initial_parameters': parameters, 'changed_parameters': changes,
                    'limitation': 'ULog records parameters used by PX4; unrecorded defaults are not independently checked.'})
            observations.append(result)
    report = {
        'attempted_logs': len(observations), 'available_logs': sum(item['available'] for item in observations),
        'rootfs': str(rootfs.resolve()),
        'trials': observations,
        'limitations': ['This is a retrospective audit, not a start-time enforcement mechanism.',
                        'Parameters not emitted into ULog cannot be independently compared.',
                        'Updates after the log header may occur during startup, before arming; they are not automatically in-flight updates.',
                        'Parameter-set differences may include used-set changes and startup calibration; inspect values before attributing control changes.',
                        'A retained archive can be audited after its source log disappears; source_available makes this explicit.']}
    write_json(study / 'px4_parameter_audit.json', report)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', type=Path, required=True)
    parser.add_argument('--crossing', type=Path)
    parser.add_argument('--rootfs', type=Path, help='Actual PX4 SITL rootfs, not the copied launch directory.')
    args = parser.parse_args()
    report = audit_studies(args.study, args.crossing, args.rootfs)
    observations = report['trials']
    print(json.dumps({'archived': sum(item['available'] for item in observations),
                      'attempted': len(observations),
                      'with_parameter_differences': [item['name'] for item in observations
                                                    if item.get('differences_from_first_attempt')],
                      'with_updates_after_header': [item['name'] for item in observations
                                                   if item.get('parameter_updates_after_header')]}, indent=2))


if __name__ == '__main__':
    main()
