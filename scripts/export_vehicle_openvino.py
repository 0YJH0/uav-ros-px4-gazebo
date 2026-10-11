#!/usr/bin/env python3
"""Export both flight input shapes before flight; never modify the selected weights."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

os.environ['YOLO_AUTOINSTALL'] = 'false'


def main():
    import openvino as ov
    from ultralytics import YOLO
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-path', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('New artifact directory required.')
    args.output.mkdir(parents=True)
    shutil.copy2(args.model_path, args.output / 'detector.pt')
    model = YOLO(str(args.output / 'detector.pt'), task='detect')
    shapes = {960: [544, 960], 640: [640, 640]}
    for size, shape in shapes.items():
        exported = Path(model.export(format='onnx', imgsz=shape, dynamic=False, simplify=False,
                                     half=False, device='cpu', opset=18, nms=False))
        onnx = exported.rename(args.output / f'detector_{size}.onnx')
        ov.save_model(ov.convert_model(onnx), args.output / f'detector_{size}.xml', compress_to_fp16=False)
    manifest = {'weight_sha256': hashlib.sha256(args.model_path.read_bytes()).hexdigest(),
                'precision': 'FP32', 'shapes': shapes, 'names': model.names,
                'runtime_sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                   for path in args.output.iterdir() if path.suffix in ('.xml', '.bin')},
                'export_script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
