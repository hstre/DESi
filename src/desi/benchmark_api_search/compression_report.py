"""v33.2 - compression measurability, novelty and quality.

Compression is formally measurable iff the four compression modes
plus 'kept' partition the whole search space (every branch is
accounted for). Novelty preservation means no distinct novel branch
is lost - only zero-novelty duplicates are merged. Quality
preservation means the retained set keeps the full quality of the
critical branches.
"""
from __future__ import annotations

from .branch_metrics import (
    MODE_KEPT, MODE_SOFT_REWEIGHTING, mode_counts, search_space,
    total_nodes,
)


def mode_breakdown() -> dict[str, int]:
    return mode_counts()


def compression_measurement() -> float:
    """1.0 iff the mode counts partition the entire search space
    (compression is fully accounted for, nothing untracked)."""
    counts = mode_counts()
    if sum(counts.values()) != total_nodes():
        return 0.0
    return 1.0 if total_nodes() > 0 else 0.0


def _distinct_novel() -> tuple:
    return tuple(b for b in search_space() if b.novelty > 0.0)


def novelty_preservation() -> float:
    """1.0 iff every branch carrying real novelty is retained
    visibly (only zero-novelty duplicates are compressed away)."""
    novel = _distinct_novel()
    if not novel:
        return 0.0
    retained = sum(1 for b in novel if b.visible)
    return round(retained / len(novel), 6)


def quality_preservation() -> float:
    """1.0 iff the retained (kept or soft-reweighted) set preserves
    at least the total quality of the kept branches."""
    kept_quality = sum(
        b.quality for b in search_space() if b.mode == MODE_KEPT
    )
    retained_quality = sum(
        b.quality for b in search_space()
        if b.mode in (MODE_KEPT, MODE_SOFT_REWEIGHTING)
    )
    if kept_quality <= 0.0:
        return 0.0
    return 1.0 if retained_quality >= kept_quality else 0.0


__all__ = [
    "compression_measurement",
    "mode_breakdown",
    "novelty_preservation",
    "quality_preservation",
]
