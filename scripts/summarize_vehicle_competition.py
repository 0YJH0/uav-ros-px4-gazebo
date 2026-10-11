#!/usr/bin/env python3
"""Report complete and missing A/B pairs without discarding failed attempts."""

import argparse
import json
from pathlib import Path
import statistics

from vehicle_experiment_study import load_json, write_json


def paired_summary(rows, plan):
    output = {}
    for metric in ('visibility', 'after_last_overlap_confirmation_wall_s',
                   'unplanned_losses', 'processing_mean_s', 'mean_pixel_error'):
        pairs = []
        for pair in sorted({trial['pair'] for trial in plan}):
            members = {row['group']: row for row in rows if row.get('pair') == pair}
            a, b = members.get('baseline', {}).get(metric), members.get('competition', {}).get(metric)
            if a is not None and b is not None:
                pairs.append({'pair': pair, 'baseline': a, 'competition': b, 'delta': b - a})
        deltas = [item['delta'] for item in pairs]
        output[metric] = {'n': len(pairs), 'missing_pairs': len(plan) // 2 - len(pairs),
                          'delta_definition': 'competition minus baseline',
                          'mean_delta': statistics.mean(deltas) if deltas else None,
                          'sample_std_delta': statistics.stdev(deltas) if len(deltas) > 1 else None,
                          'min_delta': min(deltas) if deltas else None,
                          'max_delta': max(deltas) if deltas else None, 'pairs': pairs}
    return {'paired_metrics': output,
            'attempted': len(rows), 'planned': len(plan),
            'wrong_identity_observations': sum(row.get('wrong_identity_observations') or 0 for row in rows),
            'identity_reports_missing': sum(not row.get('identity_report_available') for row in rows),
            'safety_event_trials': sum(bool(row.get('safety_event')) for row in rows),
            'limits': ['Failed trials remain in all summaries. Missing metrics are counted, not imputed zero.',
                       'Small deterministic restart sample; no inference about unseen roads or vehicles.',
                       'Coverage improvement alone cannot promote a version with worse identity or safety.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('study', type=Path)
    args = parser.parse_args()
    summary = load_json(args.study / 'study_summary.json')
    plan = load_json(args.study / 'plan.json')
    if not summary or not plan:
        raise ValueError('Missing A/B plan or summary.')
    report = paired_summary(summary['trials'], plan)
    write_json(args.study / 'paired_comparison.json', report)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
