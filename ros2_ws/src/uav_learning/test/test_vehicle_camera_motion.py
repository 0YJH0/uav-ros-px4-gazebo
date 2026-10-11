import cv2
import numpy as np

from uav_learning.vehicle_camera_motion import BackgroundMotionEstimator


def grid():
    return np.array([[x, y] for x in range(30, 600, 100) for y in range(30, 400, 100)], dtype=float)


def test_quality_accepts_distributed_background_translation():
    source = grid()
    warp = np.array([[1., 0, 8], [0, 1, -6]])
    accepted, quality = BackgroundMotionEstimator.assess(
        source, source + [8, -6], np.ones(len(source)), warp, 640, 480)
    np.testing.assert_array_equal(accepted, warp)
    assert quality['reason'] == 'applied' and quality['occupied_cells'] >= 4


def test_quality_rejects_small_local_patch_even_with_perfect_residual():
    source = grid() / 10
    accepted, quality = BackgroundMotionEstimator.assess(
        source, source, np.ones(len(source)), np.eye(2, 3), 640, 480)
    assert accepted is None and quality['reason'] == 'poor_spatial_coverage'


def test_quality_rejects_low_inlier_ratio_and_large_residual():
    source = grid()
    inliers = np.ones(len(source))
    inliers[12:] = 0
    accepted, quality = BackgroundMotionEstimator.assess(
        source, source, inliers, np.eye(2, 3), 640, 480)
    assert accepted is None and quality['reason'] == 'insufficient_inliers'
    accepted, quality = BackgroundMotionEstimator.assess(
        source, source + [0, 5], np.ones(len(source)), np.eye(2, 3), 640, 480)
    assert accepted is None and quality['reason'] == 'high_residual'


def test_foreground_exclusion_and_rejected_frame_reference_advance():
    estimator = BackgroundMotionEstimator()
    image = np.random.default_rng(17).integers(0, 256, (480, 640, 3), dtype=np.uint8)
    assert estimator.apply(image, [[150, 150, 450, 350]]) is None
    points = estimator.points.reshape(-1, 2) * 2
    assert not np.any((points[:, 0] >= 138) & (points[:, 0] < 462)
                      & (points[:, 1] >= 138) & (points[:, 1] < 362))
    moved = cv2.warpAffine(image, np.array([[1, 0, 8], [0, 1, -6]], np.float32), (640, 480))
    warp = estimator.apply(moved, [[150, 150, 450, 350]])
    np.testing.assert_allclose(warp[:, 2], [8, -6], atol=1)
    blank = np.zeros_like(image)
    assert estimator.apply(blank) is None
    assert estimator.apply(image) is None
    assert estimator.diagnostic['reason'] == 'insufficient_features'
    warp = estimator.apply(moved)
    np.testing.assert_allclose(warp[:, 2], [8, -6], atol=1)


def test_resolution_change_and_featureless_image_are_safe():
    estimator = BackgroundMotionEstimator()
    assert estimator.apply(np.zeros((100, 100, 3), np.uint8)) is None
    assert estimator.apply(np.zeros((200, 200, 3), np.uint8)) is None
    assert estimator.apply(np.zeros((200, 200, 3), np.uint8)) is None
    assert estimator.diagnostic['reason'] == 'insufficient_features'


def test_projective_quality_linearizes_at_target_without_relaxing_gates():
    source = grid()
    homography = np.array([[1., 0, 0], [0, 1, 60], [0, 0.00015, 1]])
    destination = np.c_[source, np.ones(len(source))] @ homography.T
    destination = destination[:, :2] / destination[:, 2:]
    anchor = np.array([320., 350.])
    warp, quality = BackgroundMotionEstimator.assess(
        source, destination, np.ones(len(source)), homography, 640, 480, anchor)
    assert quality['reason'] == 'applied' and quality['model'] == 'homography_local_similarity'
    actual = homography @ np.r_[anchor, 1]
    np.testing.assert_allclose(warp[:, :2] @ anchor + warp[:, 2], actual[:2] / actual[2])
    wrong, quality = BackgroundMotionEstimator.assess(
        source, destination + [5, 0], np.ones(len(source)), homography, 640, 480, anchor)
    assert wrong is None and quality['reason'] == 'high_residual'


def test_projective_estimator_recovers_pitch_frame():
    estimator = BackgroundMotionEstimator()
    image = np.random.default_rng(13).integers(0, 256, (480, 640, 3), dtype=np.uint8)
    homography = np.array([[1., 0, 0], [0, 1, 50], [0, 0.00018, 1]])
    estimator.apply(image)
    warped = cv2.warpPerspective(image, homography, (640, 480))
    warp = estimator.apply(warped, anchor=[320, 350])
    assert warp is not None
    assert estimator.diagnostic['reason'] == 'applied'
    assert estimator.diagnostic['model'] == 'homography_local_similarity'
    projected = homography @ [320, 350, 1]
    np.testing.assert_allclose(warp[:, :2] @ [320, 350] + warp[:, 2], projected[:2] / projected[2], atol=2)


def test_bad_or_offscreen_anchor_never_extrapolates_perspective():
    source = grid()
    homography = np.array([[1., 0, 0], [0, 1, 20], [0, 0.00010, 1]])
    projected = np.c_[source, np.ones(len(source))] @ homography.T
    destination = projected[:, :2] / projected[:, 2:]
    for anchor in ([320, -10000], [float('nan'), 100], [6400, 100], [1, 2, 3]):
        warp, quality = BackgroundMotionEstimator.assess(
            source, destination, np.ones(len(source)), homography, 640, 480, anchor)
        assert warp is not None and quality['reason'] == 'applied'
        assert quality['anchor_fallback'] == 'target_outside_view'
        assert quality['anchor_px'] == [320., 240.]


def test_wide_background_band_is_valid_similarity_support():
    source = np.array([[x, y] for x in range(30, 600, 100) for y in (100, 150, 200)], dtype=float)
    warp = np.array([[1., 0, 0], [0, 1, 35.]])
    accepted, quality = BackgroundMotionEstimator.assess(
        source, source + [0, 35], np.ones(len(source)), warp, 640, 480)
    assert accepted is not None and quality['reason'] == 'applied'
    assert quality['span'][1] < 0.25
    assert quality['support_rms_normalized'] > 0.03
    assert quality['spatial_conditioning'] < 100


def test_diagonal_collinear_features_are_rejected_despite_large_span():
    source = np.array([[x, x * 0.6] for x in range(30, 600, 20)], dtype=float)
    accepted, quality = BackgroundMotionEstimator.assess(
        source, source, np.ones(len(source)), np.eye(2, 3), 640, 480)
    assert accepted is None and quality['reason'] == 'poor_spatial_coverage'
