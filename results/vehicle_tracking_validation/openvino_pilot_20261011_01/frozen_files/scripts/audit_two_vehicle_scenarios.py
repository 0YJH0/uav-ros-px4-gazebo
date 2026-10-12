#!/usr/bin/env python3
"""Audit frozen two-scenario repeats without changing online or identity criteria."""

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ('overtaking', 'lane_change_overtaking')
SAFETY_FIELDS = ('armed_failsafe_observations', 'armed_offboard_lost_observations',
                 'ulog_dropout_events')
METRICS = {
    'task_passed': 'min', 'strict_joint_passed': 'min', 'identity_verified': 'min',
    'coverage_percent': 'min', 'unplanned_losses': 'max',
    'unplanned_recovery_mean_s': 'max', 'unplanned_recovery_max_s': 'max',
    'unplanned_recovery_censored_count': 'max', 'recovery_timeout_count': 'max',
    'planned_recovery_mean_s': 'max', 'planned_recovery_max_s': 'max',
    'track_mean_abs_pixel_error': 'max', 'track_p95_abs_pixel_error': 'max',
    'final_home_horizontal_error_m': 'max', 'drone_follow_travel_m': 'min',
    'full_frame_yolo_mean_s': 'max', 'full_frame_yolo_p95_s': 'max',
    'processing_mean_s': 'max', 'processing_p95_s': 'max',
    'target_publish_age_mean_s': 'max', 'target_publish_age_p95_s': 'max',
    'queue_wait_mean_s': 'max', 'queue_wait_p95_s': 'max',
    'wrong_identity_observations': 'max', 'scorable_identity_switches': 'max',
    'identity_scorable_fraction': 'min', 'post_identity_frames': 'min',
    'scene_request_failures': 'max', 'safety_event_observations': 'max',
    'wall_duration_s': 'max',
}


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def read_json(path, default=None):
    try:
        value = json.loads(Path(path).read_text())
        return value if default is None or isinstance(value, type(default)) else default
    except (OSError, ValueError):
        return default


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def read_jsonl(path):
    rows, errors = [], []
    try:
        with Path(path).open() as stream:
            for index, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError('record is not an object')
                    rows.append(value)
                except ValueError:
                    errors.append(index)
    except OSError:
        errors.append('missing_file')
    return rows, errors


def finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def distribution(values, worst='max'):
    values = [float(value) for value in values if finite(value)]
    if not values:
        return {'count': 0, 'mean': None, 'sample_std': None, 'min': None,
                'max': None, 'p95': None, 'worst': None}
    ordered = sorted(values)
    point = .95 * (len(ordered) - 1)
    low, high = math.floor(point), math.ceil(point)
    return {'count': len(values), 'mean': statistics.mean(values),
            'sample_std': statistics.stdev(values) if len(values) > 1 else None,
            'min': min(values), 'max': max(values),
            'p95': ordered[low] + (ordered[high] - ordered[low]) * (point - low),
            'worst': min(values) if worst == 'min' else max(values)}


def recovery_episodes(report):
    """Pair each loss only within its own episode; never borrow a later recovery."""
    events = sorted((event for event in report.get('events', [])
                     if finite(event.get('time_s'))), key=lambda event: event['time_s'])
    end = report.get('wall_duration_s')
    if not finite(end):
        end = max((event['time_s'] for event in events), default=None)
    episodes = []
    for index, loss in enumerate(events):
        if loss.get('event') != 'TRACK_TARGET_LOST':
            continue
        stamp = loss['time_s']
        planned = any(finite(panel.get('start_wall_s')) and finite(panel.get('end_wall_s'))
                      and panel['start_wall_s'] <= stamp <= panel['end_wall_s']
                      for panel in report.get('occlusions', []))
        timeout, recovered, boundary = False, None, end
        for event in events[index + 1:]:
            kind = event.get('event')
            if kind in ('TARGET_RECOVERED', 'TRACK_REACQUIRED'):
                recovered, boundary = event, event['time_s']
                break
            if kind == 'RECOVERY_TIMEOUT':
                timeout = True
            if kind in ('TRACK_TARGET_LOST', 'TRACK_COMPLETE', 'MISSION_DONE'):
                boundary = event['time_s']
                break
        episodes.append({
            'loss_wall_s': stamp, 'planned_occlusion': planned,
            'confirmation_wall_s': recovered['time_s'] if recovered else None,
            'duration_s': recovered['time_s'] - stamp if recovered else None,
            'censored': recovered is None,
            'censor_lower_bound_s': max(0., boundary - stamp) if recovered is None and finite(boundary) else None,
            'recovery_timeout': timeout,
        })
    return episodes


def service_evidence(trial):
    rows, files, errors = [], {}, []
    for name in ('scene_service.jsonl', 'traffic_service.jsonl'):
        records, malformed = read_jsonl(trial / name)
        files[name] = {'rows': len(records), 'malformed_lines': malformed,
                       'sha256': digest(trial / name) if (trial / name).is_file() else None}
        if not records or malformed:
            errors.append('incomplete_service_log:' + name)
        expected_client = 'scene' if name == 'scene_service.jsonl' else 'traffic'
        if any(row.get('client') != expected_client for row in records):
            errors.append('unexpected_service_client:' + name)
        rows.extend(records)
    failures = sum(row.get('success') is not True for row in rows)
    semantics = sum(row.get('success') != (row.get('binding_result') is True
                    and row.get('response_data') is True) for row in rows)
    sequences = {}
    for client in sorted({str(row.get('client', '<missing>')) for row in rows}):
        values = [row.get('sequence') for row in rows if str(row.get('client', '<missing>')) == client]
        valid = all(isinstance(value, int) and not isinstance(value, bool) and value > 0 for value in values)
        complete = valid and values == list(range(1, len(values) + 1))
        sequences[client] = {'count': len(values), 'first': values[0], 'last': values[-1],
                             'complete_from_one': complete,
                             'missing': sorted(set(range(1, max(values) + 1)) - set(values)) if valid else None,
                             'duplicates': sorted(value for value, count in Counter(values).items() if count > 1) if valid else None}
        if not complete or client == '<missing>':
            errors.append('service_receipt_sequence_incomplete:' + client)
    if failures:
        errors.append('scene_service_requests_failed')
    if semantics:
        errors.append('service_receipt_semantics_mismatch')
    return {'total': len(rows), 'failures': failures, 'receipt_errors': semantics,
            'client_sequences': sequences, 'files': files, 'errors': errors,
            'passed': not errors}


def scenario_evidence(identity, scenario):
    if scenario == 'lane_change_overtaking':
        evidence = identity.get('lane_change') or {}
        return bool(identity.get('traffic_started') and identity.get('traffic_completed')
                    and evidence.get('maneuver_observed')), evidence
    if scenario == 'overtaking':
        clearance = identity.get('minimum_world_lateral_clearance_m')
        evidence = {'traffic_started': identity.get('traffic_started'),
                    'traffic_completed': identity.get('traffic_completed'),
                    'overtaking_observed': identity.get('overtaking_observed'),
                    'minimum_world_lateral_clearance_m': clearance}
        return bool(evidence['traffic_started'] and evidence['traffic_completed']
                    and evidence['overtaking_observed'] and finite(clearance) and clearance >= .5), evidence
    return False, {'error': 'unsupported_scenario'}


def integrity_evidence(root, trial, scenario, expected_sources):
    snapshot = read_json(trial / 'implementation_snapshot.json', {})
    parameters = read_json(trial / 'runtime_parameters.json', {})
    frozen = read_json(trial.parent / 'freeze_manifest.json', {})
    expected_sources = expected_sources if expected_sources is not None else frozen.get('source_sha256', {})
    errors, verified = [], []
    sources = snapshot.get('source_sha256') or {}
    if not sources:
        errors.append('missing_source_snapshot')
    for relative, expected in sources.items():
        archived = trial / 'executed_sources' / relative
        # The runner may archive one immutable shared copy for every attempt.
        if not archived.is_file():
            archived = trial.parent / 'frozen_files' / relative
        if not archived.is_file() or digest(archived) != expected:
            errors.append('source_archive_mismatch:' + relative)
        elif expected_sources and expected_sources.get(relative) != expected:
            errors.append('source_not_frozen:' + relative)
        else:
            verified.append(relative)
    if expected_sources:
        # Evaluators and batch tools are frozen too, although not all are in the flight snapshot.
        for relative, expected in expected_sources.items():
            archived = trial.parent / 'frozen_files' / relative
            if not archived.is_file() or digest(archived) != expected:
                errors.append('frozen_archive_mismatch:' + relative)
    elif frozen:
        errors.append('missing_frozen_source_hashes')
    model = Path(snapshot.get('model_path') or '/nonexistent')
    if not model.is_absolute():
        model = root / model
    if not model.is_file() or digest(model) != snapshot.get('model_sha256'):
        errors.append('model_hash_mismatch')
    if frozen.get('model_sha256') and snapshot.get('model_sha256') != frozen['model_sha256']:
        errors.append('model_not_frozen')
    if frozen.get('model_path'):
        frozen_model = Path(frozen['model_path']).resolve()
        relative_model = str(frozen_model.relative_to(root)) if frozen_model.is_relative_to(root) else None
        if (model.resolve() != frozen_model or relative_model is None
                or expected_sources.get(relative_model) != snapshot.get('model_sha256')):
            errors.append('model_not_frozen')
    runtime_model = parameters.get('perception_node', {}).get('model_path')
    if runtime_model and Path(runtime_model).resolve() != model.resolve():
        errors.append('runtime_model_path_mismatch')
    if scenario.get('detector_backend') == 'openvino':
        artifacts = Path(scenario.get('backend_artifacts') or '/nonexistent')
        expected_artifacts = snapshot.get('backend_artifact_sha256') or {}
        required = {'manifest.json', 'detector_960.xml', 'detector_960.bin',
                    'detector_640.xml', 'detector_640.bin'}
        if set(expected_artifacts) != required:
            errors.append('openvino_artifact_manifest_incomplete')
        for name, checksum in expected_artifacts.items():
            path = artifacts / name
            relative = str(path.relative_to(root)) if path.is_relative_to(root) else None
            if (name not in required or not path.is_file() or digest(path) != checksum
                    or relative is None or expected_sources.get(relative) != checksum):
                errors.append('openvino_artifact_not_frozen:' + name)
        manifest = read_json(artifacts / 'manifest.json', {})
        if (manifest.get('weight_sha256') != snapshot.get('model_sha256')
                or manifest.get('precision') != 'FP32'):
            errors.append('openvino_weight_or_precision_mismatch')
        protocol = read_json(trial.parent / 'batch_protocol.json', {})
        expected_python = (protocol.get('backend_runtime') or {}).get('interpreter')
        supervisor = read_json(trial / 'supervisor.json', {})
        if not expected_python or supervisor.get('perception_python') != expected_python:
            errors.append('openvino_interpreter_not_verified')
    expected_parameters = frozen.get('declared_parameters')
    if expected_parameters:
        from vehicle_experiment_study import verify_parameters
        try:
            verify_parameters(parameters, scenario, expected_parameters)
        except (RuntimeError, KeyError) as exc:
            errors.append('runtime_parameter_mismatch:' + str(exc))
    if not parameters:
        errors.append('missing_runtime_parameters')
    for node, expectations in {
        'perception_node': {'overlap_candidate_recovery': True, 'bounded_scale_prediction': True,
                            'overlap_confirmation_continuity': True, 'target_reacquire_timeout': 10.},
        'px4_offboard_controller': {'recovery_timeout': 10., 'recovery_max_distance': 4., 'recovery_max_speed': .8},
        'vehicle_scene': {'traffic_scenario': scenario['traffic_scenario'], 'distractor_color': 'red',
                          'parked_vehicle_y': -4.4, 'vehicle_speed': .8,
                          'occlusion_start': 15., 'occlusion_duration': 4.},
    }.items():
        for key, value in expectations.items():
            actual = parameters.get(node, {}).get(key)
            if actual != value or (isinstance(value, bool) and not isinstance(actual, bool)):
                errors.append('required_parameter_mismatch:' + node + '.' + key)
    for key, expected in scenario.items():
        if key not in ('name', 'group') and snapshot.get('scenario', {}).get(key) != expected:
            errors.append('scenario_snapshot_mismatch:' + key)
    return {'passed': not errors, 'errors': errors, 'verified_source_files': len(verified),
            'model_sha256': snapshot.get('model_sha256')}


def recorded_px4_parameters(trial):
    from pyulog import ULog
    from audit_vehicle_ulog import normalize
    ulog = ULog(str(trial / 'flight.ulg'), message_name_filter_list=[])
    parameters = normalize(ulog.initial_parameters)
    result = {'initial_parameters': parameters,
              'initial_parameter_sha256': hashlib.sha256(json.dumps(parameters, sort_keys=True).encode()).hexdigest(),
              'changed_parameters': [{'timestamp_us': stamp, 'name': key,
                                      'value': normalize({key: value})[key]}
                                     for stamp, key, value in ulog.changed_parameters],
              'limitations': ['ULog records the used parameter set, not necessarily all PX4 defaults.',
                              'Updates include startup calibration and are not automatically in-flight updates.']}
    write_json(trial / 'px4_recorded_parameters.json', result)
    return result


def parameter_differences(reference, observed):
    differing = {key: {'reference': reference.get(key), 'observed': observed.get(key)}
                 for key in sorted(reference.keys() | observed.keys()) if reference.get(key) != observed.get(key)}
    counters = {key: value for key, value in differing.items()
                if key in ('COM_FLIGHT_UUID', 'LND_FLIGHT_T_LO', 'LND_FLIGHT_T_HI')}
    calibration = {key: value for key, value in differing.items() if key.startswith('CAL_')}
    other = {key: value for key, value in differing.items() if key not in counters and key not in calibration}
    return {'bookkeeping_differences': counters, 'calibration_differences': calibration,
            'other_parameter_differences': other}


def audit_trial(root, trial_dir, scenario, expected_sources=None):
    root, trial = Path(root), Path(trial_dir)
    if isinstance(scenario, str):
        scenario = {'traffic_scenario': scenario}
    report = read_json(trial / 'report.json', {})
    identity = read_json(trial / 'identity_report.json', {})
    supervisor = read_json(trial / 'supervisor.json', {})
    attempt = read_json(trial.parent / 'attempts' / (trial.name + '.json'), {})
    reasons = []
    attempt_complete = not attempt or attempt.get('state') == 'completed'
    if not attempt_complete:
        reasons.append('attempt_not_completed:' + str(attempt.get('state')))
    if attempt and attempt.get('returncode') != 0:
        reasons.append('supervisor_exit_not_zero:' + str(attempt.get('returncode')))
    for name, value in (('report', report), ('identity_report', identity), ('supervisor', supervisor)):
        if not value:
            reasons.append('missing_or_invalid_' + name)
    integrity = integrity_evidence(root, trial, scenario, expected_sources)
    reasons.extend(integrity['errors'])
    services = service_evidence(trial)
    reasons.extend(services['errors'])
    geometry_passed, geometry = scenario_evidence(identity, scenario['traffic_scenario'])
    if not geometry_passed:
        reasons.append('scenario_maneuver_not_verified')
    if identity.get('identity_evaluation_version') != 'exclusive_projection_v2':
        reasons.append('identity_evaluation_version_not_v2')
    if identity.get('traffic_scenario') != scenario['traffic_scenario']:
        reasons.append('identity_scenario_mismatch')
    if identity.get('target_color') != 'red' or identity.get('distractor_color') != 'red':
        reasons.append('identity_scene_color_mismatch')
    if not identity.get('identity_independently_verified'):
        reasons.append('independent_identity_not_verified')
    for phase in ('pre', 'post'):
        if identity.get('phase_counts', {}).get(phase, {}).get('tracked_vehicle', 0) < 10:
            reasons.append(phase + '_identity_evidence_insufficient')
    if identity.get('wrong_identity_observations'):
        reasons.append('wrong_identity_observations')
    reasons.extend('identity_observer_error:' + str(value) for value in identity.get('errors', []))
    for field in ('passed', 'completed', 'track_complete_event', 'landed', 'disarmed'):
        if report.get(field) is not True:
            reasons.append('task_' + field + '_not_confirmed')
    for field, predicate in (
        ('follow_time_visible_fraction', lambda value: value >= .8),
        ('track_detection_fraction', lambda value: value >= .8),
        ('vehicle_travel_m', lambda value: value > 1.),
        ('drone_track_travel_m', lambda value: value > 1.),
        ('final_home_horizontal_error_m', lambda value: value <= 1.),
    ):
        if not finite(report.get(field)) or not predicate(report[field]):
            reasons.append('task_criterion:' + field)
    if not report.get('occlusions') or report.get('occlusion_recovery_passed') is not True:
        reasons.append('planned_occlusion_criteria_not_met')
    for field in ('autonomous_passed', 'landed_disarmed_before_shutdown'):
        if supervisor.get(field) is not True:
            reasons.append('supervisor_' + field + '_not_confirmed')
    if supervisor.get('interventions'):
        reasons.append('supervisor_intervention')
    if supervisor.get('error'):
        reasons.append('supervisor_error:' + str(supervisor['error']))
    exits = supervisor.get('process_exit_codes', {})
    processes_finished = bool(exits) and all(value is not None for value in exits.values())
    if not processes_finished:
        reasons.append('process_exit_not_confirmed')
    safety, px4_parameters = None, None
    if processes_finished and (trial / 'flight.ulg').is_file():
        try:
            from repeat_best_vehicle import ulog_safety
            safety = ulog_safety(trial / 'flight.ulg')
            px4_parameters = recorded_px4_parameters(trial)
        except Exception as exc:
            reasons.append('ulog_parse_failed:' + type(exc).__name__ + ':' + str(exc))
    else:
        reasons.append('ulog_safety_evidence_missing')
    if report.get('failsafe_observed'):
        reasons.append('px4_failsafe_observed')
    if safety:
        reasons.extend(field for field, value in safety.items() if value)
    associations, malformed = read_jsonl(trial / 'association.jsonl')
    if scenario.get('detector_backend') == 'openvino' and any(
            row.get('detector_backend') != 'openvino' for row in associations):
        reasons.append('recorded_detector_backend_mismatch')
    stamps = [(row.get('stamp', {}).get('sec'), row.get('stamp', {}).get('nanosec')) for row in associations]
    valid_stamps = all(all(isinstance(value, int) for value in stamp) for stamp in stamps)
    frame_integrity = bool(stamps) and not malformed and valid_stamps
    if frame_integrity:
        frame_integrity = all(before < after for before, after in zip(stamps, stamps[1:]))
    if not frame_integrity:
        reasons.append('association_frame_integrity_failed')
    timing = {field: distribution(row.get(field) for row in associations)
              for field in ('processing_s', 'target_publish_age_s', 'queue_wait_s')}
    timing['full_frame_yolo_s'] = distribution(row.get('detector', {}).get('full_frame_yolo_s') for row in associations)
    episodes = recovery_episodes(report)
    unplanned = [item for item in episodes if not item['planned_occlusion']]
    recovered = distribution(item['duration_s'] for item in unplanned)
    planned = distribution(item.get('confirmed_recovery_s') for item in report.get('occlusions', []))
    coverage = report.get('follow_time_visible_fraction')
    total_identity = identity.get('observations_total')
    scorable = identity.get('scorable_observations')
    row = {
        'name': trial.name, 'group': scenario.get('group', scenario['traffic_scenario']),
        'directory': str(trial), 'traffic_scenario': scenario['traffic_scenario'],
        'attempted': True, 'completed': processes_finished and bool(report) and attempt_complete,
        'task_passed': report.get('passed') is True,
        'identity_verified': identity.get('identity_independently_verified') is True,
        'scenario_verified': geometry_passed, 'strict_joint_passed': not reasons,
        'failure_reasons': list(dict.fromkeys(reasons)),
        'coverage_percent': 100. * coverage if finite(coverage) else None,
        'track_losses': len(episodes) if report else None,
        'unplanned_losses': len(unplanned) if report else None,
        'planned_losses': len(episodes) - len(unplanned) if report else None,
        'recovery_episodes': episodes,
        'unplanned_recovery_mean_s': recovered['mean'], 'unplanned_recovery_max_s': recovered['max'],
        'unplanned_recovery_censored_count': sum(item['censored'] for item in unplanned) if report else None,
        'recovery_timeout_count': sum(item['recovery_timeout'] for item in episodes) if report else None,
        'planned_recovery_mean_s': planned['mean'], 'planned_recovery_max_s': planned['max'],
        'planned_occlusion_recoveries_s': [item.get('confirmed_recovery_s') for item in report.get('occlusions', [])],
        'wrong_identity_observations': identity.get('wrong_identity_observations'),
        'scorable_identity_switches': identity.get('scorable_identity_switches'),
        'identity_scorable_fraction': scorable / total_identity if finite(total_identity) and total_identity > 0 and finite(scorable) else None,
        'post_identity_frames': identity.get('phase_counts', {}).get('post', {}).get('tracked_vehicle'),
        'identity_phase_counts': identity.get('phase_counts'),
        'identity_reason_counts': identity.get('identity_reason_counts'),
        'scene_requests': services, 'scene_request_failures': services['failures'] if services['total'] else None,
        'ulog_safety': safety, 'safety_event_observations': sum(safety.values()) if safety is not None else None,
        'px4_initial_parameter_sha256': px4_parameters['initial_parameter_sha256'] if px4_parameters else None,
        'ulog_sha256': digest(trial / 'flight.ulg') if (trial / 'flight.ulg').is_file() else None,
        'integrity': integrity, 'geometry_evidence': geometry,
        'association_frames': len(associations), 'association_frame_integrity': frame_integrity,
        'timing_all_recorded_associations': timing,
        'interventions': supervisor.get('interventions'),
        'safe_to_continue': bool(processes_finished and report.get('landed') and report.get('disarmed')
            and supervisor.get('landed_disarmed_before_shutdown') and not supervisor.get('interventions')
            and not report.get('failsafe_observed') and safety is not None and not any(safety.values())
            and not identity.get('wrong_identity_observations') and integrity['passed'] and px4_parameters is not None),
        'input_sha256': {name: digest(trial / name) for name in (
            'report.json', 'identity_report.json', 'supervisor.json', 'runtime_parameters.json',
            'implementation_snapshot.json', 'association.jsonl') if (trial / name).is_file()},
        'audit_script_sha256': digest(Path(__file__)),
    }
    for key in ('track_mean_abs_pixel_error', 'track_p95_abs_pixel_error',
                'final_home_horizontal_error_m', 'drone_follow_travel_m', 'wall_duration_s'):
        row[key] = report.get(key)
    for field, stats in timing.items():
        for suffix in ('mean', 'p95'):
            row[field[:-2] + '_' + suffix + '_s'] = stats[suffix]
    write_json(trial / 'batch_audit.json', row)
    return row


def group_summary(plan, rows):
    attempted = [row for row in rows if row.get('attempted')]
    count = len(attempted)
    episodes = [episode for row in attempted for episode in row.get('recovery_episodes', [])
                if not episode['planned_occlusion']]
    return {
        'planned': len(plan), 'attempted': count, 'completed': sum(row.get('completed', False) for row in attempted),
        'not_launched': len(plan) - count,
        'task_passed': sum(row.get('task_passed', False) for row in attempted),
        'identity_verified': sum(row.get('identity_verified', False) for row in attempted),
        'strict_joint_passed': sum(row.get('strict_joint_passed', False) for row in attempted),
        'task_success_rate': sum(row.get('task_passed', False) for row in attempted) / count if count else None,
        'strict_success_rate': sum(row.get('strict_joint_passed', False) for row in attempted) / count if count else None,
        'success_denominator': 'all attempted runs, including failures; unlaunched runs shown separately',
        'metrics': {name: distribution((row.get(name) for row in attempted), worst) for name, worst in METRICS.items()},
        'pooled_unplanned_recovery': {**distribution(episode.get('duration_s') for episode in episodes),
            'total_episodes': len(episodes), 'censored_episodes': sum(episode['censored'] for episode in episodes),
            'timeout_episodes': sum(episode['recovery_timeout'] for episode in episodes),
            'censor_lower_bounds_s': [episode['censor_lower_bound_s'] for episode in episodes if episode['censored']]},
        'failure_reason_counts': dict(Counter(reason for row in attempted for reason in row.get('failure_reasons', []))),
        'safety_evidence_missing_runs': sum(row.get('ulog_safety') is None for row in attempted),
        'wrong_identity_total': sum(row.get('wrong_identity_observations') or 0 for row in attempted),
        'identity_evidence_missing_runs': sum(row.get('wrong_identity_observations') is None for row in attempted),
    }


def format_number(value):
    return 'N/A' if value is None else f'{value:.3f}'


def markdown_report(summary):
    backend = 'OpenVINO FP32 CPU' if summary.get('detector_backend') == 'openvino' else 'PyTorch CPU'
    lines = ['# Two-Scenario Frozen Repeat Report', '',
             '## Protocol', '',
             'Independent simulator restart for every attempted trial; no failed run is replaced. '
             f'Frozen YOLO11s/{backend} parameters and 10-second blind-motion limit are unchanged. '
             'Both scenarios use red distractors and a curbside parked car.', '',
             'Coverage is time-weighted onboard target confirmation, not mAP or independently verified identity accuracy. '
             'Identity uses exclusive_projection_v2 with unchanged criteria. Unscorable frames are not counted as correct.', '',
             'Strict pass requires task, independent identity, completed traffic maneuver, autonomous landing/disarming, '
             'complete successful native service receipts, ULog safety evidence and frozen source/parameter integrity.', '',
             '| Scenario | Planned | Attempted | Completed | Task Pass | Identity Pass | Strict Pass | Unlaunched |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for name, group in summary['groups'].items():
        lines.append(f"| {name} | {group['planned']} | {group['attempted']} | {group['completed']} | "
                     f"{group['task_passed']}/{group['attempted']} | {group['identity_verified']}/{group['attempted']} | "
                     f"{group['strict_joint_passed']}/{group['attempted']} | {group['not_launched']} |")
    for name, group in summary['groups'].items():
        lines += ['', '## ' + name, '', '| Metric | Available Trials | Mean | Sample SD | Worst |',
                  '|---|---:|---:|---:|---:|']
        for metric, stats in group['metrics'].items():
            lines.append(f"| {metric} | {stats['count']} | {format_number(stats['mean'])} | "
                         f"{format_number(stats['sample_std'])} | {format_number(stats['worst'])} |")
        pooled = group['pooled_unplanned_recovery']
        lines += ['', f"Unplanned recovery episodes: {pooled['total_episodes']}; recovered: {pooled['count']}; "
                  f"censored: {pooled['censored_episodes']}; timeout: {pooled['timeout_episodes']}. "
                  f"Recovered-only pooled mean: {format_number(pooled['mean'])} s, "
                  f"sample SD: {format_number(pooled['sample_std'])} s, worst: {format_number(pooled['max'])} s. "
                  f"Censor lower bounds: {pooled['censor_lower_bounds_s']}.", '', 'Failure reasons:', '']
        lines += ['- ' + reason + ': ' + str(count) for reason, count in group['failure_reason_counts'].items()] or ['- None recorded.']
    lines += ['', '## Every Planned Trial', '',
              '| Trial | State | Task | Identity | Strict | Coverage % | Unplanned Losses | Mean Error px | Post Identity Frames |',
              '|---|---|---|---|---|---:|---:|---:|---:|']
    for row in summary['trials']:
        lines.append(f"| [{row['name']}]({row['name']}/) | {row.get('attempt_state', 'not_launched')} | "
                     f"{row.get('task_passed', 'N/A')} | {row.get('identity_verified', 'N/A')} | "
                     f"{row.get('strict_joint_passed', 'N/A')} | {format_number(row.get('coverage_percent'))} | "
                     f"{row.get('unplanned_losses', 'N/A')} | {format_number(row.get('track_mean_abs_pixel_error'))} | "
                     f"{row.get('post_identity_frames', 'N/A')} |")
    lines += ['', '## Interpretation And Limits', '']
    lines += ['- ' + value for value in summary['limitations']]
    lines += ['', 'Machine-readable evidence: [SUMMARY.json](SUMMARY.json), [trials.csv](trials.csv), '
              'per-trial `batch_audit.json`, raw logs, identity projections, flight ULogs and frozen source hashes.', '']
    return '\n'.join(lines)


def plot_summary(directory, rows):
    os.environ['MPLCONFIGDIR'] = str(Path(directory).resolve() / '.matplotlib')
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
    for group, color in (('left_overtaking', '#177E89'), ('lane_change', '#C84B31')):
        relevant = [row for row in rows if row['group'] == group and row.get('attempted')]
        for ax, metric, label in zip(axes.flat,
                ('coverage_percent', 'unplanned_losses', 'track_mean_abs_pixel_error', 'target_publish_age_p95_s'),
                ('Confirmed Coverage (%)', 'Unplanned Track Losses', 'Mean Pixel Error (px)', 'Pipeline Age p95 (s)')):
            points = [(index, row.get(metric)) for index, row in enumerate(relevant, 1) if finite(row.get(metric))]
            if points:
                ax.plot([item[0] for item in points], [item[1] for item in points], 'o-', label=group, color=color)
            ax.set(title=label, xlabel='Attempt Within Scenario')
            ax.grid(alpha=.2)
            if ax.lines:
                ax.legend()
    fig.savefig(directory / 'summary.png', dpi=160)
    plt.close(fig)
    return True


def summarize_batch(batchdir):
    directory = Path(batchdir)
    plan = read_json(directory / 'plan.json', [])
    rows = []
    for trial in plan:
        attempt = read_json(directory / 'attempts' / (trial['name'] + '.json'), {})
        row = read_json(directory / trial['name'] / 'batch_audit.json', {})
        if not attempt:
            row = {'name': trial['name'], 'group': trial['group'], 'attempted': False,
                   'traffic_scenario': trial['traffic_scenario'], 'attempt_state': 'not_launched'}
        elif not row:
            row = {'name': trial['name'], 'group': trial['group'], 'attempted': True,
                   'traffic_scenario': trial['traffic_scenario'], 'completed': False,
                   'task_passed': False, 'identity_verified': False, 'strict_joint_passed': False,
                   'failure_reasons': ['audit_not_available'], 'safe_to_continue': False}
        row['attempt_state'] = attempt.get('state', 'not_launched')
        row['returncode'] = attempt.get('returncode')
        if attempt and attempt.get('state') != 'completed':
            row['completed'] = False
            row['strict_joint_passed'] = False
            row['failure_reasons'] = list(dict.fromkeys(row.get('failure_reasons', [])
                + ['attempt_not_completed:' + str(attempt.get('state'))]))
        rows.append(row)
    groups = {group: group_summary([item for item in plan if item['group'] == group],
                                   [row for row in rows if row['group'] == group])
              for group in dict.fromkeys(item['group'] for item in plan)}
    reference, parameter_rows = None, []
    for row in rows:
        if not row.get('attempted'):
            continue
        observed = read_json(directory / row['name'] / 'px4_recorded_parameters.json', {})
        values = observed.get('initial_parameters')
        if values is None:
            parameter_rows.append({'name': row['name'], 'available': False})
            continue
        if reference is None:
            reference = values
        parameter_rows.append({'name': row['name'], 'available': True,
                               'initial_parameter_sha256': observed.get('initial_parameter_sha256'),
                               **parameter_differences(reference, values),
                               'parameter_updates_after_header': observed.get('changed_parameters', [])})
    write_json(directory / 'px4_parameter_audit.json', {
        'trials': parameter_rows, 'available_logs': sum(row['available'] for row in parameter_rows),
        'comparison_reference': next((row['name'] for row in parameter_rows if row['available']), None),
        'limitations': ['Frozen launch files do not imply identical runtime calibration or flight counters.',
                       'Initial ULog values are the used parameter set; unrecorded defaults are not verified.',
                       'Startup parameter updates are not automatically in-flight updates.']})
    protocol = read_json(directory / 'batch_protocol.json', {})
    summary = {'planned': len(plan), 'attempted': sum(row.get('attempted', False) for row in rows),
               'detector_backend': protocol.get('detector_backend', 'torch'),
               'groups': groups, 'trials': rows, 'audit_script_sha256': digest(Path(__file__)),
               'batch_complete': bool(plan) and all(row.get('attempt_state') == 'completed' and row.get('completed') for row in rows),
               'px4_parameter_audit': {'available_logs': sum(row['available'] for row in parameter_rows),
                   'runs_with_bookkeeping_differences': sum(bool(row.get('bookkeeping_differences')) for row in parameter_rows),
                   'runs_with_calibration_differences': sum(bool(row.get('calibration_differences')) for row in parameter_rows),
                   'runs_with_other_parameter_differences': sum(bool(row.get('other_parameter_differences')) for row in parameter_rows)},
               'limitations': [
                   'All attempted failures remain in success denominators; unlaunched trials are explicitly incomplete, not successes or hidden failures.',
                   'Metric count is the number with available evidence; missing metrics are not imputed as zero. Sample SD uses n-1 and is unavailable for n<2.',
                   'Group timing means summarize per-trial means, not pooled frames. Per-trial timing covers all recorded associations, not only TRACK.',
                   'No-loss trials have no recovery duration, not a zero-second recovery. Unrecovered episodes remain censored and are listed separately.',
                   'Task recovery and inference durations are wall seconds; traffic trajectory phases and identity observer latency are simulation seconds.',
                   'Zero observed wrong identities applies only to scorable projected-volume evidence; ambiguous and missing-truth frames are not proof of correctness.',
                   'Fixed-scene repeats measure runtime repeatability, not random-scene, real-flight or weather generalization.',
                   'ULog safety fields are observation counts, not necessarily distinct incidents; zero counts do not certify absence of every collision.',
                   'The two traffic scenarios have different geometry; their difference is not an isolated algorithm ablation.',
                   'Historical pilot runs are excluded from the repeat denominator.',
                   'Runtime PX4 calibration and flight counters may vary despite frozen launch settings; inspect px4_parameter_audit.json before attributing changes to control tuning.',
               ]}
    write_json(directory / 'SUMMARY.json', summary)
    columns = ['name', 'group', 'attempted', 'attempt_state', 'completed', 'returncode', *METRICS, 'failure_reasons']
    with (directory / 'trials.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, 'failure_reasons': '; '.join(row.get('failure_reasons', []))})
    (directory / 'FINAL_REPORT.md').write_text(markdown_report(summary))
    plot_summary(directory, rows)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch-dir', type=Path, required=True)
    parser.add_argument('--audit-existing', action='store_true')
    args = parser.parse_args()
    if args.audit_existing:
        for scenario in read_json(args.batch_dir / 'plan.json', []):
            trial = args.batch_dir / scenario['name']
            if (trial / 'supervisor.json').is_file():
                audit_trial(ROOT, trial, scenario)
    summary = summarize_batch(args.batch_dir)
    print(json.dumps({'planned': summary['planned'], 'attempted': summary['attempted'],
                      'batch_complete': summary['batch_complete'],
                      'groups': {key: {'strict': value['strict_joint_passed'], 'attempted': value['attempted']}
                                 for key, value in summary['groups'].items()}}))


if __name__ == '__main__':
    main()
