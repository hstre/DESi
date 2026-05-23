"""v35.2 - novelty/quality preservation + compression scorecard.

Novelty preservation: every branch carrying real novelty stays
visible (only zero-novelty redundant branches are compressed away).
Quality preservation: the retained set keeps at least the quality of
the kept critical branches.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.benchmark_api_search import MODE_KEPT, MODE_SOFT_REWEIGHTING

from .critical_branch_analysis import (
    critical_branch_preservation, critical_branches_safe,
    hard_pruned_count,
)
from .planning_runner import (
    branch_compression, compute_reduction, node_reduction,
)
from .toolchain_runner import (
    adapter_envelope, dataset_hash, real_branches,
)


def _novel():
    return tuple(b for b in real_branches() if b.novelty > 0.0)


def novelty_preservation() -> float:
    novel = _novel()
    if not novel:
        return 0.0
    retained = sum(1 for b in novel if b.visible)
    return round(retained / len(novel), 6)


def quality_preservation() -> float:
    kept_q = sum(
        b.quality for b in real_branches() if b.mode == MODE_KEPT
    )
    retained_q = sum(
        b.quality for b in real_branches()
        if b.mode in (MODE_KEPT, MODE_SOFT_REWEIGHTING)
    )
    if kept_q <= 0.0:
        return 0.0
    return 1.0 if retained_q >= kept_q else 0.0


def mode_breakdown() -> dict[str, int]:
    counts: dict[str, int] = {}
    for b in real_branches():
        counts[b.mode] = counts.get(b.mode, 0) + 1
    return dict(sorted(counts.items()))


@dataclass(frozen=True)
class CompressionScorecard:
    total_branches: int
    node_reduction: float
    compute_reduction: float
    branch_compression: float
    critical_branch_preservation: float
    novelty_preservation: float
    quality_preservation: float
    hard_pruned_count: int
    mode_breakdown: tuple[tuple[str, int], ...]
    dataset_hash: str
    replay_hash: str
    governance_status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "total_branches": self.total_branches,
            "node_reduction": self.node_reduction,
            "compute_reduction": self.compute_reduction,
            "branch_compression": self.branch_compression,
            "critical_branch_preservation":
                self.critical_branch_preservation,
            "novelty_preservation": self.novelty_preservation,
            "quality_preservation": self.quality_preservation,
            "hard_pruned_count": self.hard_pruned_count,
            "mode_breakdown": [list(m) for m in self.mode_breakdown],
            "dataset_hash": self.dataset_hash,
            "replay_hash": self.replay_hash,
            "governance_status": self.governance_status,
        }


def compression_scorecard() -> CompressionScorecard:
    env = adapter_envelope()
    return CompressionScorecard(
        total_branches=len(real_branches()),
        node_reduction=node_reduction(),
        compute_reduction=compute_reduction(),
        branch_compression=branch_compression(),
        critical_branch_preservation=critical_branch_preservation(),
        novelty_preservation=novelty_preservation(),
        quality_preservation=quality_preservation(),
        hard_pruned_count=hard_pruned_count(),
        mode_breakdown=tuple(mode_breakdown().items()),
        dataset_hash=dataset_hash(),
        replay_hash=env.replay_hash,
        governance_status=env.governance_status,
    )


def scorecard_traceable() -> bool:
    c = compression_scorecard()
    return (
        bool(c.replay_hash)
        and bool(c.dataset_hash)
        and critical_branches_safe()
    )


__all__ = [
    "CompressionScorecard",
    "compression_scorecard",
    "mode_breakdown",
    "novelty_preservation",
    "quality_preservation",
    "scorecard_traceable",
]
