"""Optional, pre-exported FP32 CPU detector with the existing YOLO postprocessing."""

import hashlib
import json
from pathlib import Path

import numpy as np


class OpenVINOVehicleDetector:
    def __init__(self, artifacts, weight_path, threads=8):
        import openvino as ov
        import torch
        directory = Path(artifacts)
        manifest = json.loads((directory / 'manifest.json').read_text())
        if hashlib.sha256(Path(weight_path).read_bytes()).hexdigest() != manifest['weight_sha256']:
            raise ValueError('OpenVINO artifacts do not match the selected YOLO weights.')
        expected_files = {f'detector_{size}.{extension}' for size in (960, 640) for extension in ('xml', 'bin')}
        if set(manifest['runtime_sha256']) != expected_files:
            raise ValueError('Incomplete OpenVINO runtime artifact manifest.')
        for name, checksum in manifest['runtime_sha256'].items():
            path = directory / name
            if path.resolve().parent != directory.resolve() or hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
                raise ValueError('OpenVINO runtime artifact integrity mismatch.')
        if manifest.get('precision') != 'FP32' or manifest.get('shapes') != {'960': [544, 960], '640': [640, 640]}:
            raise ValueError('Unsupported OpenVINO input contract.')
        self.names = {int(key): value for key, value in manifest['names'].items()}
        self.shapes = {int(key): tuple(value) for key, value in manifest['shapes'].items()}
        self.models = {}
        torch.set_num_threads(threads)
        core = ov.Core()
        for size in self.shapes:
            model = core.compile_model(str(directory / f'detector_{size}.xml'), 'CPU', {
                'PERFORMANCE_HINT': 'LATENCY', 'NUM_STREAMS': '1',
                'INFERENCE_NUM_THREADS': threads, 'INFERENCE_PRECISION_HINT': 'f32'})
            self.models[size] = model
        self.threads_actual = {size: model.get_property('INFERENCE_NUM_THREADS') for size, model in self.models.items()}

    def predict(self, source, classes, conf, imgsz, device='cpu', verbose=False):
        import torch
        from ultralytics.data.augment import LetterBox
        from ultralytics.engine.results import Results
        from ultralytics.utils.nms import non_max_suppression
        from ultralytics.utils.ops import scale_boxes
        if device != 'cpu' or imgsz not in self.models:
            raise ValueError('Pre-exported OpenVINO supports CPU and image sizes 960/640 only.')
        shape, model = self.shapes[imgsz], self.models[imgsz]
        pixels = LetterBox(new_shape=shape, auto=False, stride=32)(image=source)
        batch = np.ascontiguousarray(pixels[:, :, ::-1].transpose(2, 0, 1)[None], dtype=np.float32) / 255.
        prediction = torch.from_numpy(model([batch])[model.output(0)])
        boxes = non_max_suppression(prediction, conf_thres=conf, iou_thres=.7, classes=classes)[0]
        boxes[:, :4] = scale_boxes(shape, boxes[:, :4], source.shape)
        return [Results(orig_img=source, path='', names=self.names, boxes=boxes)]
