"""Observable, bounded association on top of YOLO/ByteTrack detections."""

import math

import cv2
import numpy as np

from uav_learning.vehicle_recovery_competition import RecoveryCompetition


class VehicleTargetLock:
    def __init__(self, recovery_timeout=10.0, acquisition_center_gate=1.0,
                 acquisition_confirm_frames=1, confidence_threshold=0.25,
                 weak_idless_confirm_frames=3, weak_idless_max_age=2.0,
                 recovery_competition_enabled=True, predict_box_scale_velocity=True,
                 overlap_candidate_recovery=True, bounded_scale_prediction=True):
        # Legacy argument: horizon of the image-motion model, not lock expiry.
        self.prediction_horizon = recovery_timeout
        self.acquisition_center_gate = acquisition_center_gate
        self.acquisition_confirm_frames = acquisition_confirm_frames
        self.confidence_threshold = confidence_threshold
        self.weak_idless_confirm_frames = weak_idless_confirm_frames
        self.weak_idless_max_age = weak_idless_max_age
        self.last_strong_seen = None
        self.target_id = None
        self.last_seen = None
        self.last_predict = None
        self.last_measurement = None
        self.reference = None
        self.pending_id = None
        self.pending_count = 0
        self.pending_measurement = None
        self.pending_time = None
        self.pending_evidence = None
        self.mode = 'acquiring'
        self.reason = 'no_candidates'
        self.elapsed_since_seen = None
        self.diagnostics = []
        self.camera_motion_reason = 'unavailable'
        self.overlap_guard_active = False
        self.overlap_guard_reason = None
        self.last_similar_rival = None
        self.crossing_risk_diagnostic = {}
        self.recovery_competition_enabled = recovery_competition_enabled
        self.predict_box_scale_velocity = predict_box_scale_velocity
        self.overlap_candidate_recovery = overlap_candidate_recovery
        self.bounded_scale_prediction = bounded_scale_prediction
        self.candidate_overlap = {}
        self.merged_candidates = set()
        self.scale_prediction_clamped = False
        self.competition = RecoveryCompetition()
        self.competition_diagnostic = {'reason': 'inactive'}
        self.filter = cv2.KalmanFilter(8, 4, 0, cv2.CV_64F)
        self.filter.measurementMatrix = np.eye(4, 8, dtype=np.float64)
        self.filter.measurementNoiseCov = np.diag([0.008**2] * 2 + [0.08**2] * 2)

    @staticmethod
    def measurement(item, width, height):
        _, _, _, x1, y1, x2, y2 = item
        return np.array([[(x1 + x2) / (2 * width)],
                         [(y1 + y2) / (2 * height)],
                         [math.log(max((x2 - x1) / width, 1e-6))],
                         [math.log(max((y2 - y1) / height, 1e-6))]])

    def reset_prediction(self, measurement, now):
        self.filter.statePost = np.vstack([measurement, np.zeros((4, 1))])
        self.filter.errorCovPost = np.diag([0.01**2] * 2 + [0.1**2] * 2
                                         + [0.1**2] * 2 + [0.3**2] * 2)
        self.last_predict = now

    @staticmethod
    def vertical_truncation(item, height):
        return bool(item[4] <= 0.5 or item[6] >= height - 0.5)

    def correct_geometry(self, measurement, truncated):
        if not truncated:
            self.filter.correct(measurement)
            return measurement
        # A censored box measures neither full height nor full vertical center.
        # Keep horizontal evidence, but do not learn vertical motion from it.
        matrix = self.filter.measurementMatrix.copy()
        masked = matrix.copy()
        masked[[1, 3], :] = 0.
        observed = measurement.copy()
        observed[[1, 3]] = 0.
        try:
            self.filter.measurementMatrix = masked
            self.filter.correct(observed)
        finally:
            self.filter.measurementMatrix = matrix
        state = self.filter.statePost.copy()
        state[[5, 7]] = 0.
        self.filter.statePost = state
        safe_measurement = measurement.copy()
        safe_measurement[[1, 3]] = state[[1, 3]]
        return safe_measurement

    def clear_pending(self):
        self.pending_id, self.pending_count = None, 0
        self.pending_measurement, self.pending_time = None, None
        self.pending_evidence = None

    @staticmethod
    def validate_camera_motion(warp, width, height):
        if warp is None:
            return None, 'unavailable'
        warp = np.asarray(warp, dtype=np.float64)
        if warp.shape != (2, 3) or not np.all(np.isfinite(warp)):
            return None, 'invalid_warp'
        linear = warp[:, :2]
        scale = math.sqrt(abs(float(np.linalg.det(linear))))
        shift = warp[:, 2:3] / np.array([[width], [height]])
        rotation = math.atan2(linear[1, 0], linear[0, 0])
        if (np.linalg.det(linear) <= 0 or not 0.9 <= scale <= 1.1 or
                abs(rotation) > 0.2 or np.linalg.norm(shift) > 0.25 or
                np.max(np.abs(linear.T @ linear - np.eye(2) * scale**2)) > 0.01):
            return None, 'warp_bounds'
        return warp, 'applied'

    def compensate_camera_motion(self, warp, width, height):
        warp, self.camera_motion_reason = self.validate_camera_motion(warp, width, height)
        if warp is None:
            return
        linear = warp[:, :2]
        scale = math.sqrt(float(np.linalg.det(linear)))
        shift = warp[:, 2:3] / np.array([[width], [height]])
        normalized = np.diag([1 / width, 1 / height]) @ linear @ np.diag([width, height])

        def view(measurement):
            transformed = measurement.copy()
            transformed[:2] = normalized @ measurement[:2] + shift
            transformed[2:4] += math.log(scale)
            return transformed

        if self.last_measurement is not None:
            self.last_measurement = view(self.last_measurement)
            jacobian = np.eye(8)
            jacobian[:2, :2] = jacobian[4:6, 4:6] = normalized
            state = jacobian @ self.filter.statePost
            state[:2] += shift
            state[2:4] += math.log(scale)
            self.filter.statePost = state
            self.filter.errorCovPost = jacobian @ self.filter.errorCovPost @ jacobian.T
        if self.pending_measurement is not None:
            self.pending_measurement = view(self.pending_measurement)
        self.competition.compensate(normalized, shift, math.log(scale))
        self.camera_motion_reason = 'applied'

    def confirm(self, item, measurement, now, required, evidence='standard'):
        compatible_id = (self.pending_id == item[0] or
                         self.pending_id is None or item[0] is None)
        if evidence == 'partial_overlap':
            compatible_id = self.pending_id == item[0]
        consistent = (self.pending_count > 0 and compatible_id and self.pending_evidence == evidence
                      and now - self.pending_time <= 0.5
                      and np.linalg.norm(measurement[:2] - self.pending_measurement[:2]) < 0.05
                      and np.max(np.abs(measurement[2:] - self.pending_measurement[2:])) < 0.2)
        self.pending_count = min(required, self.pending_count + 1) if consistent else 1
        self.pending_evidence = evidence
        self.pending_id, self.pending_time = item[0], now
        self.pending_measurement = measurement.copy()
        return self.pending_count >= required

    @staticmethod
    def view_box(measurement, width, height):
        center = measurement[:2, 0] * [width, height]
        size = np.exp(measurement[2:4, 0]) * [width, height]
        return np.r_[center - size / 2, center + size / 2]

    @staticmethod
    def box_overlap(first, second):
        size = np.maximum(0.0, np.minimum(first[2:], second[2:]) - np.maximum(first[:2], second[:2]))
        intersection = float(np.prod(size))
        union = float(np.prod(first[2:] - first[:2]) + np.prod(second[2:] - second[:2]) - intersection)
        return intersection / union if union > 0 else 0.0

    def crossing_risk(self, candidates, histograms, predicted, width, height, now):
        self.crossing_risk_diagnostic = {}
        self.candidate_overlap = {}
        self.merged_candidates = set()
        if self.reference is None:
            return None
        expected = self.view_box(predicted, width, height)
        similar = []
        for index, (item, histogram) in enumerate(zip(candidates, histograms)):
            if (item[2] < self.confidence_threshold or histogram is None or
                    cv2.compareHist(self.reference, histogram, cv2.HISTCMP_CORREL) < 0.95):
                continue
            measurement = self.measurement(item, width, height)
            if np.linalg.norm(measurement[:2] - predicted[:2]) <= 0.35:
                similar.append((index, measurement, np.asarray(item[3:], dtype=float)))
        nearby = [(index, measurement, box) for index, measurement, box in similar
                  if self.box_overlap(expected, box) >= 0.2]
        risk = None
        for index, measurement, box in nearby:
            for other, other_measurement, other_box in similar:
                if index == other:
                    continue
                overlap = self.box_overlap(box, other_box)
                # Duplicate full-frame/ROI boxes are not two independent cars.
                if np.linalg.norm(measurement[:2] - other_measurement[:2]) <= 0.025 or overlap >= 0.7:
                    continue
                if candidates[index][0] is None or candidates[other][0] is None:
                    intersection = np.maximum(0., np.minimum(box[2:], other_box[2:])
                                              - np.maximum(box[:2], other_box[:2]))
                    horizontal_union = max(box[2], other_box[2]) - min(box[0], other_box[0])
                    smaller_area = min(np.prod(box[2:] - box[:2]), np.prod(other_box[2:] - other_box[:2]))
                    # YOLO can emit nested height variants of the same car.
                    # Distinct confirmed IDs still require the crossing hold.
                    if (intersection[0] / horizontal_union >= 0.9 and
                            np.prod(intersection) / smaller_area >= 0.9):
                        continue
                self.last_similar_rival = now
                if overlap > 0.05:
                    risk = 'similar_vehicle_overlap'
                    self.candidate_overlap.setdefault(index, set()).add(other)
                    self.candidate_overlap.setdefault(other, set()).add(index)
        rival_age = None if self.last_similar_rival is None else now - self.last_similar_rival
        # Missed/stale frames must not erase a rival before identity is restored.
        # Confirmed tracking still expires this evidence after two seconds.
        gap_retained = (rival_age is not None and rival_age > 2.0
                        and self.last_seen - self.last_similar_rival <= 2.0
                        and now - self.last_seen <= self.prediction_horizon)
        self.crossing_risk_diagnostic = {'similar_rival_age_s': rival_age,
                                         'gap_retained': gap_retained}
        if rival_age is not None and (rival_age <= 2.0 or gap_retained):
            for index, measurement, _ in nearby:
                change = (measurement[2:4] - self.last_measurement[2:4])[:, 0]
                vertical_merge = (self.bounded_scale_prediction and change[1] > math.log(1.35)
                                  and change[1] - change[0] > math.log(1.25))
                if change[0] > math.log(1.6) or vertical_merge:
                    risk = 'merged_vehicle_box'
                    self.merged_candidates.add(index)
        return risk

    def overlap_distinguishable(self, index, candidates):
        box = np.asarray(candidates[index][3:], dtype=float)
        others = [np.asarray(candidates[other][3:], dtype=float)
                  for other in self.candidate_overlap.get(index, ())]
        if not others:
            return True
        # Subtract the union of competing boxes, not a sum that double-counts overlaps.
        xs = sorted({box[0], box[2], *(float(np.clip(x, box[0], box[2]))
                    for other in others for x in (other[0], other[2]))})
        ys = sorted({box[1], box[3], *(float(np.clip(y, box[1], box[3]))
                    for other in others for y in (other[1], other[3]))})
        exclusive = 0.
        for x1, x2 in zip(xs, xs[1:]):
            for y1, y2 in zip(ys, ys[1:]):
                x, y = (x1 + x2) / 2, (y1 + y2) / 2
                if not any(other[0] < x < other[2] and other[1] < y < other[3] for other in others):
                    exclusive += (x2 - x1) * (y2 - y1)
        fraction = exclusive / max(float(np.prod(box[2:] - box[:2])), 1e-12)
        self.diagnostics[index]['candidate_exclusive_fraction'] = fraction
        return fraction > .5

    def select(self, candidates, histograms, width, height, now, camera_motion=None):
        self.competition_diagnostic = {'reason': 'inactive'}
        # Register the old view to this frame before target-motion prediction.
        # This image evidence neither confirms identity nor refreshes last_seen.
        self.compensate_camera_motion(camera_motion, width, height)
        self.elapsed_since_seen = None if self.last_seen is None else max(0.0, now - self.last_seen)
        self.mode = ('acquiring' if self.last_seen is None else
                     'reacquiring' if self.elapsed_since_seen > self.prediction_horizon else 'tracking')
        self.reason = 'no_candidates' if not candidates else 'all_candidates_rejected'
        self.diagnostics = [{'track_id': item[0], 'confidence': float(item[2]),
                             'bbox': list(item[3:]), 'accepted': False,
                             'reason': 'not_selected', 'rejection_reasons': []}
                            for item in candidates]
        for item, diagnostic in zip(candidates, self.diagnostics):
            diagnostic['vertical_truncated'] = self.vertical_truncation(item, height)
        if not candidates:
            self.clear_pending()
        if self.last_seen is None:
            eligible = []
            for index, item in enumerate(candidates):
                error = abs((item[3] + item[5]) / width - 1)
                diagnostic = self.diagnostics[index]
                diagnostic.update(center_error=error, center_gate=self.acquisition_center_gate)
                if diagnostic['vertical_truncated']:
                    diagnostic['rejection_reasons'].append('truncated_acquisition_box')
                if item[2] < self.confidence_threshold:
                    diagnostic['rejection_reasons'].append('confidence_gate')
                if error > self.acquisition_center_gate:
                    diagnostic['rejection_reasons'].append('acquisition_region')
                if diagnostic['rejection_reasons']:
                    diagnostic['reason'] = diagnostic['rejection_reasons'][0]
                else:
                    eligible.append(index)
            if not eligible:
                self.clear_pending()
                return None
            index = max(eligible, key=lambda idx: candidates[idx][1])
            selected = candidates[index]
            measurement = self.measurement(selected, width, height)
            if not self.confirm(selected, measurement, now, self.acquisition_confirm_frames):
                self.mark_pending(index, self.acquisition_confirm_frames)
                return None
            self.reset_prediction(measurement, now)
            return self.accept(selected, histograms[index], measurement, now, index)

        elapsed = self.elapsed_since_seen
        stale = self.mode == 'reacquiring'
        recovering = elapsed >= 2.0
        self.scale_prediction_clamped = False
        if stale:
            # Camera yaw and target motion invalidate old extrapolation. Keep
            # identity evidence, but use a bounded last-view search with stronger
            # appearance and temporal confirmation, never an expiry rejection.
            predicted = self.last_measurement
            covariance = None
        else:
            if not self.predict_box_scale_velocity:
                state = self.filter.statePost.copy()
                state[6:] = 0.
                self.filter.statePost = state
            dt = max(0.0, now - self.last_predict)
            self.last_predict = now
            transition = np.eye(8)
            transition[:4, 4:] = np.eye(4) * dt
            if self.bounded_scale_prediction:
                # Damped scale velocity has a finite, frame-rate-independent integral.
                observed_dt = min(dt, max(0., .5 - max(0., elapsed - dt)))
                decay = math.exp(-(dt - observed_dt))
                transition[2:4, 6:8] = np.eye(2) * (observed_dt + 1. - decay)
                transition[6:8, 6:8] = np.eye(2) * decay
            self.filter.transitionMatrix = transition
            noise = np.zeros((8, 8))
            for axis, variance in enumerate([0.03**2] * 2 + [0.15**2] * 2):
                noise[axis, axis] = variance * dt**4 / 4
                noise[axis, axis + 4] = noise[axis + 4, axis] = variance * dt**3 / 2
                noise[axis + 4, axis + 4] = variance * dt**2
            self.filter.processNoiseCov = noise
            predicted = self.filter.predict()[:4]
            if self.bounded_scale_prediction and elapsed > .5:
                state = self.filter.statePost.copy()
                bounded = np.clip(state[2:4], self.last_measurement[2:4] - math.log(1.25),
                                  self.last_measurement[2:4] + math.log(1.25))
                clamped = np.abs(state[2:4] - bounded)[:, 0] > 1e-12
                self.scale_prediction_clamped = bool(np.any(clamped))
                state[2:4] = bounded
                state[6:8][clamped] = 0.
                self.filter.statePost = state
                self.filter.statePre = state.copy()
                predicted = state[:4].copy()
            covariance = self.filter.errorCovPre[:4, :4] + self.filter.measurementNoiseCov

        matches = []
        risk = self.crossing_risk(candidates, histograms, predicted, width, height, now)
        if risk:
            if self.recovery_competition_enabled:
                self.competition.start(self.filter.statePost[4:6])
            self.overlap_guard_active = True
            self.overlap_guard_reason = risk
        for index, (item, histogram) in enumerate(zip(candidates, histograms)):
            measurement = self.measurement(item, width, height)
            residual = measurement - predicted
            center_error = float(np.linalg.norm(residual[:2]))
            scale_error = float(np.max(np.abs(residual[2:])))
            center_gate = 0.35 if stale else min(0.18, 0.04 + 0.025 * elapsed)
            scale_gate = math.log(3.0 if stale else 2.0)
            similarity = None
            if self.reference is not None and histogram is not None:
                similarity = float(cv2.compareHist(self.reference, histogram, cv2.HISTCMP_CORREL))
            appearance_gate = 0.85 if stale else 0.75
            weak = item[2] < self.confidence_threshold
            weak_idless = weak and item[0] is None
            if weak_idless:
                center_gate = min(center_gate, 0.03)
                scale_gate = min(scale_gate, math.log(1.25))
                appearance_gate = max(appearance_gate, 0.95)
            distance = (None if stale else float(
                (residual.T @ np.linalg.solve(covariance, residual)).item()))
            diagnostic = self.diagnostics[index]
            diagnostic.update(center_error=center_error, center_gate=center_gate,
                              log_scale_error=scale_error, log_scale_gate=scale_gate,
                              appearance_similarity=similarity, appearance_gate=appearance_gate,
                              mahalanobis_distance=distance, mahalanobis_gate=None if stale else 18.5)
            reasons = diagnostic['rejection_reasons']
            if stale and diagnostic['vertical_truncated']:
                reasons.append('truncated_reacquisition_box')
            continuation = not stale and item[0] is not None and item[0] == self.target_id
            diagnostic.update(confidence_gate=self.confidence_threshold,
                              low_confidence_continuation=weak and continuation,
                              weak_idless_candidate=weak_idless)
            if risk and not self.overlap_candidate_recovery:
                reasons.append(risk)
                diagnostic['crossing_risk_evidence'] = dict(self.crossing_risk_diagnostic)
            elif self.overlap_guard_active:
                # Preserve the pre-overlap shape instead of learning a merged
                # box or trusting an old tracker ID attached to another car.
                diagnostic.update(overlap_recovery=True, overlap_width_ratio_max=1.35)
                if risk:
                    diagnostic['crossing_risk_evidence'] = dict(self.crossing_risk_diagnostic)
                if index in self.merged_candidates:
                    reasons.append('merged_vehicle_box')
                elif self.overlap_candidate_recovery and not self.overlap_distinguishable(index, candidates):
                    reasons.append('overlap_ambiguous_geometry')
                if weak:
                    reasons.append('overlap_recovery_requires_strong')
                if similarity is None or similarity < 0.85:
                    reasons.append('overlap_recovery_appearance')
                size_change = measurement[2:4] - self.last_measurement[2:4]
                shape_growth = (float(np.max(size_change)) if self.bounded_scale_prediction
                                else float(size_change[0, 0]))
                if shape_growth > math.log(1.35):
                    reasons.append('overlap_shape_gate')
            diagnostic.update(scale_prediction_clamped=self.scale_prediction_clamped,
                              predicted_size_px=(np.exp(predicted[2:4, 0]) * [width, height]).tolist())
            if weak_idless:
                anchor_age = None if self.last_strong_seen is None else max(0.0, now - self.last_strong_seen)
                diagnostic.update(strong_anchor_age_s=anchor_age, strong_anchor_max_age_s=self.weak_idless_max_age)
                if stale or anchor_age is None or anchor_age > self.weak_idless_max_age:
                    reasons.append('weak_idless_anchor_expired')
                if similarity is None:
                    reasons.append('weak_idless_appearance_missing')
            elif weak and not continuation:
                reasons.append('confidence_gate')
            if center_error > center_gate:
                reasons.append('center_gate')
            if scale_error > scale_gate:
                reasons.append('scale_gate')
            if similarity is not None and similarity < appearance_gate:
                reasons.append('appearance_gate')
            if stale and similarity is None:
                reasons.append('appearance_missing')
            elif recovering and similarity is None:
                reasons.append('recovery_appearance_missing')
            changed_id = item[0] != self.target_id or item[0] is None
            if not stale and changed_id and similarity is None and (
                    elapsed > 0.75 or center_error > 0.025 or scale_error > 0.2):
                reasons.append('id_change_without_appearance')
            if distance is not None and distance > 18.5:
                reasons.append('mahalanobis_gate')
            if reasons:
                diagnostic['reason'] = reasons[0]
                continue
            score = ((center_error / center_gate)**2 + (scale_error / scale_gate)**2
                     if stale else distance)
            score += 0.0 if similarity is None else 4 * (1 - similarity)
            diagnostic['score'] = score
            matches.append((score, index, measurement))

        motion_winner = None
        if self.recovery_competition_enabled and self.overlap_guard_active:
            motion_winner = self.competition.choose(
                matches, candidates, now, self.camera_motion_reason == 'applied')
            self.competition_diagnostic = self.competition.diagnostic
            for _, matched_index, _ in matches:
                info = self.competition.diagnostic['candidates'].get(candidates[matched_index][0])
                if info:
                    self.diagnostics[matched_index]['recovery_competition'] = info
        if not matches:
            self.clear_pending()
            return None
        matches.sort(key=lambda match: match[0])
        score, index, measurement = matches[0]
        competition_confirmed = False
        if len(matches) > 1 and matches[1][0] - score < (0.2 if stale else 2.0):
            if motion_winner is None:
                for _, matched_index, _ in matches:
                    self.diagnostics[matched_index]['reason'] = 'ambiguous_candidates'
                    self.diagnostics[matched_index]['rejection_reasons'] = ['ambiguous_candidates']
                self.reason = 'ambiguous_candidates'
                self.clear_pending()
                return None
            score, index, measurement = next(match for match in matches if match[1] == motion_winner)
            self.diagnostics[index]['competition_resolved_ambiguity'] = True
            competition_confirmed = True
        selected = candidates[index]
        weak_idless = selected[2] < self.confidence_threshold and selected[0] is None
        residual = measurement - predicted
        changed_id = selected[0] != self.target_id or selected[0] is None
        near_continuation = (elapsed <= 0.75 and np.linalg.norm(residual[:2]) < 0.025
                             and np.max(np.abs(residual[2:])) < 0.2)
        required = self.weak_idless_confirm_frames if weak_idless else 3 if recovering or self.overlap_guard_active else 2
        if competition_confirmed:
            self.diagnostics[index].update(confirmation_count=self.competition.consecutive[selected[0]],
                                           confirmation_required=required)
        elif weak_idless or recovering or self.overlap_guard_active or (changed_id and not near_continuation):
            if not self.confirm(selected, measurement, now, required,
                                evidence='weak_idless' if weak_idless else
                                'partial_overlap' if risk and self.overlap_candidate_recovery else
                                'overlap_recovery' if self.overlap_guard_active else
                                'recovery' if recovering else 'standard'):
                self.mark_pending(index, required)
                return None
            self.diagnostics[index].update(confirmation_count=self.pending_count,
                                           confirmation_required=required)
        if stale:
            self.reset_prediction(measurement, now)
            self.diagnostics[index]['geometry_update'] = 'full_reset'
        else:
            truncated = self.diagnostics[index]['vertical_truncated']
            measurement = self.correct_geometry(measurement, truncated)
            self.diagnostics[index]['geometry_update'] = 'horizontal_only' if truncated else 'full'
            if truncated:
                self.diagnostics[index]['protected_axes'] = ['center_y', 'log_height', 'velocity_y', 'velocity_log_height']
            state = self.filter.statePost.copy()
            state[4:6] = np.clip(state[4:6], -0.15, 0.15)
            state[6:] = np.clip(state[6:], -0.3, 0.3)
            if not self.predict_box_scale_velocity:
                state[6:] = 0.
            self.filter.statePost = state
        return self.accept(selected, histograms[index], measurement, now, index,
                           preserve_confirmation=weak_idless or bool(risk and self.overlap_candidate_recovery),
                           overlap_continuation=bool(risk and self.overlap_candidate_recovery))

    def mark_pending(self, index, required):
        self.reason = 'pending_confirmation'
        self.diagnostics[index].update(reason='pending_confirmation',
                                       confirmation_count=self.pending_count,
                                       confirmation_required=required)

    def accept(self, selected, histogram, measurement, now, index, preserve_confirmation=False,
               overlap_continuation=False):
        # An identity-associated raw box may temporarily lack a tracker ID.
        # Keep the last known ID; do not disable low-score continuity by erasing it.
        if selected[0] is not None:
            self.target_id = selected[0]
        self.last_seen = now
        if selected[2] >= self.confidence_threshold:
            self.last_strong_seen = now
        self.last_measurement = measurement.copy()
        if not preserve_confirmation:
            self.clear_pending()
        self.reason = 'confirmed'
        if not overlap_continuation:
            self.overlap_guard_active = False
            self.overlap_guard_reason = None
            self.competition.clear()
        self.diagnostics[index].update(accepted=True, reason='confirmed',
                                       weak_idless_confirmed=preserve_confirmation and not overlap_continuation,
                                       overlap_continuation=overlap_continuation)
        if self.reference is None and histogram is not None:
            self.reference = histogram.copy()
        return selected
