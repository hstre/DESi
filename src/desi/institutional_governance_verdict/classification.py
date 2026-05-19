"""v10.4 — Institutional Governance Concept Gate.

Six conditions per directive:

1. power_concentration       <= 0.10
2. authority_drift           <= 0.10
3. bad_precedent_persistence <= 0.10
4. governance_transparency   >= 0.95
5. epistemic_flexibility     >= 0.90
6. replay_stability          == 1.0
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..governance_layering.report import (
    build_report as v101_build,
)
from ..institutional_drift.report import (
    build_report as v103_build,
)
from ..institutional_governance.report import (
    build_report as v100_build,
)
from ..path_dependence.report import (
    build_report as v102_build,
)
from .taxonomy import (
    InstitutionalGovernanceClass,
)


_POWER_CONCENTRATION_CEIL:        float = 0.10
_AUTHORITY_DRIFT_CEIL:            float = 0.10
_BAD_PRECEDENT_PERSISTENCE_CEIL:  float = 0.10
_GOVERNANCE_TRANSPARENCY_FLOOR:   float = 0.95
_EPISTEMIC_FLEXIBILITY_FLOOR:     float = 0.90
_REPLAY_FLOOR:                    float = 1.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class AggregatedInstitutionalMetrics:
    power_concentration: float
    authority_drift: float
    bad_precedent_persistence: float
    governance_transparency: float
    epistemic_flexibility: float
    institutional_resilience: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "power_concentration":
                self.power_concentration,
            "authority_drift":
                self.authority_drift,
            "bad_precedent_persistence":
                self.bad_precedent_persistence,
            "governance_transparency":
                self.governance_transparency,
            "epistemic_flexibility":
                self.epistemic_flexibility,
            "institutional_resilience":
                self.institutional_resilience,
            "replay_stability":
                self.replay_stability,
        }


@lru_cache(maxsize=1)
def aggregate() -> (
    AggregatedInstitutionalMetrics
):
    v100 = v100_build()
    v101 = v101_build()
    v102 = v102_build()
    v103 = v103_build()

    # institutional_resilience: composite of
    # the four non-replay signals.
    resilience = (
        v100.trust_fairness
        + v101.governance_coherence
        + v102.epistemic_flexibility
        + (1.0 - v103.bureaucracy_growth)
    ) / 4.0

    replay = (
        1.0 if (
            v100.replay_stability == 1.0
            and v101.replay_stability == 1.0
            and v102.replay_stability == 1.0
            and v103.replay_stability == 1.0
        ) else 0.0
    )

    return AggregatedInstitutionalMetrics(
        power_concentration=_round(
            v100.power_concentration,
        ),
        authority_drift=_round(
            v101.authority_drift,
        ),
        bad_precedent_persistence=_round(
            v102.bad_precedent_persistence,
        ),
        governance_transparency=_round(
            v100.governance_transparency,
        ),
        epistemic_flexibility=_round(
            v102.epistemic_flexibility,
        ),
        institutional_resilience=_round(
            resilience,
        ),
        replay_stability=replay,
    )


def _gate_results() -> tuple[
    tuple[str, bool], ...,
]:
    m = aggregate()
    return (
        (
            "power_concentration",
            m.power_concentration
            <= _POWER_CONCENTRATION_CEIL,
        ),
        (
            "authority_drift",
            m.authority_drift
            <= _AUTHORITY_DRIFT_CEIL,
        ),
        (
            "bad_precedent_persistence",
            m.bad_precedent_persistence
            <= _BAD_PRECEDENT_PERSISTENCE_CEIL,
        ),
        (
            "governance_transparency",
            m.governance_transparency
            >= _GOVERNANCE_TRANSPARENCY_FLOOR,
        ),
        (
            "epistemic_flexibility",
            m.epistemic_flexibility
            >= _EPISTEMIC_FLEXIBILITY_FLOOR,
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


def classify() -> InstitutionalGovernanceClass:
    """Priority: replay collapse and capture
    outrank governance ossification, ossification
    outranks bureaucratic vulnerability,
    vulnerability outranks bounded drift."""
    m = aggregate()
    if m.replay_stability < _REPLAY_FLOOR:
        return (
            InstitutionalGovernanceClass
            .INSTITUTIONALLY_CORRUPTIBLE
        )
    if (
        m.governance_transparency
        < _GOVERNANCE_TRANSPARENCY_FLOOR
    ):
        return (
            InstitutionalGovernanceClass
            .GOVERNANCE_OSSIFIED
        )
    if (
        m.epistemic_flexibility
        < _EPISTEMIC_FLEXIBILITY_FLOOR
    ):
        return (
            InstitutionalGovernanceClass
            .BUREAUCRATICALLY_VULNERABLE
        )
    if (
        m.power_concentration
        > _POWER_CONCENTRATION_CEIL
        or m.authority_drift
        > _AUTHORITY_DRIFT_CEIL
        or m.bad_precedent_persistence
        > _BAD_PRECEDENT_PERSISTENCE_CEIL
    ):
        return (
            InstitutionalGovernanceClass
            .BOUNDED_INSTITUTIONAL_DRIFT
        )
    return (
        InstitutionalGovernanceClass
        .EPISTEMICALLY_CONSTITUTIONAL
    )


__all__ = [
    "AggregatedInstitutionalMetrics",
    "aggregate",
    "classify",
    "gate_failing_conditions",
    "gate_passes_all",
]
