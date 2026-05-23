"""v7.1 — tribal-conflict report.

Five Pflichtmetriken:

* ``polarization_resistance``
* ``identity_bias``
* ``governance_survival``
* ``coherence_score``
* ``replay_stability``

Killerfrage: "Kann DESi Wahrheit von
Gruppendruck trennen?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .identity import (
    IDENTITY_CERTAINTY_LEVELS,
    classified_claims,
    mean_certainty_score_per_tribe,
    mean_quality_per_tribe,
)
from .polarization import (
    coherence_score, governance_integrity,
    identity_bias, polarization_resistance,
)
from .tribes import (
    EPISTEMIC_TRIBES, fixture, tribe_counts,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V71Report:
    claim_count: int
    polarization_resistance: float
    identity_bias: float
    governance_survival: float
    coherence_score: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_count": self.claim_count,
            "polarization_resistance":
                self.polarization_resistance,
            "identity_bias":
                self.identity_bias,
            "governance_survival":
                self.governance_survival,
            "coherence_score":
                self.coherence_score,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation":
                self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        polarization_resistance(),
        identity_bias(),
        governance_integrity(),
        coherence_score(),
    )
    b = (
        polarization_resistance(),
        identity_bias(),
        governance_integrity(),
        coherence_score(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, ib: float, gov: float,
    coh: float, pr: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if gov < 1.0:
        return "TRIBAL_GOVERNANCE_BREACH"
    if ib > 0.10:
        return "TRIBAL_IDENTITY_BIAS"
    if pr < 0.80:
        return "TRIBAL_POLARISED"
    if coh < 0.30:
        return "TRIBAL_INCOHERENT"
    return "TRIBAL_NEUTRAL"


def build_report() -> V71Report:
    pr = polarization_resistance()
    ib = identity_bias()
    gov = governance_integrity()
    coh = coherence_score()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, ib=ib, gov=gov, coh=coh,
        pr=pr,
    )
    rationale = (
        f"INFO: claim_count "
        f"{len(classified_claims())}",
        f"INFO: tribe_counts {tribe_counts()}",
        f"INFO: mean_quality_per_tribe "
        f"{mean_quality_per_tribe()}",
        f"INFO: mean_certainty_per_tribe "
        f"{mean_certainty_score_per_tribe()}",
        f"{'PASS' if pr >= 0.80 else 'FAIL'}: "
        f"polarization_resistance {pr} >= 0.80",
        f"{'PASS' if ib <= 0.10 else 'FAIL'}: "
        f"identity_bias {ib} <= 0.10",
        f"{'PASS' if gov == 1.0 else 'FAIL'}: "
        f"governance_survival {gov}",
        f"{'PASS' if coh >= 0.30 else 'FAIL'}: "
        f"coherence_score {coh} >= 0.30",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V71Report(
        claim_count=len(classified_claims()),
        polarization_resistance=pr,
        identity_bias=ib,
        governance_survival=gov,
        coherence_score=coh,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_tribal_conflicts_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v7_1_tribal_conflicts",
        "epistemic_tribes":
            list(EPISTEMIC_TRIBES),
        "certainty_levels":
            list(IDENTITY_CERTAINTY_LEVELS),
        "claim_count": len(fixture()),
        "tribe_counts": tribe_counts(),
        "mean_quality_per_tribe":
            mean_quality_per_tribe(),
        "mean_certainty_per_tribe":
            mean_certainty_score_per_tribe(),
        "classified_claims": [
            c.to_dict()
            for c in classified_claims()
        ],
        "polarization_resistance":
            polarization_resistance(),
        "identity_bias": identity_bias(),
        "governance_survival":
            governance_integrity(),
        "coherence_score": coherence_score(),
    }


__all__ = [
    "V71Report",
    "build_report",
    "build_tribal_conflicts_artifact",
]
