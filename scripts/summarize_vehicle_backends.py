#!/usr/bin/env python3
"""Aggregate matched backend runs, not correlated frame timings as independent trials."""

import argparse
import hashlib
import json
from pathlib import Path
import statistics


def summarize(paths):
    reports = [json.loads(path.read_text()) for path in paths]
    if not reports:
        raise ValueError('At least one report is required.')
    keys = ('weight_sha256', 'raw_sha256', 'script_sha256', 'input_shape', 'cpu_threads',
            'conf', 'nms_iou', 'precision', 'warmup_full_pipeline_frames', 'versions')
    if any(any(report.get(key) != reports[0].get(key) for key in keys) for report in reports):
        raise ValueError('Cannot combine different pixels, weights, settings or implementation.')
    if not reports[0].get('warmup_full_pipeline_frames'):
        raise ValueError('Complete-pipeline warmup is required.')
    engines = {}
    for name in ('torch', 'onnxruntime', 'openvino'):
        rows = [report['summary'][name] for report in reports]
        means = [row['total_mean_s'] for row in rows]
        engines[name] = {'runs': len(rows), 'mean_of_run_means_s': statistics.mean(means),
                         'sample_std_run_means_s': statistics.stdev(means) if len(means) > 1 else None,
                         'worst_run_mean_s': max(means), 'worst_run_p95_s': max(row['total_p95_s'] for row in rows),
                         'worst_observed_frame_s': max(row['total_max_s'] for row in rows),
                         'unmatched_boxes': sum(row['unmatched_boxes'] for row in rows),
                         'box_max_delta_px': max(row['box_max_delta_px'] for row in rows),
                         'confidence_max_delta': max(row['confidence_max_delta'] for row in rows),
                         'runs_detail': rows}
    return {'reports': [{'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
                        for path in paths], 'backend_order': [report['backend_order'] for report in reports],
            'distinct_raw_images': len(reports[0]['raw_sha256']), 'summary': engines,
            'settings': {key: reports[0][key] for key in keys if key != 'raw_sha256'},
            'limitations': ['Per-run sample standard deviation, not independent 414-scene confidence.',
                            'Box agreement is measured against Torch, not fully annotated detector mAP.',
                            'A faster backend has not yet been verified in the live ROS/flight loop.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('reports', nargs='+', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Never overwrite comparison evidence.')
    report = summarize(args.reports)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps(report['summary'], indent=2))


if __name__ == '__main__':
    main()
