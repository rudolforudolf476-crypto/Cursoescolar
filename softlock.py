"""Experimental temporal gate inspired by NormalTargettingDifficultyInfo.

The XML supplies tuning values, not documented engine semantics. These seconds
are an external approximation, not a reproduction of the game's soft lock.
"""
from math import hypot


class SoftLock:
    def __init__(self, acquire_time=0.25, hold_time=2.5, max_shift=20):
        self.acquire_time = acquire_time
        self.hold_time = hold_time
        self.max_shift = max_shift
        self.reset()

    def reset(self):
        self.previous = None
        self.since = None
        self.locked_at = None
        self.last_seen = None
        self.state = 'sem alvo'

    def update(self, target, now):
        # Never apply resistance using an old detection. Long inference gaps
        # also require acquisition again, rather than counting unseen time.
        if target is None:
            self.reset()
            return None
        changed = self.previous is not None and hypot(
            target.x - self.previous.x, target.y - self.previous.y) > self.max_shift
        stale = self.last_seen is not None and now - self.last_seen > 0.30
        expired = self.locked_at is not None and now - self.locked_at >= self.hold_time
        if self.since is None or changed or stale or expired:
            self.since = now
            self.locked_at = None
        self.previous = target
        self.last_seen = now
        if self.locked_at is None and now - self.since >= self.acquire_time:
            self.locked_at = now
        self.state = 'assistencia ativa' if self.locked_at is not None else 'a adquirir alvo'
        return target if self.locked_at is not None else None
