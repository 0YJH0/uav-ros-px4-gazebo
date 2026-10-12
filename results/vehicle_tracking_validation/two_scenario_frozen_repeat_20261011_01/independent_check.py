#!/usr/bin/env python3
"""Recompute the completed study's counts and evidence without rewriting verdicts."""

from collections import Counter
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys

os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
BATCH = Path(__file__).resolve().parent
ROOT = BATCH.parents[2]
sys.path.insert(0, str(BATCH / 'frozen_files/scripts'))


def read(path):
    return json.loads(path.read_text())


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def sha(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def numeric(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def close(actual, expected):
    if expected is None or actual is None:
        return expected is None and actual is None
    return math.isclose(float(actual), float(expected), rel_tol=1e-11, abs_tol=1e-11)


def stats(values, worst):
    values = sorted(float(value) for value in values if numeric(value))
    if not values:
        return {'count': 0, 'mean': None, 'sample_std': None, 'min': None,
                'max': None, 'p95': None, 'worst': None}
    rank = .95 * (len(values) - 1)
    low, high = math.floor(rank), math.ceil(rank)
    return {'count': len(values), 'mean': statistics.mean(values),
            'sample_std': statistics.stdev(values) if len(values) > 1 else None,
            'min': values[0], 'max': values[-1],
            'p95': values[low] + (values[high] - values[low]) * (rank - low),
            'worst': values[0] if worst == 'min' else values[-1]}


def main():
    plan = read(BATCH / 'plan.json')
    summary = read(BATCH / 'SUMMARY.json')
    status = read(BATCH / 'study_status.json')
    if not status.get('completed') or len(plan) != 20:
        raise RuntimeError('Wait for all twenty planned attempts to finish.')
    frozen = read(BATCH / 'freeze_manifest.json')
    protocol = read(BATCH / 'batch_protocol.json')
    markdown = (BATCH / 'FINAL_REPORT.md').read_text()
    checks, mismatches = {}, []

    def check(name, condition):
        checks[name] = bool(condition)
        if not condition:
            mismatches.append(name)

    check('twenty_unique_plan_entries', len({row['name'] for row in plan}) == 20)
    check('two_groups_ten_each', Counter(row['group'] for row in plan)
          == {'left_overtaking': 10, 'lane_change': 10})
    check('exactly_twenty_attempt_ledgers', len(list((BATCH / 'attempts').glob('*.json'))) == 20)
    check('summary_complete_twenty', summary.get('batch_complete') and summary.get('attempted') == 20)
    check('freeze_manifest_unchanged', sha(BATCH / 'freeze_manifest.json') == protocol['freeze_manifest_sha256'])
    check('plan_unchanged', sha(BATCH / 'plan.json') == protocol['plan_sha256'])
    source_errors = []
    for relative, expected in frozen['source_sha256'].items():
        archived = BATCH / 'frozen_files' / relative
        if not archived.is_file() or sha(archived) != expected:
            source_errors.append(relative)
    check('shared_frozen_sources_valid', not source_errors)
    model = Path(protocol['model_path'])
    check('live_model_matches_frozen_model', sha(model) == protocol['model_sha256'])
    from pyulog import ULog
    import numpy as np
    from vehicle_crossing_validation import identity_summary

    trials, ulog_hashes, previous_finished = [], [], None
    summary_rows = {row['name']: row for row in summary['trials']}
    for item in plan:
        name = item['name']
        trial = BATCH / name
        ledger = read(BATCH / 'attempts' / (name + '.json'))
        audit = read(trial / 'batch_audit.json')
        report = read(trial / 'report.json')
        identity = read(trial / 'identity_report.json')
        snapshot = read(trial / 'implementation_snapshot.json')
        archive = read(trial / 'archive_manifest.json')
        check(name + ':completed_ledger', ledger.get('state') == 'completed' and ledger.get('name') == name)
        check(name + ':ledger_freeze_hash', ledger.get('freeze_manifest_sha256') == protocol['freeze_manifest_sha256'])
        check(name + ':attempt_time_order', ledger['started_utc'] <= ledger['finished_utc']
              and (previous_finished is None or ledger['started_utc'] >= previous_finished))
        previous_finished = ledger['finished_utc']
        check(name + ':summary_matches_trial_audit', all(summary_rows[name].get(key) == value
              for key, value in audit.items()))
        check(name + ':strict_verdict_matches_reasons', audit['strict_joint_passed'] == (not audit['failure_reasons']))
        check(name + ':coverage_from_raw_report', close(audit['coverage_percent'], 100 * report['follow_time_visible_fraction']))
        check(name + ':task_success_from_raw_report', audit['task_passed'] == report['passed'])
        check(name + ':archive_snapshot_hash', sha(trial / 'implementation_snapshot.json') == archive['implementation_snapshot_sha256'])
        check(name + ':model_provenance', snapshot['model_sha256'] == protocol['model_sha256']
              and snapshot['model_path'] == protocol['model_path'])
        check(name + ':all_snapshot_sources_frozen', all(frozen['source_sha256'].get(relative) == expected
              and sha(trial / 'executed_sources' / relative) == expected for relative, expected in snapshot['source_sha256'].items()))
        for filename, expected in audit['input_sha256'].items():
            check(name + ':raw_unchanged:' + filename, sha(trial / filename) == expected)
        native, missing_sequences = [], {}
        for filename, client in (('scene_service.jsonl', 'scene'), ('traffic_service.jsonl', 'traffic')):
            rows = lines(trial / filename)
            check(name + ':valid_client:' + client, bool(rows) and all(row.get('client') == client for row in rows))
            numbers = [row['sequence'] for row in rows]
            missing = sorted(set(range(1, max(numbers) + 1)) - set(numbers))
            missing_sequences[client] = missing
            check(name + ':missing_sequence_accounting:' + client,
                  audit['scene_requests']['client_sequences'][client]['missing'] == missing)
            check(name + ':service_log_hash:' + client, sha(trial / filename) == audit['scene_requests']['files'][filename]['sha256'])
            native += rows
        native_failed = sum(not (row.get('binding_result') is True and row.get('response_data') is True) for row in native)
        check(name + ':native_failure_count', native_failed == audit['scene_requests']['failures'])
        check(name + ':native_request_count', len(native) == audit['scene_requests']['total'])
        identity_rows = lines(trial / 'identity_observations.jsonl')
        reidentified = identity_summary(identity_rows, lines(trial / 'crossing_events.jsonl'),
                                         identity['errors'], item['traffic_scenario'], 'red')
        check(name + ':raw_identity_counts_and_maneuver', all(reidentified.get(key) == identity.get(key)
              for key in ('identity_independently_verified', 'wrong_identity_observations', 'phase_counts',
                          'scorable_identity_switches', 'scorable_observations', 'observations_total',
                          'traffic_started', 'traffic_completed', 'overtaking_observed', 'lane_change')))
        associations = lines(trial / 'association.jsonl')
        for field in ('processing_s', 'target_publish_age_s', 'queue_wait_s', 'full_frame_yolo_s'):
            values = [row.get('detector', {}).get(field) if field == 'full_frame_yolo_s' else row.get(field)
                      for row in associations]
            measured = stats(values, 'max')
            check(name + ':timing:' + field, all(close(measured[key], audit['timing_all_recorded_associations'][field][key])
                  for key in measured))
        ulog_hash = sha(trial / 'flight.ulg')
        ulog_hashes.append(ulog_hash)
        check(name + ':ulog_hash_matches_archive', ulog_hash == archive['ulog_sha256'] == audit['ulog_sha256'])
        ulog = ULog(str(trial / 'flight.ulg'), message_name_filter_list=['vehicle_status', 'failsafe_flags'])
        statuses = ulog.get_dataset('vehicle_status').data
        flags = ulog.get_dataset('failsafe_flags').data
        lookup = np.searchsorted(statuses['timestamp'], flags['timestamp'], side='right') - 1
        valid = lookup >= 0
        safe_lookup = np.maximum(lookup, 0)
        armed = statuses['arming_state'] == 2
        offboard_armed = valid & armed[safe_lookup] & (statuses['nav_state'][safe_lookup] == 14)
        independently_safety = {
            'armed_failsafe_observations': int(np.count_nonzero(armed & (statuses['failsafe'] != 0))),
            'armed_offboard_lost_observations': int(np.count_nonzero(offboard_armed & (flags['offboard_control_signal_lost'] != 0))),
            'ulog_dropout_events': len(ulog.dropouts),
        }
        check(name + ':independent_ulog_safety', independently_safety == audit['ulog_safety'])
        trials.append({'name': name, 'group': item['group'], 'strict_joint_passed': audit['strict_joint_passed'],
                       'failure_reasons': audit['failure_reasons'], 'coverage_percent': audit['coverage_percent'],
                       'native_requests': len(native), 'native_failed_requests': native_failed,
                       'missing_service_sequences': missing_sequences, 'ulog_sha256': ulog_hash,
                       'ulog_safety': independently_safety,
                       'snapshot_source_files_checked': len(snapshot['source_sha256']),
                       'identity_phase_counts': reidentified['phase_counts']})
    check('twenty_distinct_archived_ulogs', len(set(ulog_hashes)) == 20)

    minimum_metrics = {'task_passed', 'strict_joint_passed', 'identity_verified', 'coverage_percent',
                       'drone_follow_travel_m', 'identity_scorable_fraction', 'post_identity_frames'}
    recomputed_groups = {}
    for group, recorded in summary['groups'].items():
        rows = [row for row in summary['trials'] if row['group'] == group]
        check(group + ':ten_actual_completed', len(rows) == 10 and all(row['attempted'] and row['completed'] for row in rows))
        metrics = {}
        for metric, recorded_stats in recorded['metrics'].items():
            recalculated = stats([row.get(metric) for row in rows], 'min' if metric in minimum_metrics else 'max')
            metrics[metric] = recalculated
            check(group + ':statistic:' + metric, all(close(recorded_stats[key], value) for key, value in recalculated.items()))
            def fmt(value):
                return 'N/A' if value is None else f'{value:.3f}'
            line = (f"| {metric} | {recalculated['count']} | {fmt(recalculated['mean'])} | "
                    f"{fmt(recalculated['sample_std'])} | {fmt(recalculated['worst'])} |")
            section = markdown.split('## ' + group + '\n', 1)[1].split('\n## ', 1)[0]
            check(group + ':markdown_metric:' + metric, line in section)
        task_count = sum(row['task_passed'] for row in rows)
        identity_count = sum(row['identity_verified'] for row in rows)
        strict_count = sum(row['strict_joint_passed'] for row in rows)
        check(group + ':pass_counts', (task_count, identity_count, strict_count)
              == (recorded['task_passed'], recorded['identity_verified'], recorded['strict_joint_passed']))
        check(group + ':markdown_pass_counts', f'| {group} | 10 | 10 | 10 | {task_count}/10 | {identity_count}/10 | {strict_count}/10 | 0 |' in markdown)
        check(group + ':success_rates', close(recorded['task_success_rate'], task_count / 10)
              and close(recorded['strict_success_rate'], strict_count / 10))
        recomputed_groups[group] = {'metrics': metrics, 'task_passed': task_count,
                                    'identity_verified': identity_count, 'strict_joint_passed': strict_count}
    with (BATCH / 'trials.csv').open() as stream:
        csv_rows = list(csv.DictReader(stream))
    check('csv_twenty_rows', len(csv_rows) == 20)
    for row in csv_rows:
        original = summary_rows[row['name']]
        check(row['name'] + ':csv_fields', all(value == ('' if original.get(key) is None else str(original.get(key)))
              for key, value in row.items() if key != 'failure_reasons')
              and row['failure_reasons'] == '; '.join(original['failure_reasons']))
    result = {'check_passed': not mismatches, 'checks_count': len(checks), 'mismatches': mismatches,
              'meaning': 'Report/evidence consistency check, not a replacement for frozen trial verdicts.',
              'planned_trials': len(plan), 'completed_trials': len(trials),
              'shared_frozen_files_checked': len(frozen['source_sha256']), 'source_archive_errors': source_errors,
              'total_native_requests_recorded': sum(row['native_requests'] for row in trials),
              'total_native_requests_failed': sum(row['native_failed_requests'] for row in trials),
              'total_missing_service_receipts': sum(len(numbers) for row in trials for numbers in row['missing_service_sequences'].values()),
              'groups_recomputed': recomputed_groups, 'trials': trials, 'checks': checks,
              'checker_sha256': sha(Path(__file__)),
              'input_sha256': {name: sha(BATCH / name) for name in ('SUMMARY.json', 'trials.csv', 'FINAL_REPORT.md',
                                                                  'plan.json', 'freeze_manifest.json', 'batch_protocol.json')},
              'limitations': ['This post-hoc check does not rewrite frozen criteria, failed runs or missing receipts.',
                              'Original identity rows are re-aggregated using the frozen v2 evaluator; no new identity thresholds are introduced.',
                              'Zero observed ULog events does not certify absence of every possible collision.',
                              'Unique ledgers, ordered nonoverlapping times and distinct ULogs support independent attempts; they are not proof of all external host activity.']}
    (BATCH / 'INDEPENDENT_CHECK.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({key: result[key] for key in ('check_passed', 'checks_count', 'mismatches',
                                                  'total_native_requests_recorded', 'total_native_requests_failed',
                                                  'total_missing_service_receipts')}))
    return 0 if result['check_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
