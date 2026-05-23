"""v11.4 — Chess Governance Concept Gate.

Six conditions per directive:

1. compute_reduction          >= 0.50
2. quality_preservation       >= 0.95
3. tactical_miss_rate         <= 0.05
4. pv_stability               >= 0.90
5. search_governance_integrity >= 0.95
6. replay_stability           == 1.0
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..chess_governance.report import (
    build_report as v110_build,
)
from ..compute_efficiency.report import (
    build_report as v113_build,
)
from ..desi_guided_search.report import (
    build_report as v111_build,
)
from ..tactical_stress.report import (
    build_report as v112_build,
)
from .taxonomy import ChessGovernanceClass


_COMPUTE_REDUCTION_FLOOR:    float = 0.50
_QUALITY_PRESERVATION_FLOOR: float = 0.95
_TACTICAL_MISS_CEIL:         float = 0.05
_PV_STABILITY_FLOOR:         float = 0.90
_GOVERNANCE_FLOOR:           float = 0.95
_REPLAY_FLOOR:               float = 1.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class AggregatedChessMetrics:
    compute_reduction: float
    quality_preservation: float
    tactical_miss_rate: float
    pv_stability: float
    search_governance_integrity: float
    compute_efficiency_gain: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "compute_reduction":
                self.compute_reduction,
            "quality_preservation":
                self.quality_preservation,
            "tactical_miss_rate":
                self.tactical_miss_rate,
            "pv_stability":
                self.pv_stability,
            "search_governance_integrity":
                (
                    self
                    .search_governance_integrity
                ),
            "compute_efficiency_gain":
                self.compute_efficiency_gain,
            "replay_stability":
                self.replay_stability,
        }


@lru_cache(maxsize=1)
def aggregate() -> AggregatedChessMetrics:
    v110 = v110_build()
    v111 = v111_build()
    v112 = v112_build()
    v113 = v113_build()

    # search_governance_integrity: every sprint's
    # closed-enum discipline survived, no critical
    # branch was dropped, no PV displaced, no
    # tactical line lost.
    sgi = (
        (1.0 if v110.no_critical_dropped
         else 0.0)
        + v111.pv_stability
        + (1.0 - v112.tactical_miss_rate)
        + v110.forced_line_detection
    ) / 4.0

    # compute_efficiency_gain: weighted combo of
    # node, time, energy reductions.
    efficiency_gain = v113.compute_reduction

    replay = (
        1.0 if (
            v110.replay_stability == 1.0
            and v111.replay_stability == 1.0
            and v112.replay_stability == 1.0
            and v113.replay_stability == 1.0
        ) else 0.0
    )

    return AggregatedChessMetrics(
        compute_reduction=_round(
            v113.compute_reduction,
        ),
        quality_preservation=_round(
            v113.quality_preservation,
        ),
        tactical_miss_rate=_round(
            v112.tactical_miss_rate,
        ),
        pv_stability=_round(
            v111.pv_stability,
        ),
        search_governance_integrity=_round(
            sgi,
        ),
        compute_efficiency_gain=_round(
            efficiency_gain,
        ),
        replay_stability=replay,
    )


def _gate_results() -> tuple[
    tuple[str, bool], ...,
]:
    m = aggregate()
    return (
        (
            "compute_reduction",
            m.compute_reduction
            >= _COMPUTE_REDUCTION_FLOOR,
        ),
        (
            "quality_preservation",
            m.quality_preservation
            >= _QUALITY_PRESERVATION_FLOOR,
        ),
        (
            "tactical_miss_rate",
            m.tactical_miss_rate
            <= _TACTICAL_MISS_CEIL,
        ),
        (
            "pv_stability",
            m.pv_stability
            >= _PV_STABILITY_FLOOR,
        ),
        (
            "search_governance_integrity",
            m.search_governance_integrity
            >= _GOVERNANCE_FLOOR,
        ),
        (
            "replay_stability",
            m.replay_stability
            >= _REPLAY_FLOOR,
        ),
    )


def gate_passes_all() -> bool:
    return all(
        ok for _, ok in _gate_results()
    )


def gate_failing_conditions() -> tuple[
    str, ...,
]:
    return tuple(
        name for name, ok in _gate_results()
        if not ok
    )


def classify() -> ChessGovernanceClass:
    """Priority order: replay collapse outranks
    governance, governance outranks quality
    loss, quality loss outranks bounded
    compression, bounded compression outranks
    full compressor."""
    m = aggregate()
    if m.replay_stability < _REPLAY_FLOOR:
        return (
            ChessGovernanceClass
            .SEARCH_DEGRADING
        )
    if (
        m.tactical_miss_rate
        > _TACTICAL_MISS_CEIL
        or m.quality_preservation
        < _QUALITY_PRESERVATION_FLOOR
    ):
        return (
            ChessGovernanceClass
            .TACTICAL_RISK_OPTIMIZER
        )
    if (
        m.compute_reduction
        < _COMPUTE_REDUCTION_FLOOR
    ):
        return (
            ChessGovernanceClass
            .BRUTE_FORCE_DEPENDENT
        )
    if (
        m.search_governance_integrity
        < _GOVERNANCE_FLOOR
        or m.pv_stability
        < _PV_STABILITY_FLOOR
    ):
        return (
            ChessGovernanceClass
            .BOUNDED_COMPUTE_REDUCER
        )
    return (
        ChessGovernanceClass
        .EPISTEMIC_SEARCH_COMPRESSOR
    )


__all__ = [
    "AggregatedChessMetrics",
    "aggregate",
    "classify",
    "gate_failing_conditions",
    "gate_passes_all",
]
