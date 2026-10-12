from pathlib import Path
import json
import sys
import time
import numpy as np
import cv2
import torch

ROOT = Path('/home/yjh/ROS2_manmade')
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'ros2_ws/src/uav_learning')]
from uav_learning.vehicle_roi_detector import choose_crop, merge_boxes
from vehicle_crossing_validation import evaluate_identity
from ultralytics import YOLO

def rows(p):
    return [json.loads(x) for x in p.read_text().splitlines()]

def key(r):
    return r['stamp']['sec'], r['stamp']['nanosec']

torch.set_num_threads(8)
p = ROOT / 'results/vehicle_tracking_validation/overlap_scale_gui_20261011_01'
a = {key(r): r for r in rows(p / 'association.jsonl')}
manifest = [r for r in rows(p / 'crossing_image_manifest.jsonl') if r['wall_s'] > 158]
model = YOLO(str(ROOT / 'yolo11s.pt'))
model.predict(np.zeros((540,960,3), np.uint8), classes=[2], conf=.1, imgsz=960, verbose=False)
results = []
for row in manifest:
    image = cv2.imread(str(p / row['image']))
    old = a.get(key(row))
    assert old is not None
    center = old['detector']['roi_view_norm']
    dimensions = old['candidates'][0]['predicted_size_px']
    view = np.r_[center, np.log(np.asarray(dimensions) / [960,540])]
    crop = choose_crop(view, 960, 540)
    left,top,right,bottom = crop
    start=time.monotonic()
    full = model.predict(image, classes=[2], conf=.1, imgsz=960, verbose=False)[0].boxes
    full_s=time.monotonic()-start
    start=time.monotonic()
    zoom = model.predict(image[top:bottom,left:right], classes=[2], conf=.1, imgsz=640, verbose=False)[0].boxes
    zoom_s=time.monotonic()-start
    merged,sources = merge_boxes(full, zoom, crop, image.shape[:2])
    out={'image':row['image'],'wall_s':row['wall_s'],'original_label':row['label'],
         'crop':crop,'full_s':full_s,'zoom_s':zoom_s,'candidates':[]}
    for box,source in zip(merged.data.cpu().numpy(),sources):
        ev=evaluate_identity(box[:4].tolist(),row['projected_boxes'])
        out['candidates'].append({'box':box[:4].tolist(),'confidence':float(box[4]),'source':source,
                                  'label':ev['label'],'reason':ev['reason']})
    results.append(out)
    print(json.dumps(out),flush=True)
Path('/tmp/post_merge_detection_check.json').write_text(json.dumps(results,indent=2))
