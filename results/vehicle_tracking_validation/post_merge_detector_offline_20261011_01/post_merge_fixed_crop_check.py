from pathlib import Path
import json
import sys
import time
import numpy as np
import cv2
import torch

ROOT = Path('/home/yjh/ROS2_manmade')
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'ros2_ws/src/uav_learning')]
from vehicle_crossing_validation import evaluate_identity
from ultralytics import YOLO

def rows(p):
    return [json.loads(x) for x in p.read_text().splitlines()]

def key(r):
    return r['stamp']['sec'], r['stamp']['nanosec']

torch.set_num_threads(8)
p = ROOT / 'results/vehicle_tracking_validation/overlap_scale_gui_20261011_01'
a = {key(r): r for r in rows(p / 'association.jsonl')}
manifest = [r for r in rows(p / 'crossing_image_manifest.jsonl') if r['wall_s'] > 169]
model = YOLO(str(ROOT / 'yolo11s.pt'))
results = []
for row in manifest:
    image = cv2.imread(str(p / row['image']))
    old = a[key(row)]
    center = np.array(old['detector']['roi_view_norm']) * [960,540]
    dimensions = old['candidates'][0]['predicted_size_px']
    crops=[]
    for size in (320,400,480,540):
        left=int(np.clip(round(center[0]-size/2),0,960-size))
        top=int(np.clip(round(center[1]-size/2),0,540-size))
        crops.append(('fixed_square'+str(size),[left,top,left+size,top+size]))
    crops.append(('full_frame',[0,0,960,540]))
    for name,crop in crops:
        left,top,right,bottom=crop
        left=max(0,left);top=max(0,top);right=min(960,right);bottom=min(540,bottom)
        for size in (640,):
            start=time.monotonic()
            boxes=model.predict(image[top:bottom,left:right],classes=[2],conf=.1,imgsz=size,verbose=False)[0].boxes
            seconds=time.monotonic()-start
            out={'image':row['image'],'wall_s':row['wall_s'],'original_label':row['label'],
                 'crop_name':name,'crop':crop,'imgsz':size,'infer_s':seconds,'candidates':[]}
            for bb in boxes.data.cpu().numpy():
                box=bb[:4]+[left,top,left,top]
                ev=evaluate_identity(box.tolist(),row['projected_boxes'])
                out['candidates'].append({'box':box.tolist(),'confidence':float(bb[4]),
                                          'label':ev['label'],'reason':ev['reason'],
                                          'crop_border_touches':bool(bb[0]<2 or bb[1]<2 or bb[2]>right-left-2 or bb[3]>bottom-top-2)})
            results.append(out)
            print(json.dumps(out),flush=True)
Path('/tmp/post_merge_fixed_crop_check.json').write_text(json.dumps(results,indent=2))
