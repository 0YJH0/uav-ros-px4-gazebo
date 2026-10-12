#!/usr/bin/env python3
"""Same FP32 weights, input pixels, letterbox and NMS on Torch/ORT/OpenVINO CPU."""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import statistics
import time

import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment
import torch

os.environ['YOLO_AUTOINSTALL'] = 'false'

from ultralytics import YOLO
from ultralytics.data.augment import LetterBox
from ultralytics.utils.nms import non_max_suppression
from ultralytics.utils.ops import scale_boxes

from vehicle_crossing_validation import iou


def comparison(reference, candidate):
    matrix = np.array([[iou(a['bbox'], b['bbox']) for b in candidate] for a in reference])
    matches = []
    if reference and candidate:
        for a, b in zip(*linear_sum_assignment(-matrix)):
            if matrix[a, b] >= .95:
                matches.append((a, b))
    return {'matched': len(matches), 'reference_boxes': len(reference), 'candidate_boxes': len(candidate),
            'unmatched': len(reference) + len(candidate) - 2 * len(matches),
            'confidence_max_delta': max((abs(reference[a]['confidence'] - candidate[b]['confidence'])
                                         for a, b in matches), default=None),
            'box_max_delta_px': max((max(abs(x - y) for x, y in zip(reference[a]['bbox'], candidate[b]['bbox']))
                                    for a, b in matches), default=None)}


def predict(run, pixels, transform, classes, shape):
    start = time.monotonic()
    batch = np.ascontiguousarray(transform(image=pixels)[:, :, ::-1].transpose(2, 0, 1)[None],
                                 dtype=np.float32) / 255.
    before_infer = time.monotonic()
    prediction = run(batch)
    after_infer = time.monotonic()
    detection = non_max_suppression(prediction, conf_thres=.1, iou_thres=.7, classes=classes)[0]
    detection[:, :4] = scale_boxes(shape, detection[:, :4], pixels.shape)
    cars = [{'bbox': box[:4].tolist(), 'confidence': float(box[4])} for box in detection]
    return cars, after_infer - before_infer, time.monotonic() - start


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial', required=True, type=Path)
    parser.add_argument('--model-path', type=Path, default=Path('yolo11s.pt'))
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--cpu-threads', type=int, default=16)
    parser.add_argument('--repeat', type=int, default=3)
    parser.add_argument('--warmup', type=int, default=10)
    parser.add_argument('--backend-order', nargs=3,
                        default=['torch', 'onnxruntime', 'openvino'])
    args = parser.parse_args()
    if args.cpu_threads < 1 or args.repeat < 1 or args.warmup < 1 or not args.model_path.is_file():
        raise ValueError('Positive thread/repeat counts and a local weight file are required.')
    if set(args.backend_order) != {'torch', 'onnxruntime', 'openvino'}:
        raise ValueError('Backend order must contain all three distinct engines.')
    if args.output.exists():
        raise ValueError('New output directory required.')
    for name in ('onnx', 'onnxruntime', 'openvino'):
        importlib.metadata.version(name)
    import onnxruntime as ort
    import openvino as ov
    args.output.mkdir(parents=True)
    shutil.copy2(args.model_path, args.output / 'detector.pt')
    model = YOLO(str(args.output / 'detector.pt'), task='detect')
    classes = [key for key, name in model.names.items() if name == 'car']
    if not classes:
        raise ValueError('Detector must contain the car class.')
    shape = (544, 960)
    torch.set_num_threads(args.cpu_threads)
    onnx = model.export(format='onnx', imgsz=list(shape), dynamic=False, simplify=False,
                        half=False, device='cpu', opset=18, nms=False)
    converted = ov.convert_model(onnx)
    ov.save_model(converted, args.output / 'detector.xml', compress_to_fp16=False)
    compiled = ov.Core().compile_model(converted, 'CPU', {
        'PERFORMANCE_HINT': 'LATENCY', 'NUM_STREAMS': '1', 'INFERENCE_NUM_THREADS': args.cpu_threads,
        'INFERENCE_PRECISION_HINT': 'f32'})
    options = ort.SessionOptions()
    options.intra_op_num_threads, options.inter_op_num_threads = args.cpu_threads, 1
    session = ort.InferenceSession(onnx, sess_options=options, providers=['CPUExecutionProvider'])
    model.fuse(verbose=False)
    model.model.eval()
    torch.set_num_threads(args.cpu_threads)
    input_name = session.get_inputs()[0].name
    engines = {'torch': lambda x: model.model(torch.from_numpy(x))[0].detach(),
               'onnxruntime': lambda x: torch.from_numpy(session.run(None, {input_name: x})[0]),
               'openvino': lambda x: torch.from_numpy(compiled([x])[compiled.output(0)])}
    entries = []
    for manifest, key in (('image_manifest.jsonl', 'raw_image'), ('crossing_image_manifest.jsonl', 'image')):
        if (args.trial / manifest).exists():
            entries.extend({**json.loads(line), 'file': json.loads(line)[key]}
                           for line in (args.trial / manifest).read_text().splitlines() if json.loads(line).get(key))
    if not entries:
        raise ValueError('No raw images; debug overlays cannot be benchmark inputs.')
    images = {entry['file']: entry for entry in entries}
    rows, hashes = [], {}
    transform = LetterBox(new_shape=shape, auto=False, stride=32)
    with torch.inference_mode():
        for name in args.backend_order:
            run = engines[name]
            warmup_start = time.monotonic()
            warmup_pixels = cv2.imread(str(args.trial / next(iter(images))))
            if warmup_pixels is None:
                raise ValueError('Unreadable warmup raw image.')
            for _ in range(args.warmup):
                predict(run, warmup_pixels, transform, classes, shape)
            warmup_s = time.monotonic() - warmup_start
            for file, entry in images.items():
                path = args.trial / file
                pixels = cv2.imread(str(path))
                if pixels is None:
                    raise ValueError(f'Unreadable raw image: {path}')
                hashes[file] = hashlib.sha256(path.read_bytes()).hexdigest()
                for repeat in range(args.repeat):
                    cars, inference_s, total_s = predict(run, pixels, transform, classes, shape)
                    boxes = entry.get('projected_boxes', {})
                    target = boxes.get('tracked_vehicle')
                    scorable = target is not None and not any(iou(target, box) > .1
                        for identity, box in boxes.items() if identity != 'tracked_vehicle')
                    target_hit = any(iou(target, car['bbox']) >= .4 for car in cars) if scorable else None
                    rows.append({'backend': name, 'image': file, 'stamp': entry['stamp'], 'repeat': repeat,
                                 'inference_s': inference_s, 'total_s': total_s,
                                 'warmup_s': warmup_s, 'cars': cars,
                                 'projection_target_hit_proxy': target_hit})
    reference = {(row['image'], row['repeat']): row for row in rows if row['backend'] == 'torch'}
    summary = {}
    for name in engines:
        subset = [row for row in rows if row['backend'] == name]
        times = [row['total_s'] for row in subset]
        deltas = [comparison(reference[row['image'], row['repeat']]['cars'], row['cars']) for row in subset]
        hits = [row['projection_target_hit_proxy'] for row in subset if row['projection_target_hit_proxy'] is not None]
        summary[name] = {'frames': len(subset), 'total_mean_s': statistics.mean(times),
                         'total_p95_s': float(np.percentile(times, 95)), 'total_max_s': max(times),
                         'unmatched_boxes': sum(row['unmatched'] for row in deltas),
                         'matched_boxes': sum(row['matched'] for row in deltas),
                         'box_max_delta_px': max((row['box_max_delta_px'] or 0 for row in deltas), default=0),
                         'confidence_max_delta': max((row['confidence_max_delta'] or 0 for row in deltas), default=0)}
        summary[name].update(projection_scorable_observations=len(hits),
                             projection_target_hit_fraction_proxy=statistics.mean(hits) if hits else None,
                             distinct_raw_images=len(images))
    report = {'summary': summary, 'frames': rows, 'raw_sha256': hashes,
              'weight_sha256': hashlib.sha256(args.model_path.read_bytes()).hexdigest(),
              'artifact_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                  for path in args.output.glob('detector.*')},
              'versions': {name: importlib.metadata.version(name) for name in (
                  'torch', 'ultralytics', 'onnx', 'onnxruntime', 'openvino', 'numpy', 'opencv-python')},
              'cpu_threads': args.cpu_threads, 'precision': 'FP32', 'input_shape': list(shape),
              'backend_order': args.backend_order,
              'warmup_full_pipeline_frames': args.warmup,
              'threads_actual': {'torch': torch.get_num_threads(),
                                 'onnxruntime_intra_op': session.get_session_options().intra_op_num_threads,
                                 'onnxruntime_inter_op': session.get_session_options().inter_op_num_threads,
                                 'openvino': compiled.get_property('INFERENCE_NUM_THREADS')},
              'conf': .1, 'nms_iou': .7, 'car_classes': classes,
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'limitations': ['Backend box agreement with Torch is not ground-truth detection accuracy.',
                              'Projection hit proxy excludes overlapping/no-truth frames and is not annotated mAP or identity accuracy.',
                              'Includes identical letterbox and NMS, excludes GMC/ROI/ByteTrack/ROS/flight.',
                              'No backend is automatically promoted into flight.',
                              'Repeated timings are correlated measurements, not independent flight trials.']}
    (args.output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
