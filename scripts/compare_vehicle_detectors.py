#!/usr/bin/env python3
"""Compare local YOLO weights on exactly paired raw validation frames."""

import argparse
import hashlib
import json
from pathlib import Path
import time

import cv2
import torch
from ultralytics import YOLO


def raw_entries(directory, start, end):
    entries = [json.loads(line) for line in (directory / 'image_manifest.jsonl').read_text().splitlines()]
    return [entry for entry in entries if entry.get('raw_image')
            and start <= entry['wall_s'] <= end]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('--models', nargs='+', type=Path, default=[Path('yolo11n.pt'), Path('yolo11s.pt')])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--start', type=float, default=0)
    parser.add_argument('--end', type=float, default=float('inf'))
    parser.add_argument('--cpu-threads', type=int)
    args = parser.parse_args()
    if args.cpu_threads is not None and args.cpu_threads < 1:
        parser.error('--cpu-threads must be positive')
    output = args.output or args.directory / 'offline_detector_comparison.json'
    if output.exists():
        raise RuntimeError('Refusing to overwrite existing evidence.')
    if not all(path.is_file() for path in args.models):
        raise RuntimeError('All model weights must exist locally; this tool never downloads weights.')
    entries = raw_entries(args.directory, args.start, args.end)
    if not entries:
        raise RuntimeError('No timestamp-paired raw frames in the requested interval.')
    rows, models = [], []
    for path in args.models:
        model = YOLO(str(path), task='detect')
        classes = [key for key, value in model.names.items() if value == 'car']
        if not classes:
            raise RuntimeError(f'{path} has no car class.')
        models.append({'path': str(path.resolve()), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        for index, entry in enumerate(entries):
            pixels = cv2.imread(str(args.directory / entry['raw_image']))
            if pixels is None:
                raise RuntimeError(f"Unreadable raw image: {entry['raw_image']}")
            if args.cpu_threads is not None:
                torch.set_num_threads(args.cpu_threads)
            started = time.monotonic()
            result = model.predict(pixels, classes=classes, conf=0.1, imgsz=960,
                                   device='cpu', verbose=False)[0]
            rows.append({'model': str(path), 'raw_image': entry['raw_image'],
                         'stamp': entry['stamp'], 'wall_s': entry['wall_s'],
                         'processing_s': time.monotonic() - started, 'warmup_frame': index == 0,
                         'cpu_threads_actual': torch.get_num_threads(),
                         'cars': [{'confidence': float(score), 'bbox': box.tolist()}
                                  for box, score in zip(result.boxes.xyxy, result.boxes.conf)]})
    report = {'models': models, 'image_size': 960, 'confidence_threshold': 0.1,
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'raw_sha256': {entry['raw_image']: hashlib.sha256(
                  (args.directory / entry['raw_image']).read_bytes()).hexdigest() for entry in entries},
              'cpu_threads_requested': args.cpu_threads,
              'timing_note': 'First prediction is cold and can reset CPU threads during backend initialization; '
                             'exclude warmup_frame and check cpu_threads_actual for comparisons.',
              'limitation': 'No independent ground-truth labels. Candidate counts are not recall, '
                            'same-vehicle identity, live latency or flight success. Run after the '
                            'flight, not concurrently with its detector.', 'frames': rows}
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'Compared {len(entries)} raw frames across {len(models)} models: {output}')


if __name__ == '__main__':
    main()
