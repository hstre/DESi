"""v33.2 - the search space and its compression modes.

A deterministic search/planning space of branches. Compression must
clearly distinguish four mechanisms, because they have very different
epistemic safety:

    hard_pruning                  - a branch is deleted (lossy;
                                    never applied to a critical branch)
    soft_reweighting              - a branch is downweighted but kept
                                    fully visible (reversible)
    replay_reuse                  - a branch's result is reused from
                                    the replay cache (lossless)
    redundant_branch_compression  - duplicate branches are merged
                                    (lossless for novelty)

Critical (load-bearing) branches are always KEPT and visible; they
are never hard-pruned. Compression comes from lossless reuse/merge and
reversible reweighting, so the search space shrinks without hiding any
load-bearing branch.
"""
from __future__ import annotations

from dataclasses import dataclass

MODE_KEPT = "kept"
MODE_HARD_PRUNING = "hard_pruning"
MODE_SOFT_REWEIGHTING = "soft_reweighting"
MODE_REPLAY_REUSE = "replay_reuse"
MODE_REDUNDANT_COMPRESSION = "redundant_branch_compression"

COMPRESSION_MODES: tuple[str, ...] = (
    MODE_KEPT, MODE_HARD_PRUNING, MODE_SOFT_REWEIGHTING,
    MODE_REPLAY_REUSE, MODE_REDUNDANT_COMPRESSION,
)

# Modes that retain the branch in a visible, recoverable form.
_LOSSLESS_MODES: frozenset[str] = frozenset({
    MODE_KEPT, MODE_SOFT_REWEIGHTING, MODE_REPLAY_REUSE,
    MODE_REDUNDANT_COMPRESSION,
})


@dataclass(frozen=True)
class Branch:
    branch_id: str
    critical: bool
    redundant: bool
    novelty: float
    quality: float
    mode: str

    @property
    def visible(self) -> bool:
        return self.mode in _LOSSLESS_MODES

    @property
    def recomputed(self) -> bool:
        """A branch costs a recompute only if kept or soft-reweighted;
        reuse/merge cost nothing, hard-pruned ones are gone."""
        return self.mode in (MODE_KEPT, MODE_SOFT_REWEIGHTING)


def _build_space() -> tuple[Branch, ...]:
    out: list[Branch] = []
    # 10 critical branches - kept, fully visible, high novelty/quality
    for i in range(10):
        out.append(Branch(
            f"critical_{i}", True, False, 1.0, 1.0, MODE_KEPT))
    # 25 non-critical unique branches - soft reweighted (visible)
    for i in range(25):
        out.append(Branch(
            f"unique_{i}", False, False, 0.6, 0.7,
            MODE_SOFT_REWEIGHTING))
    # 20 redundant branches reused from the replay cache
    for i in range(20):
        out.append(Branch(
            f"reuse_{i}", False, True, 0.0, 0.7, MODE_REPLAY_REUSE))
    # 20 redundant duplicates merged by redundant-branch compression
    for i in range(20):
        out.append(Branch(
            f"dup_{i}", False, True, 0.0, 0.7,
            MODE_REDUNDANT_COMPRESSION))
    return tuple(out)


_SEARCH_SPACE: tuple[Branch, ...] = _build_space()


def search_space() -> tuple[Branch, ...]:
    return _SEARCH_SPACE


def total_nodes() -> int:
    return len(search_space())


def distinct_nodes() -> int:
    """Branches that survive as distinct recompute nodes (kept or
    soft-reweighted)."""
    return sum(1 for b in search_space() if b.recomputed)


def mode_counts() -> dict[str, int]:
    counts = {m: 0 for m in COMPRESSION_MODES}
    for b in search_space():
        counts[b.mode] += 1
    return counts


def hard_pruned_count() -> int:
    return mode_counts()[MODE_HARD_PRUNING]


def node_reduction() -> float:
    total = total_nodes()
    if total <= 0:
        return 0.0
    return round((total - distinct_nodes()) / total, 6)


def branch_compression() -> float:
    """Fraction of branches handled by a compression mode (anything
    other than plain 'kept')."""
    total = total_nodes()
    if total <= 0:
        return 0.0
    compressed = sum(
        1 for b in search_space() if b.mode != MODE_KEPT
    )
    return round(compressed / total, 6)


def compute_reduction() -> float:
    """Recompute saved: a baseline recomputes every branch once;
    reuse/merge cost nothing."""
    total = total_nodes()
    if total <= 0:
        return 0.0
    recomputed = sum(1 for b in search_space() if b.recomputed)
    return round((total - recomputed) / total, 6)


__all__ = [
    "COMPRESSION_MODES",
    "MODE_HARD_PRUNING",
    "MODE_KEPT",
    "MODE_REDUNDANT_COMPRESSION",
    "MODE_REPLAY_REUSE",
    "MODE_SOFT_REWEIGHTING",
    "Branch",
    "branch_compression",
    "compute_reduction",
    "distinct_nodes",
    "hard_pruned_count",
    "mode_counts",
    "node_reduction",
    "search_space",
    "total_nodes",
]
