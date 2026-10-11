#!/usr/bin/env python3
"""Fine-tune only reviewed annotations; keep candidate weights out of flight."""

import argparse
import hashlib
import json
import os
from pathlib import Path


def verify_review(dataset):
    manifest = json.loads((dataset / 'review_manifest.json').read_text())
    approval = json.loads((dataset / 'annotation_approval.json').read_text())
    if approval.get('review_manifest_sha256') != hashlib.sha256((dataset / 'review_manifest.json').read_bytes()).hexdigest():
        raise ValueError('Approval refers to another review manifest.')
    if not approval.get('training_authorized'):
        raise ValueError('Annotation review has not authorized training.')
    reviewed = approval.get('images', {})
    if set(reviewed) != {row['image'] for row in manifest['rows']}:
        raise ValueError('Every annotation needs an explicit approved/rejected decision.')
    for row in manifest['rows']:
        item = reviewed[row['image']]
        if item.get('status') != 'approved':
            raise ValueError('Remove rejected annotations into a new, reviewed dataset before training.')
        if hashlib.sha256((dataset / row['image']).read_bytes()).hexdigest() != row['image_sha256']:
            raise ValueError('Reviewed raw pixels changed.')
        if hashlib.sha256((dataset / row['label']).read_bytes()).hexdigest() != item.get('label_sha256'):
            raise ValueError('Reviewed annotation changed.')
    train = {row['trial'] for row in manifest['rows'] if row['split'] == 'train'}
    val = {row['trial'] for row in manifest['rows'] if row['split'] == 'val'}
    train_pixels = {row['image_sha256'] for row in manifest['rows'] if row['split'] == 'train'}
    val_pixels = {row['image_sha256'] for row in manifest['rows'] if row['split'] == 'val'}
    if not train or not val or train & val:
        raise ValueError('Independent train/validation trial split required.')
    if train_pixels & val_pixels:
        raise ValueError('Duplicate pixels across train/validation splits.')
    return manifest, approval


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=Path, required=True)
    parser.add_argument('--model-path', type=Path, default=Path('yolo11s.pt'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--epochs', type=int, default=20)
    parser.add_argument('--cpu-threads', type=int, default=16)
    args = parser.parse_args()
    if args.output.exists() or not args.model_path.is_file() or args.epochs < 1 or args.cpu_threads < 1:
        raise ValueError('New output, local weights and positive epochs/threads required.')
    manifest, approval = verify_review(args.dataset)
    args.output.mkdir(parents=True)
    os.environ['YOLO_CONFIG_DIR'] = str(args.output.resolve() / 'ultralytics_config')
    os.environ['YOLO_AUTOINSTALL'] = 'false'
    import torch
    from ultralytics import YOLO
    torch.set_num_threads(args.cpu_threads)
    protocol = {'dataset': str(args.dataset.resolve()), 'epochs': args.epochs, 'seed': 42,
                'weight_sha256': hashlib.sha256(args.model_path.read_bytes()).hexdigest(),
                'review_sha256': hashlib.sha256((args.dataset / 'annotation_approval.json').read_bytes()).hexdigest(),
                'cpu_threads': args.cpu_threads, 'candidate_only': True,
                'test_trials': manifest['test_trials'],
                'limits': 'No automatic flight promotion. Independent test frames and new closed-loop A/B are still required.'}
    (args.output / 'training_protocol.json').write_text(json.dumps(protocol, indent=2) + '\n')
    YOLO(str(args.model_path)).train(data=str((args.dataset / 'data.yaml').resolve()),
        device='cpu', epochs=args.epochs, batch=2, imgsz=960, workers=0,
        seed=42, deterministic=True, amp=False, pretrained=True, freeze=10,
        project=str(args.output.resolve()), name='training', exist_ok=False, patience=0,
        plots=True, cache=False, val=True)


if __name__ == '__main__':
    main()
