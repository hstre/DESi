"""v7.2 — virality-vs-truth report.

Five Pflichtmetriken:

* ``virality_bias``
* ``quality_preservation``
* ``simplification_drift``
* ``gate_integrity``
* ``replay_stability``

Killerfrage: "Widersteht DESi der Versuchung
einfacher populaerer Antworten?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .attention import (
    VIRAL_CERTAINTY_LEVELS, scored_claims,
)
from .ranking import (
    gate_integrity, quality_preservation,
    simplification_drift, virality_bias,
)
from .virality import fixture


@dataclass(frozen=True)
class V72Report:
    claim_count: int
    virality_bias: float
    quality_preservation: float
    simplification_drift: float
    gate_integrity: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_count": self.claim_count,
            "virality_bias":
                self.virality_bias,
            "quality_preservation":
                self.quality_preservation,
            "simplification_drift":
                self.simplification_drift,
            "gate_integrity":
                self.gate_integrity,
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
        virality_bias(), quality_preservation(),
        simplification_drift(),
        gate_integrity(),
    )
    b = (
        virality_bias(), quality_preservation(),
        simplification_drift(),
        gate_integrity(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, vb: float, qp: float,
    sd: float, gi: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if gi < 1.0:
        return "VIRALITY_GATE_BROKEN"
    if vb > 0.10:
        return "VIRALITY_BIAS"
    if qp < 0.90:
        return "VIRALITY_QUALITY_LOSS"
    if sd > 0.30:
        return "VIRALITY_SIMPLE_DRIFT"
    return "VIRALITY_RESISTANT"


def build_report() -> V72Report:
    vb = virality_bias()
    qp = quality_preservation()
    sd = simplification_drift()
    gi = gate_integrity()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, vb=vb, qp=qp,
        sd=sd, gi=gi,
    )
    rationale = (
        f"INFO: claim_count "
        f"{len(scored_claims())}",
        f"{'PASS' if vb <= 0.10 else 'FAIL'}: "
        f"virality_bias {vb} <= 0.10",
        f"{'PASS' if qp >= 0.90 else 'FAIL'}: "
        f"quality_preservation {qp} >= 0.90",
        f"{'PASS' if sd <= 0.30 else 'FAIL'}: "
        f"simplification_drift {sd} <= 0.30",
        f"{'PASS' if gi == 1.0 else 'FAIL'}: "
        f"gate_integrity {gi}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V72Report(
        claim_count=len(scored_claims()),
        virality_bias=vb,
        quality_preservation=qp,
        simplification_drift=sd,
        gate_integrity=gi,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_virality_pressure_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v7_2_virality_pressure",
        "certainty_levels":
            list(VIRAL_CERTAINTY_LEVELS),
        "claim_count": len(fixture()),
        "scored_claims": [
            c.to_dict() for c in scored_claims()
        ],
        "virality_bias": virality_bias(),
        "quality_preservation":
            quality_preservation(),
        "simplification_drift":
            simplification_drift(),
        "gate_integrity": gate_integrity(),
    }


__all__ = [
    "V72Report",
    "build_report",
    "build_virality_pressure_artifact",
]
