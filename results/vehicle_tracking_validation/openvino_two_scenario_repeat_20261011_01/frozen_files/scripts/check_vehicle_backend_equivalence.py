#!/usr/bin/env python3
"""Check detector numerics on fixed full frames and crops, without adaptive scheduling."""

import argparse
import hashlib
import json
from pathlib import Path

import cv2
from ultralytics import YOLO

from compare_vehicle_backends import comparison
from uav_learning.vehicle_detector_backend import OpenVINOVehicleDetector
from uav_learning.perception_node import PerceptionNode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial', type=Path, required=True)
    parser.add_argument('--model-path', type=Path, required=True)
    parser.add_argument('--backend-artifacts', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('New result directory required.')
    files = set()
    for name, key in [('image_manifest.jsonl', 'raw_image'), ('crossing_image_manifest.jsonl', 'image')]:
        files.update(row[key] for row in map(json.loads, (args.trial/name).read_text().splitlines()) if row.get(key))
    reference = YOLO(str(args.model_path), task='detect')
    candidate = OpenVINOVehicleDetector(args.backend_artifacts, args.model_path)
    PerceptionNode.warmup_roi_merge()
    rows = []
    for file in sorted(files):
        image = cv2.imread(str(args.trial/file))
        height, width = image.shape[:2]
        # Fixed central crop contains typical mission targets; this is not truth-based selection.
        left, top = (width-320)//2, (height-320)//2
        for size, pixels in [(960, image), (640, image[top:top+320, left:left+320])]:
            cars = []
            for model in (reference, candidate):
                result = model.predict(source=pixels, classes=[2], conf=.1, imgsz=size, device='cpu', verbose=False)[0]
                cars.append([{'bbox': box[:4].tolist(), 'confidence': float(box[4])} for box in result.boxes.data])
            rows.append({'image': file, 'size': size, **comparison(*cars)})
    report = {'inputs': len(files), 'comparisons': len(rows), 'rows': rows,
              'model_sha256': hashlib.sha256(args.model_path.read_bytes()).hexdigest(),
              'backend_manifest_sha256': hashlib.sha256((args.backend_artifacts/'manifest.json').read_bytes()).hexdigest(),
              'unmatched_boxes': sum(row['unmatched'] for row in rows),
              'matched_boxes': sum(row['matched'] for row in rows),
              'max_box_delta_px': max(row['box_max_delta_px'] or 0 for row in rows),
              'max_confidence_delta': max(row['confidence_max_delta'] or 0 for row in rows),
              'raw_sha256': {file: hashlib.sha256((args.trial/file).read_bytes()).hexdigest() for file in files},
              'limitations': 'Fixed detector inputs test numerical agreement, not identity, deadlines or flight success.'}
    report['passed'] = report['unmatched_boxes']==0 and report['max_box_delta_px'] < .005 and report['max_confidence_delta'] < .0001
    args.output.mkdir(parents=True)
    (args.output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: value for key, value in report.items() if key not in ('rows', 'raw_sha256')}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
