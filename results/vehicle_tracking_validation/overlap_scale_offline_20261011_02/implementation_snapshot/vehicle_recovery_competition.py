"""Bounded temporal evidence on eligible ByteTrack candidates, not a new tracker."""

from collections import deque

import numpy as np


class RecoveryCompetition:
    def __init__(self):
        self.anchor_velocity = None
        self.histories = {}
        self.consecutive = {}
        self.diagnostic = {'reason': 'inactive'}

    def start(self, velocity):
        if self.anchor_velocity is None:
            self.anchor_velocity = np.asarray(velocity, dtype=float).reshape(2).copy()

    def clear(self):
        self.anchor_velocity = None
        self.histories.clear()
        self.consecutive.clear()
        self.diagnostic = {'reason': 'inactive'}

    def compensate(self, linear, shift, log_scale=0.):
        if self.anchor_velocity is not None:
            self.anchor_velocity = linear @ self.anchor_velocity
        for samples in self.histories.values():
            for sample in samples:
                sample['center'] = linear @ sample['center'] + shift.reshape(2)
                sample['size'] += log_scale

    def choose(self, matches, candidates, now, camera_available):
        self.diagnostic = {'reason': 'collecting', 'candidates': {}}
        if self.anchor_velocity is None:
            return None
        if not camera_available:
            self.histories.clear()
            self.consecutive.clear()
            self.diagnostic['reason'] = 'camera_motion_unavailable'
            return None
        present = [candidates[index][0] for _, index, _ in matches]
        self.histories = {identity: samples for identity, samples in self.histories.items()
                          if 0 <= now - samples[-1]['time'] <= 1.0}
        self.consecutive = {identity: count if identity in present else 0
                            for identity, count in self.consecutive.items() if identity in self.histories}
        ranked = []
        for score, index, measurement in matches:
            identity = candidates[index][0]
            # Unassigned boxes retain their existing, separate confirmation path.
            if identity is None or present.count(identity) != 1:
                self.histories.pop(identity, None)
                continue
            samples = self.histories.setdefault(identity, deque(maxlen=5))
            center = measurement[:2].reshape(2)
            size = measurement[2:].reshape(2)
            if samples and (now <= samples[-1]['time']
                            or now - samples[-1]['time'] > 0.5
                            or np.linalg.norm(center - samples[-1]['center']) >= 0.05
                            or np.max(np.abs(size - samples[-1]['size'])) >= 0.2):
                samples.clear()
                self.consecutive[identity] = 0
            self.consecutive[identity] = self.consecutive.get(identity, 0) + 1
            samples.append({'time': now, 'center': center.copy(), 'size': size.copy(), 'score': float(score)})
            span = now - samples[0]['time']
            info = {'samples': len(samples), 'span_s': span,
                    'consecutive': self.consecutive[identity]}
            self.diagnostic['candidates'][identity] = info
            if len(samples) < 3 or span < 0.3:
                continue
            velocity = (center - samples[0]['center']) / span
            motion_error = float(np.linalg.norm(velocity - self.anchor_velocity))
            total = float(np.mean([sample['score'] for sample in samples])) + (motion_error / 0.03)**2
            info.update(motion_error=motion_error, score=total)
            ranked.append((total, motion_error, index))
        # All competing boxes need mature evidence; a newly appearing rival
        # cannot be silently discarded just because the winner has a history.
        if len(ranked) != len(matches) or len(ranked) < 2:
            return None
        ranked.sort()
        winner, runner = ranked[:2]
        winner_id = candidates[winner[2]][0]
        observations = min(info['samples'] for info in self.diagnostic['candidates'].values())
        evidence_margin = (runner[0] - winner[0]) * observations
        if (winner[1] > 0.03 or evidence_margin < 2.0
                or self.consecutive[winner_id] < 3
                or any(other[1] - winner[1] < 0.005 for other in ranked[1:])):
            self.diagnostic['reason'] = 'motion_evidence_ambiguous'
            return None
        self.diagnostic.update(reason='motion_winner', winner_index=winner[2],
                               score_margin=evidence_margin)
        return winner[2]
