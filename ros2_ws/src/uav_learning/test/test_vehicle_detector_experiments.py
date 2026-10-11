import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


@pytest.fixture
def modules(monkeypatch):
    scripts = Path(__file__).resolve().parents[4] / 'scripts'
    monkeypatch.syspath_prepend(str(scripts))
    result = {}
    for name in ('prepare_vehicle_finetune', 'train_vehicle_detector', 'compare_vehicle_backends',
                 'summarize_vehicle_backends'):
        spec = importlib.util.spec_from_file_location(name, scripts / (name + '.py'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result[name] = module
    return result


def test_yolo_annotation_is_normalized_and_rejects_bad_bounds(modules):
    convert = modules['prepare_vehicle_finetune'].yolo_box
    assert convert([40, 30, 60, 50], 100, 100) == [.5, .4, .2, .2]
    for box in ([-1, 30, 60, 50], [60, 30, 40, 50], [40, 30, 101, 50]):
        with pytest.raises(ValueError):
            convert(box, 100, 100)


def test_backend_agreement_does_not_count_displaced_box_as_matched(modules):
    compare = modules['compare_vehicle_backends'].comparison
    a = {'bbox': [0, 0, 10, 10], 'confidence': .9}
    b = {'bbox': [30, 0, 40, 10], 'confidence': .9}
    assert compare([a], [a])['matched'] == 1
    assert compare([a], [b])['unmatched'] == 2
    assert compare([a], [])['unmatched'] == 1
    assert compare([], [])['unmatched'] == 0


def test_backend_prediction_uses_shared_full_preprocess_and_nms(modules):
    import numpy as np
    import torch
    module = modules['compare_vehicle_backends']
    prediction = torch.zeros(1, 84, 1)
    prediction[0, :4, 0] = torch.tensor([50., 50., 20., 20.])
    prediction[0, 6, 0] = .9
    cars, inference, total = module.predict(lambda pixels: prediction.clone(),
        np.zeros((100, 100, 3), np.uint8), module.LetterBox(new_shape=(100, 100), auto=False),
        [2], (100, 100))
    assert len(cars) == 1 and cars[0]['bbox'] == [40., 40., 60., 60.]
    assert cars[0]['confidence'] == pytest.approx(.9) and total >= inference >= 0


def test_backend_aggregation_rejects_mismatched_weights_or_no_full_warmup(modules, tmp_path):
    paths = [tmp_path / f'{name}.json' for name in ('a', 'b')]
    for path, weight in zip(paths, ('a', 'b')):
        path.write_text(json.dumps({'weight_sha256': weight, 'warmup_full_pipeline_frames': 10}))
    with pytest.raises(ValueError, match='different'):
        modules['summarize_vehicle_backends'].summarize(paths)
    paths[0].write_text('{}')
    with pytest.raises(ValueError, match='warmup'):
        modules['summarize_vehicle_backends'].summarize(paths[:1])


def test_training_requires_matching_manifest_and_reviewed_annotations(modules, tmp_path):
    manifest = tmp_path / 'review_manifest.json'
    manifest.write_text(json.dumps({'rows': []}))
    approval = {'review_manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
                'training_authorized': False}
    (tmp_path / 'annotation_approval.json').write_text(json.dumps(approval))
    with pytest.raises(ValueError, match='authorized'):
        modules['train_vehicle_detector'].verify_review(tmp_path)
    approval['training_authorized'] = True
    approval['review_manifest_sha256'] = 'changed'
    (tmp_path / 'annotation_approval.json').write_text(json.dumps(approval))
    with pytest.raises(ValueError, match='manifest'):
        modules['train_vehicle_detector'].verify_review(tmp_path)
