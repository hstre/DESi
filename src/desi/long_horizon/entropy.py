"""v5.3 — windowed entropy + contradiction
growth + frame explosion metrics over the
long-horizon trajectory."""
from __future__ import annotations

import math
from collections import Counter

from ..open_world.claim_stream import (
    FRAME_TYPES, all_conflicts,
)
from .stability import STEP_COUNT, trajectory


def _normalised_entropy(
    items: list[str], universe_size: int,
) -> float:
    if not items:
        return 0.0
    cnt = Counter(items)
    total = sum(cnt.values())
    h = 0.0
    for c in cnt.values():
        p = c / total
        if p > 0:
            h -= p * math.log2(p)
    max_h = math.log2(max(universe_size, 2))
    if max_h <= 0:
        return 0.0
    return round(h / max_h, 6)


def early_entropy() -> float:
    """Frame entropy over the first 50 steps."""
    traj = trajectory()
    frames = [s.frame for s in traj[:50]]
    return _normalised_entropy(
        frames, len(FRAME_TYPES),
    )


def late_entropy() -> float:
    """Frame entropy over the last 50 steps."""
    traj = trajectory()
    frames = [
        s.frame
        for s in traj[STEP_COUNT - 50:]
    ]
    return _normalised_entropy(
        frames, len(FRAME_TYPES),
    )


def entropy_growth() -> float:
    """Difference between late and early frame
    entropy. Near 0 means DESi stabilised; a
    large positive value means new frames keep
    appearing; a large negative value means
    collapse."""
    return round(
        late_entropy() - early_entropy(), 6,
    )


def contradiction_growth() -> int:
    """Closed-stream conflicts touched by the
    trajectory. The number of UNIQUE
    contradictions seen does not grow with the
    trajectory length because the claim stream
    is finite (and cycled), so this metric is
    the contradiction count IN the stream that
    the trajectory exposed at all."""
    seen = set()
    traj_claim_ids = {
        s.claim_id for s in trajectory()
    }
    for a, b, kind in all_conflicts():
        if (
            kind == "contradiction"
            and a in traj_claim_ids
            and b in traj_claim_ids
        ):
            seen.add((a, b))
    return len(seen)


def frame_universe_seen() -> int:
    return len({
        s.frame for s in trajectory()
    })


def frame_explosion() -> float:
    """Fraction of the closed FRAME_TYPES enum
    that the trajectory exposed. Capped at 1.0
    by construction - a true 'explosion' would
    require new frame types to appear, which the
    closed enum forbids; so this metric measures
    coverage rather than runaway."""
    return round(
        frame_universe_seen() / len(FRAME_TYPES),
        6,
    )


__all__ = [
    "contradiction_growth",
    "early_entropy",
    "entropy_growth",
    "frame_explosion",
    "frame_universe_seen",
    "late_entropy",
]
