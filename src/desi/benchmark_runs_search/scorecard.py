"""v34.1 - search-compression run scorecard.

A single traceable scorecard summarising the run: the measured
compression metrics, the per-aspect branch breakdown, the replay
hash and the governance status.
"""
from __future__ import annotations

from dataclasses import dataclass

from .branch_preservation import aspect_breakdown, critical_branches_safe
from .search_runner import metrics, run


@dataclass(frozen=True)
class SearchScorecard:
    metrics: tuple[tuple[str, float], ...]
    aspect_breakdown: tuple[tuple[str, int], ...]
    critical_safe: bool
    replay_hash: str
    governance_status: str

    def to_dict(self) -> dict[str, object]:
        return {
            "metrics": [list(m) for m in self.metrics],
            "aspect_breakdown": [list(a) for a in self.aspect_breakdown],
            "critical_safe": self.critical_safe,
            "replay_hash": self.replay_hash,
            "governance_status": self.governance_status,
        }


def search_scorecard() -> SearchScorecard:
    res = run()
    m = metrics()
    return SearchScorecard(
        metrics=tuple(sorted(m.items())),
        aspect_breakdown=tuple(sorted(aspect_breakdown().items())),
        critical_safe=critical_branches_safe(),
        replay_hash=res.replay_hash,
        governance_status=res.governance_status,
    )


def scorecard_traceable() -> bool:
    c = search_scorecard()
    return bool(c.replay_hash) and bool(c.governance_status)


__all__ = [
    "SearchScorecard",
    "scorecard_traceable",
    "search_scorecard",
]
