"""v9.4 — Strategic Epistemics Concept Gate.

Six conditions per directive:

1. strategy_detection     >= 0.90
2. gaming_detection_rate  >= 0.90
3. consensus_integrity    >= 0.90
4. governance_stability   >= 0.95
5. epistemic_sovereignty  >= 0.90
6. replay_stability       == 1.0
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..coalition_warfare.report import (
    build_report as v92_build,
)
from ..governance_gaming.report import (
    build_report as v91_build,
)
from ..strategic_epistemics.report import (
    build_report as v90_build,
)
from ..strategic_pressure.report import (
    build_report as v93_build,
)
from .taxonomy import StrategicEpistemicsClass


_STRATEGY_DETECTION_FLOOR: float = 0.90
_GAMING_DETECTION_FLOOR:   float = 0.90
_CONSENSUS_INTEGRITY_FLOOR: float = 0.90
_GOVERNANCE_FLOOR:         float = 0.95
_SOVEREIGNTY_FLOOR:        float = 0.90
_REPLAY_FLOOR:             float = 1.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class AggregatedStrategicMetrics:
    strategy_detection: float
    gaming_detection_rate: float
    consensus_integrity: float
    governance_stability: float
    governance_survival: float
    epistemic_sovereignty: float
    dissent_integrity: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "strategy_detection":
                self.strategy_detection,
            "gaming_detection_rate":
                self.gaming_detection_rate,
            "consensus_integrity":
                self.consensus_integrity,
            "governance_stability":
                self.governance_stability,
            "governance_survival":
                self.governance_survival,
            "epistemic_sovereignty":
                self.epistemic_sovereignty,
            "dissent_integrity":
                self.dissent_integrity,
            "replay_stability":
                self.replay_stability,
        }


@lru_cache(maxsize=1)
def aggregate() -> AggregatedStrategicMetrics:
    v90 = v90_build()
    v91 = v91_build()
    v92 = v92_build()
    v93 = v93_build()

    # governance_stability: AND across v9.0
    # (closed actor-enum), v9.1 (closed
    # gaming-enum), v9.3 (no gate_bypass over
    # 5000 steps and no governance-snapshot
    # drift).
    governance = min(
        v90.governance_integrity,
        v91.gate_integrity,
        1.0 - v93.governance_erosion,
        1.0 - v93.capture_risk,
    )

    # epistemic_sovereignty: composite of
    # v9.0 strategy_detection, v9.1 gaming
    # detection rate, v9.2 consensus integrity,
    # v9.3 (1 - opportunism_growth).
    sovereignty = (
        v90.strategy_detection
        + v91.gaming_detection_rate
        + v92.consensus_integrity
        + (1.0 - v93.opportunism_growth)
    ) / 4.0

    dissent = v92.dissent_preservation

    replay = (
        1.0 if (
            v90.replay_stability == 1.0
            and v91.replay_stability == 1.0
            and v92.replay_stability == 1.0
            and v93.replay_stability == 1.0
        ) else 0.0
    )

    return AggregatedStrategicMetrics(
        strategy_detection=_round(
            v90.strategy_detection,
        ),
        gaming_detection_rate=_round(
            v91.gaming_detection_rate,
        ),
        consensus_integrity=_round(
            v92.consensus_integrity,
        ),
        governance_stability=_round(governance),
        governance_survival=_round(governance),
        epistemic_sovereignty=_round(
            sovereignty,
        ),
        dissent_integrity=_round(dissent),
        replay_stability=replay,
    )


def _gate_results() -> tuple[
    tuple[str, bool], ...,
]:
    m = aggregate()
    return (
        (
            "strategy_detection",
            m.strategy_detection
            >= _STRATEGY_DETECTION_FLOOR,
        ),
        (
            "gaming_detection_rate",
            m.gaming_detection_rate
            >= _GAMING_DETECTION_FLOOR,
        ),
        (
            "consensus_integrity",
            m.consensus_integrity
            >= _CONSENSUS_INTEGRITY_FLOOR,
        ),
        (
            "governance_stability",
            m.governance_stability
            >= _GOVERNANCE_FLOOR,
        ),
        (
            "epistemic_sovereignty",
            m.epistemic_sovereignty
            >= _SOVEREIGNTY_FLOOR,
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


def classify() -> StrategicEpistemicsClass:
    """Priority order: replay collapse outranks
    governance, governance outranks coalition
    sensitivity, coalition outranks bounded
    strategic drift."""
    m = aggregate()
    if m.replay_stability < _REPLAY_FLOOR:
        return (
            StrategicEpistemicsClass
            .EPISTEMICALLY_CORRUPTIBLE
        )
    if (
        m.governance_stability
        < _GOVERNANCE_FLOOR
    ):
        return (
            StrategicEpistemicsClass
            .GOVERNANCE_CAPTURABLE
        )
    if (
        m.consensus_integrity
        < _CONSENSUS_INTEGRITY_FLOOR
    ):
        return (
            StrategicEpistemicsClass
            .COALITION_SENSITIVE
        )
    if (
        m.epistemic_sovereignty
        < _SOVEREIGNTY_FLOOR
    ):
        return (
            StrategicEpistemicsClass
            .BOUNDED_STRATEGIC_DRIFT
        )
    return (
        StrategicEpistemicsClass
        .EPISTEMICALLY_SOVEREIGN
    )


__all__ = [
    "AggregatedStrategicMetrics",
    "aggregate",
    "classify",
    "gate_failing_conditions",
    "gate_passes_all",
]
