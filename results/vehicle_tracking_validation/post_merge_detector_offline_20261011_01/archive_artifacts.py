"""Archive existing read-only detector experiments without re-running inference."""

from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import shutil

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
TRIAL = ROOT / 'results/vehicle_tracking_validation/overlap_scale_gui_20261011_01'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    manifest = OUT / 'archive_manifest.json'
    if manifest.exists():
        raise RuntimeError('Do not overwrite the archived experiment.')
    mappings = {
        'post_merge_detection_check.py': 'post_merge_detection_check.py',
        'post_merge_detection_check.json': 'post_merge_detection_check.json',
        'post_merge_crop_check.py': 'post_merge_fixed_crop_check.py',
        'post_merge_fixed_crop_check.json': 'post_merge_fixed_crop_check.json',
        'post_merge_crop_check.json': 'post_merge_crop_check.json',
        'post_merge_diagnosis.md': 'DIAGNOSIS.md',
    }
    copied = {}
    for source, name in mappings.items():
        path = Path('/tmp') / source
        target = OUT / name
        if target.exists():
            raise RuntimeError(f'Archive target exists: {target}')
        shutil.copy2(path, target)
        copied[name] = {'working_source': str(path), 'sha256': digest(target)}

    first = json.loads((OUT / 'post_merge_detection_check.json').read_text())
    names = sorted({row['image'] for row in first})
    inputs = {}
    (OUT / 'inputs').mkdir()
    for name in names:
        source = TRIAL / name
        shutil.copy2(source, OUT / 'inputs' / name)
        inputs[name] = {'source_relative_to_root': str(source.relative_to(ROOT)),
                        'sha256': digest(source), 'size_bytes': source.stat().st_size}
    source_paths = (
        'ros2_ws/src/uav_learning/uav_learning/vehicle_roi_detector.py',
        'scripts/vehicle_crossing_validation.py',
    )
    sources = {}
    for relative in source_paths:
        source = ROOT / relative
        target = OUT / 'source_snapshot' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        frozen = TRIAL / 'executed_sources' / relative
        sources[relative] = {'sha256': digest(source),
                             'matches_prior_flight_snapshot': (
                                 frozen.exists() and digest(frozen) == digest(source))}
    evidence = {}
    for name in ('association.jsonl', 'identity_observations.jsonl',
                 'crossing_image_manifest.jsonl', 'runtime_parameters.json',
                 'identity_report.json'):
        source = TRIAL / name
        evidence[name] = {'source_relative_to_root': str(source.relative_to(ROOT)),
                          'sha256': digest(source)}
    model = ROOT / 'yolo11s.pt'
    data = {
        'archived_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_trial': str(TRIAL.relative_to(ROOT)),
        'scope': 'Read-only detection checks; no deployed detector change or new closed-loop run.',
        'sample_count': len(names),
        'late_crop_sweep_sample_count': 3,
        'late_crop_sweep_sim_s': [125.6, 126.6, 127.652],
        'confirmed_nms_loss_examples': 1,
        'confirmed_nms_loss_example_sim_s': 126.6,
        'matching_key': 'Exact image stamp (sec, nanosec), not wall_s.',
        'wall_clock_limitation': 'Output wall_s uses identity/image-manifest epoch; association epoch differs by about +4.484 s.',
        'model': {'path_relative_to_root': 'yolo11s.pt', 'sha256': digest(model),
                  'size_bytes': model.stat().st_size},
        'settings': {'classes': [2], 'confidence': 0.1, 'full_frame_imgsz': 960,
                     'roi_default_imgsz': 640, 'torch_cpu_threads': 8,
                     'existing_cross_source_nms_iou': 0.7},
        'environment_versions': {name: version(name) for name in
                                 ('torch', 'torchvision', 'ultralytics', 'numpy', 'opencv-python')},
        'images': inputs,
        'original_evidence': evidence,
        'source_snapshot': sources,
        'copied_artifacts': copied,
        'reconstructed_script': {
            'name': 'post_merge_broad_crop_reconstructed.py',
            'status': 'Reconstructed from this turn execution record after original /tmp script was edited for fixed-square comparison; not rerun.',
            'sha256': digest(OUT / 'post_merge_broad_crop_reconstructed.py'),
        },
        'limitations': [
            'Nine archived images and a three-image hard-case crop sweep, not an independent test set.',
            'Labels are projected-box evidence, not pixel-instance ground truth.',
            'Raw output contains diagnostic timings including initialization in some first calls.',
            'No new coverage, recovery, wrong-identity, or closed-loop safety result is inferred.',
            'Detector source snapshots match the prior flight only when explicitly recorded true.',
        ],
    }
    manifest.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'archive': str(OUT), 'images': len(names),
                      'source_snapshot': sources, 'model_sha256': data['model']['sha256']}, indent=2))


if __name__ == '__main__':
    main()
