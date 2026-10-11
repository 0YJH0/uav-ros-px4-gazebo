#!/usr/bin/env python3
"""Offline YOLO inspection of saved debug JPEGs, not live identity verification."""

import argparse
import json
from pathlib import Path

from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('images', nargs='+')
    parser.add_argument('--output', required=True)
    parser.add_argument('--model', default='yolo11n.pt')
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        raise RuntimeError('Refusing to overwrite existing inspection evidence.')
    model = YOLO(args.model)
    frames = []
    for path in args.images:
        result = model.predict(source=path, classes=[2], conf=0.05,
                               imgsz=960, device='cpu', verbose=False)[0]
        boxes, scores = result.boxes.xyxy.tolist(), result.boxes.conf.tolist()
        frames.append({'image': path, 'cars': [
            {'confidence': float(score), 'box': box,
             'center_error': (box[0] + box[2]) / result.orig_shape[1] - 1}
            for box, score in zip(boxes, scores)]})
    report = {'model': args.model, 'confidence_threshold': 0.05, 'image_size': 960,
              'limitation': 'Saved JPEGs include debug overlays and compression; '
              'offline predictions do not prove exact live detections or target identity.',
              'frames': frames}
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
