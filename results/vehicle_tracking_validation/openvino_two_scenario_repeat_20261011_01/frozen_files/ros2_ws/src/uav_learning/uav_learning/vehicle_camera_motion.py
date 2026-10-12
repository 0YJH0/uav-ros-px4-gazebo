"""Quality-gated background registration using OpenCV LK and RANSAC."""

import cv2
import numpy as np

from uav_learning.vehicle_target_lock import VehicleTargetLock


class BackgroundMotionEstimator:
    def __init__(self, downscale=2):
        self.downscale = downscale
        self.previous = None
        self.points = None
        self.diagnostic = {}

    @staticmethod
    def assess(previous, current, inliers, warp, width, height, anchor=None):
        previous = np.asarray(previous).reshape(-1, 2)
        current = np.asarray(current).reshape(-1, 2)
        keep = np.asarray(inliers).ravel().astype(bool)
        diagnostic = {'matches': len(previous), 'inliers': int(keep.sum()),
                      'inlier_ratio': float(keep.mean()) if len(keep) else 0.0}
        if keep.sum() < 12 or diagnostic['inlier_ratio'] < 0.6:
            return None, {**diagnostic, 'reason': 'insufficient_inliers'}
        source, destination = previous[keep], current[keep]
        projective = warp.shape == (3, 3)
        if projective:
            corners = np.array([[0, 0], [width, 0], [width, height], [0, height]], dtype=float)
            projected = np.c_[corners, np.ones(4)] @ warp.T
            if (not np.all(np.isfinite(projected)) or np.any(projected[:, 2] <= 0.1)):
                return None, {**diagnostic, 'reason': 'invalid_perspective'}
            projected = projected[:, :2] / projected[:, 2:]
            if np.max(np.linalg.norm((projected - corners) / [width, height], axis=1)) > 0.5:
                return None, {**diagnostic, 'reason': 'perspective_bounds'}
            predicted = np.c_[source, np.ones(len(source))] @ warp.T
            predicted = predicted[:, :2] / predicted[:, 2:]
        else:
            predicted = source @ warp[:, :2].T + warp[:, 2]
        residuals = np.linalg.norm(predicted - destination, axis=1)
        cells = np.minimum((source / [width, height] * [4, 3]).astype(int), [3, 2])
        coverage = len(np.unique(cells, axis=0))
        span = np.ptp(source, axis=0) / [width, height]
        eigenvalues = np.linalg.eigvalsh(np.cov(source / [width, height], rowvar=False))
        support_rms = float(np.sqrt(max(0., eigenvalues[0])))
        conditioning = float(eigenvalues[-1] / eigenvalues[0]) if eigenvalues[0] > 0 else None
        diagnostic.update(residual_median_px=float(np.median(residuals)),
                          residual_p90_px=float(np.quantile(residuals, 0.9)),
                          occupied_cells=coverage, span=span.tolist(),
                          support_rms_normalized=support_rms, spatial_conditioning=conditioning)
        # Similarity needs well-conditioned two-dimensional support, not an
        # arbitrary full-image height span: sky/foreground can leave a wide
        # background band. Perspective fits retain the stronger span check.
        if (coverage < 4 or support_rms < 0.03 or conditioning is None or conditioning > 100
                or (projective and min(span) < 0.25)):
            return None, {**diagnostic, 'reason': 'poor_spatial_coverage'}
        if diagnostic['residual_median_px'] > 1.5 or diagnostic['residual_p90_px'] > 3.0:
            return None, {**diagnostic, 'reason': 'high_residual'}
        if projective:
            center = np.asarray(anchor if anchor is not None else [width / 2, height / 2])
            if (center.shape != (2,) or not np.all(np.isfinite(center))
                    or np.any(center < 0) or np.any(center > [width, height])):
                center = np.array([width / 2, height / 2])
                diagnostic['anchor_fallback'] = 'target_outside_view'
            mapped = warp @ np.r_[center, 1.]
            denominator = mapped[2]
            jacobian = (warp[:2, :2] * denominator - mapped[:2, None] * warp[2, :2]) / denominator**2
            u, singular, vt = np.linalg.svd(jacobian)
            if singular.min() <= 0 or singular.max() / singular.min() > 1.15:
                return None, {**diagnostic, 'reason': 'local_perspective_distortion'}
            linear = u @ vt * singular.mean()
            local_warp = np.c_[linear, mapped[:2] / denominator - linear @ center]
            diagnostic.update(model='homography_local_similarity', anchor_px=center.tolist(),
                              homography_px=warp.tolist(), local_singular_values=singular.tolist())
        else:
            local_warp = warp
            diagnostic['model'] = 'similarity'
        accepted, reason = VehicleTargetLock.validate_camera_motion(local_warp, width, height)
        return accepted, {**diagnostic, 'reason': reason}

    def apply(self, image, detections=None, anchor=None):
        height, width = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (width // self.downscale, height // self.downscale))
        scale = np.array([width / gray.shape[1], height / gray.shape[0]])
        mask = np.full(gray.shape, 255, np.uint8)
        # Foreground vehicles must not vote for the camera transform.
        if detections is not None:
            for box in np.asarray(detections).reshape(-1, 4):
                x1, y1, x2, y2 = box / [*scale, *scale]
                margin = 6
                mask[max(0, int(y1) - margin):min(gray.shape[0], int(y2) + margin),
                     max(0, int(x1) - margin):min(gray.shape[1], int(x2) + margin)] = 0
        points = cv2.goodFeaturesToTrack(gray, maxCorners=400, qualityLevel=0.01,
                                        minDistance=8, blockSize=3, mask=mask)
        previous, old_points = self.previous, self.points
        # Always advance the reference, even after a rejected estimate.
        self.previous, self.points = gray, points
        self.diagnostic = {'reason': 'initializing', 'features': 0 if points is None else len(points)}
        if previous is None or previous.shape != gray.shape:
            return None
        if old_points is None or len(old_points) < 12:
            self.diagnostic['reason'] = 'insufficient_features'
            return None
        forward, status, _ = cv2.calcOpticalFlowPyrLK(previous, gray, old_points, None)
        if forward is None:
            self.diagnostic['reason'] = 'flow_failed'
            return None
        backward, back_status, _ = cv2.calcOpticalFlowPyrLK(gray, previous, forward, None)
        if backward is None:
            self.diagnostic['reason'] = 'backward_flow_failed'
            return None
        error = np.linalg.norm((backward - old_points).reshape(-1, 2) * scale, axis=1)
        valid = status.ravel().astype(bool) & back_status.ravel().astype(bool) & (error <= 3.0)
        source = old_points.reshape(-1, 2)[valid] * scale
        destination = forward.reshape(-1, 2)[valid] * scale
        # Reject points entering a currently detected foreground region too.
        if detections is not None and len(source):
            background = np.ones(len(source), dtype=bool)
            for x1, y1, x2, y2 in np.asarray(detections).reshape(-1, 4):
                background &= ~((destination[:, 0] >= x1 - 12) & (destination[:, 0] <= x2 + 12)
                                & (destination[:, 1] >= y1 - 12) & (destination[:, 1] <= y2 + 12))
            source, destination = source[background], destination[background]
        self.diagnostic.update(matches=len(source), forward_backward_rejected=int((~valid).sum()))
        if len(source) < 12:
            self.diagnostic['reason'] = 'insufficient_matches'
            return None
        warp, inliers = cv2.estimateAffinePartial2D(source, destination, method=cv2.RANSAC,
                                                   ransacReprojThreshold=3.0, maxIters=1000,
                                                   confidence=0.99)
        if warp is None or inliers is None:
            self.diagnostic['reason'] = 'affine_failed'
            return None
        warp, quality = self.assess(source, destination, inliers, warp, width, height)
        if warp is None:
            # Pitch produces perspective motion that a global similarity cannot
            # explain. Fit the same background matches, with the same quality
            # requirements, then linearize around the original target view.
            affine_reason = quality['reason']
            homography, homography_inliers = cv2.findHomography(
                source, destination, method=cv2.RANSAC, ransacReprojThreshold=3.0,
                maxIters=1000, confidence=0.99)
            if homography is not None and homography_inliers is not None:
                warp, quality = self.assess(source, destination, homography_inliers,
                                           homography, width, height, anchor)
            quality['similarity_rejection'] = affine_reason
        self.diagnostic.update(quality)
        return warp
