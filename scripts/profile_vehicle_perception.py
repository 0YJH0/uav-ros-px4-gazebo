#!/usr/bin/env python3
"""Profile the real perception callback on fixed raw inputs, without DDS or flight."""

import argparse
import hashlib
import json
import itertools
from pathlib import Path
import shutil
import time
from types import SimpleNamespace

import cv2
import numpy as np
from cv_bridge import CvBridge
from ultralytics import YOLO

from uav_learning.perception_node import PerceptionNode
from uav_learning.vehicle_target_lock import VehicleTargetLock


ROOT = Path(__file__).resolve().parents[1]


def make_pipeline(model, threads):
    sink = []
    logger = SimpleNamespace(info=lambda message: None, error=lambda message: None)
    node = SimpleNamespace(model=model, class_ids=[key for key, value in model.names.items() if value == 'car'],
        settings={'confidence_threshold': .25, 'tracking_confidence_threshold': .1, 'image_size': 960,
                  'device': 'cpu', 'cpu_inference_threads': threads, 'min_area_ratio': .0005,
                  'target_roi_enabled': True, 'target_roi_image_size': 640,
                  'target_roi_full_frame_budget_s': .25, 'max_frame_age_s': .5},
        tracker=PerceptionNode.create_tracker(.25), motion_estimator=PerceptionNode.create_motion_estimator(),
        camera_motion=None, bridge=CvBridge(), target_id=None, last_log=0.,
        appearance=PerceptionNode.appearance, get_logger=lambda: logger,
        target_pub=SimpleNamespace(publish=lambda message: None),
        vehicles_pub=SimpleNamespace(publish=lambda message: None),
        debug_pub=SimpleNamespace(publish=lambda message: None),
        association_pub=SimpleNamespace(publish=lambda message: sink.append(json.loads(message.data))))
    node.infer_vehicles = lambda image: PerceptionNode.infer_vehicles(node, image)
    return node, sink


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trial', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model-path', type=Path, default=ROOT / 'yolo11s.pt')
    parser.add_argument('--threads', type=int, nargs='+', default=[0, 4, 2])
    parser.add_argument('--backends', nargs='+', choices=('torch', 'openvino'), default=['torch'])
    parser.add_argument('--backend-artifacts', type=Path)
    parser.add_argument('--warmup', type=int, default=6)
    args = parser.parse_args()
    if args.output.exists() or args.warmup < 2 or any(not 0 <= value <= 32 for value in args.threads):
        raise ValueError('New output directory, at least two warmups and threads in [0,32] required.')
    entries = {}
    for name, key in [('image_manifest.jsonl', 'raw_image'), ('crossing_image_manifest.jsonl', 'image')]:
        for row in map(json.loads, (args.trial / name).read_text().splitlines()):
            if row.get(key):
                entries[row[key]] = row
    associations = list(map(json.loads, (args.trial / 'association.jsonl').read_text().splitlines()))
    entries = sorted(entries.items(), key=lambda item: (item[1]['stamp']['sec'], item[1]['stamp']['nanosec']))
    args.output.mkdir(parents=True)
    module = ROOT / 'ros2_ws/src/uav_learning/uav_learning'
    snapshot = args.output / 'source_snapshot'
    snapshot.mkdir()
    for path in list(module.glob('vehicle_*.py')) + [module / 'perception_node.py', Path(__file__)]:
        shutil.copy2(path, snapshot / path.name)
    results, hashes = [], {}
    for backend, threads in itertools.product(args.backends, args.threads):
        if backend == 'openvino':
            from uav_learning.vehicle_detector_backend import OpenVINOVehicleDetector
            model = OpenVINOVehicleDetector(args.backend_artifacts, args.model_path, threads or 8)
        else:
            model = YOLO(str(args.model_path), task='detect')
        node, sink = make_pipeline(model, threads)
        node.settings['detector_backend'] = backend
        PerceptionNode.warmup_roi_merge()
        warm = cv2.imread(str(args.trial / entries[0][0]))
        for index in range(args.warmup):
            model.predict(source=warm if index % 2 else warm[:320, :320],
                          imgsz=960 if index % 2 else 640, classes=node.class_ids, conf=.1,
                          device='cpu', verbose=False)
            PerceptionNode.configure_cpu_threads(node)
        for index in range(args.warmup):
            node.target_lock = VehicleTargetLock(recovery_competition_enabled=False)
            message = node.bridge.cv2_to_imgmsg(warm.copy(), 'bgr8')
            message.header.stamp.sec = index + 1
            PerceptionNode.image_callback(node, message)
            sink.clear()
        node.last_frame_stamp = None
        node.tracker = PerceptionNode.create_tracker(.25)
        node.motion_estimator = PerceptionNode.create_motion_estimator()
        for file, entry in entries:
            path = args.trial / file
            pixels = cv2.imread(str(path))
            if pixels is None:
                raise ValueError(f'Unreadable image: {path}')
            hashes[file] = hashlib.sha256(path.read_bytes()).hexdigest()
            stamp = entry['stamp']
            key = lambda value: (value['stamp']['sec'], value['stamp']['nanosec'])
            previous = [row for row in associations if key(row) <= key(entry)
                        and any(candidate.get('accepted') for candidate in row['candidates'])]
            node.target_lock = VehicleTargetLock(recovery_competition_enabled=False)
            node.target_id = None
            # The same archived detector box seeds all configurations. No pose truth is used.
            if previous:
                candidate = next(item for item in previous[-1]['candidates'] if item.get('accepted'))
                box = candidate['bbox']
                item = (candidate['track_id'], (box[2]-box[0])*(box[3]-box[1]), candidate['confidence'], *box)
                node.target_lock.select([item], [node.appearance(pixels, box)], pixels.shape[1], pixels.shape[0],
                                        time.monotonic())
                node.target_id = node.target_lock.target_id
            message = node.bridge.cv2_to_imgmsg(pixels, 'bgr8')
            message.header.stamp.sec, message.header.stamp.nanosec = stamp['sec'], stamp['nanosec']
            started = time.monotonic()
            PerceptionNode.image_callback(node, message, started)
            result = sink.pop()
            results.append({'backend': backend, 'threads_requested': threads, 'image': file, 'callback_total_s': time.monotonic()-started,
                            'diagnostic': result})
        print('Completed', backend, 'thread setting', threads, flush=True)
    summary = []
    for backend, threads in itertools.product(args.backends, args.threads):
        group = [row for row in results if row['threads_requested'] == threads and row['backend'] == backend]
        times = [row['callback_total_s'] for row in group]
        summary.append({'backend': backend, 'threads_requested': threads,
            'threads_actual': group[0]['diagnostic']['cpu_inference_threads_actual'],
            'frames': len(group), 'mean_s': float(np.mean(times)), 'p95_s': float(np.percentile(times, 95)),
            'max_s': max(times), 'deadline_misses': sum(row['diagnostic']['reason']=='stale_inference_result' for row in group),
            'roi_attempts': sum('roi_s' in row['diagnostic'].get('detector', {}) for row in group)})
    report = {'summary': summary, 'frames': results, 'raw_sha256': hashes,
              'full_callback_warmup_frames': args.warmup,
              'model_sha256': hashlib.sha256(args.model_path.read_bytes()).hexdigest(),
              'source_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in snapshot.iterdir()},
              'limitations': ['Real callback includes conversion, YOLO, GMC, ROI, ByteTrack, appearance, association and debug rendering.',
                  'Publishers are sinks: DDS serialization, transport, camera arrival and simulator CPU load are excluded.',
                  'Archived accepted detector boxes seed a fixed zero-velocity view for profiling, not identity accuracy.',
                  'ROI uses the existing deadline budget and may skip work at slower settings; counts are reported.',
                  'Sparse archived images and a single order cannot establish live coverage or hard real-time performance.']}
    (args.output / 'report.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
