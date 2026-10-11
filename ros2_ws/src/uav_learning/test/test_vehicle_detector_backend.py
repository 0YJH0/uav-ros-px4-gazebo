import hashlib
import json
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from uav_learning.vehicle_detector_backend import OpenVINOVehicleDetector


def artifacts(tmp_path, monkeypatch):
    weight = tmp_path / 'weights.pt'
    weight.write_bytes(b'fixed weights')
    names = [f'detector_{size}.{ext}' for size in (960, 640) for ext in ('xml', 'bin')]
    for name in names:
        (tmp_path / name).write_bytes(name.encode())
    manifest = {'weight_sha256': hashlib.sha256(weight.read_bytes()).hexdigest(),
                'runtime_sha256': {name: hashlib.sha256((tmp_path/name).read_bytes()).hexdigest() for name in names},
                'precision': 'FP32', 'shapes': {'960': [544, 960], '640': [640, 640]}, 'names': {'2': 'car'}}
    (tmp_path / 'manifest.json').write_text(json.dumps(manifest))
    class Compiled:
        def get_property(self, key):
            return 8

        def output(self, index):
            return 'output'

        def __call__(self, batch):
            assert batch[0].dtype == np.float32 and batch[0].shape[0] == 1
            return {'output': np.zeros((1, 84, 5), np.float32)}
    core = SimpleNamespace(compile_model=lambda *args, **kwargs: Compiled())
    monkeypatch.setitem(sys.modules, 'openvino', SimpleNamespace(Core=lambda: core))
    return weight


def test_backend_rejects_different_weights_and_modified_ir(tmp_path, monkeypatch):
    weight = artifacts(tmp_path, monkeypatch)
    weight.write_bytes(b'other weights')
    with pytest.raises(ValueError, match='selected YOLO weights'):
        OpenVINOVehicleDetector(tmp_path, weight)
    weight.write_bytes(b'fixed weights')
    (tmp_path / 'detector_640.bin').write_bytes(b'modified')
    with pytest.raises(ValueError, match='integrity mismatch'):
        OpenVINOVehicleDetector(tmp_path, weight)


def test_backend_returns_standard_boxes_for_both_input_shapes(tmp_path, monkeypatch):
    weight = artifacts(tmp_path, monkeypatch)
    detector = OpenVINOVehicleDetector(tmp_path, weight)
    image = np.zeros((540, 960, 3), np.uint8)
    for size in (960, 640):
        result = detector.predict(image, [2], .1, size)[0]
        assert result.orig_shape == (540, 960) and len(result.boxes) == 0
    with pytest.raises(ValueError, match='sizes'):
        detector.predict(image, [2], .1, 320)
