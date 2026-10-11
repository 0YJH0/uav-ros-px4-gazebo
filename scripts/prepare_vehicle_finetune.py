#!/usr/bin/env python3
"""Build a leakage-checked weak-label review set, never silently start training."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil

import cv2
import yaml

from vehicle_crossing_validation import iou


def yolo_box(box, width, height):
    x1, y1, x2, y2 = box
    if not (0 <= x1 < x2 <= width and 0 <= y1 < y2 <= height):
        raise ValueError('Invalid or unclipped annotation.')
    return [(x1 + x2) / (2 * width), (y1 + y2) / (2 * height),
            (x2 - x1) / width, (y2 - y1) / height]


def write_review_template(directory):
    path = directory / 'annotation_approval.json'
    if path.exists():
        raise ValueError('Never overwrite annotation review decisions.')
    manifest_path = directory / 'review_manifest.json'
    manifest = json.loads(manifest_path.read_text())
    approval = {'training_authorized': False,
                'review_manifest_sha256': hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                'reviewer': '', 'images': {row['image']: {
                    'status': 'pending',
                    'label_sha256': hashlib.sha256((directory / row['label']).read_bytes()).hexdigest()}
                    for row in manifest['rows']}}
    path.write_text(json.dumps(approval, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--study', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--approval-template-only', action='store_true')
    args = parser.parse_args()
    if args.approval_template_only:
        write_review_template(args.output)
        return
    if args.study is None:
        parser.error('--study is required when preparing a new dataset.')
    trials = sorted(path for path in args.study.glob('crossing_*')
                    if path.is_dir() and (path / 'crossing_image_manifest.jsonl').is_file())
    if len(trials) < 3:
        raise ValueError('At least three independent trial directories are required.')
    if args.output.exists():
        raise ValueError('Use a new directory; never overwrite an annotation review.')
    args.output.mkdir(parents=True)
    # Validation holds out entire restarts; future A/B images are excluded entirely.
    validation = {path.name for path in trials[-max(1, len(trials) // 5):]}
    seen, rows, dropped = {}, [], Counter()
    for trial in trials:
        split = 'val' if trial.name in validation else 'train'
        for line in (trial / 'crossing_image_manifest.jsonl').read_text().splitlines():
            evidence = json.loads(line)
            source = trial / evidence['image']
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if digest in seen:
                dropped['duplicate_image'] += 1
                continue
            seen[digest] = split
            pixels = cv2.imread(str(source))
            if pixels is None:
                raise ValueError(f'Unreadable image: {source}')
            height, width = pixels.shape[:2]
            boxes = {name: box for name, box in evidence.get('projected_boxes', {}).items() if box is not None}
            if not boxes or evidence.get('pose_age_sim_s', float('inf')) > .15:
                dropped['missing_or_occluded_projection'] += 1
                continue
            overlap = any(iou(a, b) > .1 for index, a in enumerate(boxes.values())
                          for b in list(boxes.values())[index + 1:])
            truncated = any(box[0] <= 1 or box[1] <= 1 or box[2] >= width - 1 or box[3] >= height - 1
                            for box in boxes.values())
            name = f'{trial.name}_{source.stem}'
            image = args.output / 'images' / split / (name + '.png')
            label = args.output / 'labels' / split / (name + '.txt')
            image.parent.mkdir(parents=True, exist_ok=True)
            label.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, image)
            label.write_text(''.join('0 ' + ' '.join(f'{value:.8f}' for value in yolo_box(box, width, height))
                                     + '\n' for box in boxes.values()))
            rows.append({'image': str(image.relative_to(args.output)), 'label': str(label.relative_to(args.output)),
                         'source': str(source.resolve()), 'image_sha256': digest, 'split': split,
                         'trial': trial.name, 'stamp': evidence['stamp'], 'projected_boxes': boxes,
                         'requires_manual_review': True, 'overlap': overlap, 'truncated': truncated,
                         'label_source': 'simulation_mesh_projection_weak_label',
                         'review_status': 'pending', 'car_class': 0})
    if not rows:
        raise ValueError('No raw frames with matched projections; no training dataset produced.')
    manifest = {'train_trials': [path.name for path in trials if path.name not in validation],
                'val_trials': sorted(validation), 'test_trials': [],
                'counts': dict(Counter(row['split'] for row in rows)), 'dropped': dict(dropped),
                'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'training_authorized': False, 'rows': rows,
                'limitations': ['Projected 3D bounds are weak labels, not verified visible-body annotations.',
                                'All annotations, especially overlaps/truncation, require review before training.',
                                'Test set must use new restarts, not these training/validation images.',
                                'Single class car becomes class 0; runtime target class must be resolved by name.']}
    (args.output / 'review_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    (args.output / 'data.yaml').write_text(yaml.safe_dump({
        'path': str(args.output.resolve()), 'train': 'images/train', 'val': 'images/val',
        'names': {0: 'car'}}, sort_keys=False))
    write_review_template(args.output)
    print(json.dumps({'counts': manifest['counts'], 'dropped': manifest['dropped'],
                      'training_authorized': False, 'output': str(args.output)}))


if __name__ == '__main__':
    main()
