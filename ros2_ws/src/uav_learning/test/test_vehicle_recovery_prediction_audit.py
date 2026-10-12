import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest

from uav_learning.vehicle_target_lock import VehicleTargetLock

SCRIPTS = Path(__file__).resolve().parents[4] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('recovery_prediction_audit',
                                             SCRIPTS / 'analyze_vehicle_recovery_prediction.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def test_empty_candidate_frame_still_advances_kalman_prediction():
    first, second = VehicleTargetLock(), VehicleTargetLock()
    view = np.array([[.5], [.5], [-2.], [-2.]])
    for lock in (first, second):
        lock.reset_prediction(view, 0.)
        lock.last_seen = 0.
        lock.last_measurement = view.copy()
        state = lock.filter.statePost.copy()
        state[4:8, 0] = [.01, -.02, .03, -.04]
        lock.filter.statePost = state
    first.select([], [], 960, 540, .4)
    predicted, covariance = audit.predict(second, .4)
    np.testing.assert_array_equal(first.filter.statePre[:4], predicted)
    np.testing.assert_array_equal(first.filter.errorCovPre, second.filter.errorCovPre)
    np.testing.assert_array_equal(covariance, first.filter.errorCovPre[:4, :4]
                                  + first.filter.measurementNoiseCov)


def test_expired_prediction_uses_last_view_without_advancing_filter():
    lock = VehicleTargetLock(recovery_timeout=10.)
    view = np.array([[.5], [.5], [-2.], [-2.]])
    lock.reset_prediction(view, 0.)
    lock.last_seen, lock.last_measurement = 0., view.copy()
    before = lock.filter.statePost.copy()
    predicted, covariance = audit.predict(lock, 10.1)
    np.testing.assert_array_equal(predicted, view)
    np.testing.assert_array_equal(lock.filter.statePost, before)
    assert covariance is None and lock.last_predict == 0.


def test_recorded_elapsed_clock_reconstructs_exact_residuals_after_miss(tmp_path, monkeypatch):
    lock = VehicleTargetLock(bounded_scale_prediction=False)
    frames = []
    for index, now in enumerate((0., .2, .5, .7)):
        candidates = [] if index == 1 else [(7, 10000., .9,
                                            430 + index, 230, 530 + index, 330)]
        elapsed = None if lock.last_seen is None else now - lock.last_seen
        chosen = lock.select(candidates, [None] * len(candidates), 960, 540, now)
        frames.append({'wall_s': now + 10., 'stamp': {'sec': index, 'nanosec': 0},
                       'image_shape': [540, 960], 'mode': lock.mode, 'reason': lock.reason,
                       'identity_confirmed': chosen is not None,
                       'elapsed_since_confirmed_s': elapsed,
                       'candidates': [dict(candidate, index=i) for i, candidate in enumerate(lock.diagnostics)]})
    (tmp_path / 'association.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in frames))
    (tmp_path / 'identity_observations.jsonl').write_text('')
    (tmp_path / 'report.json').write_text(json.dumps({'transitions': [{'state': 'SEARCH', 'time_s': 9.}]}))
    (tmp_path / 'runtime_parameters.json').write_text(json.dumps({'perception_node': {
        'predict_box_scale_velocity': True, 'target_reacquire_timeout': 10.,
        'bounded_scale_prediction': False}}))
    module = 'ros2_ws/src/uav_learning/uav_learning/vehicle_target_lock.py'
    (tmp_path / 'implementation_snapshot.json').write_text(json.dumps({
        'source_sha256': {module: audit.digest(audit.ROOT / module)}}))
    monkeypatch.setattr(audit, 'extend_truth', lambda directory, truth, associations, root: (truth, {}))
    rows, validation = audit.reconstruct(tmp_path)
    assert len(rows) == 4
    assert rows[1]['predicted_box'] is not None
    assert all(value['max_abs_error'] == 0. for value in validation['residual_validation'].values())


@pytest.mark.parametrize('now', [.500001, 5., 10.])
def test_direct_legacy_predict_rejects_bounded_gap_without_mutating_filter(now):
    lock = VehicleTargetLock()
    view = np.array([[.5], [.5], [-2.], [-2.]])
    lock.reset_prediction(view, 0.)
    lock.last_seen, lock.last_measurement = 0., view.copy()
    state = lock.filter.statePost.copy()
    state[6:, 0] = [.1, -.1]
    lock.filter.statePost = state
    covariance = lock.filter.errorCovPost.copy()
    with pytest.raises(ValueError, match='Legacy CV prediction cannot reconstruct bounded'):
        audit.predict(lock, now)
    np.testing.assert_array_equal(lock.filter.statePost, state)
    np.testing.assert_array_equal(lock.filter.errorCovPost, covariance)
    assert lock.last_predict == lock.last_seen == 0.


@pytest.mark.parametrize('configuration', [{'bounded_scale_prediction': True}, {}])
def test_reconstruction_rejects_enabled_or_unknown_bounded_model_before_reading_frames(tmp_path,
                                                                                     configuration):
    settings = {'predict_box_scale_velocity': True, 'target_reacquire_timeout': 10.,
                **configuration}
    (tmp_path / 'runtime_parameters.json').write_text(json.dumps({'perception_node': settings}))
    with pytest.raises(ValueError, match='requires explicit bounded_scale_prediction=false'):
        audit.reconstruct(tmp_path)
    assert sorted(path.name for path in tmp_path.iterdir()) == ['runtime_parameters.json']


@pytest.mark.parametrize('geometry', ['horizontal_only', 'vertical_only', 'protected', 'unknown'])
def test_reconstruction_rejects_unsupported_corrected_geometry_before_truth_lookup(tmp_path, geometry):
    (tmp_path / 'runtime_parameters.json').write_text(json.dumps({'perception_node': {
        'predict_box_scale_velocity': True, 'target_reacquire_timeout': 10.,
        'bounded_scale_prediction': False}}))
    (tmp_path / 'association.jsonl').write_text(json.dumps({
        'candidates': [{'accepted': True, 'geometry_update': geometry}]}) + '\n')
    with pytest.raises(ValueError, match='does not support masked geometry corrections'):
        audit.reconstruct(tmp_path)
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        'association.jsonl', 'runtime_parameters.json']
