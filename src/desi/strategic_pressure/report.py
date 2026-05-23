"""v9.3 — long-horizon strategic-pressure
report.

Five Pflichtmetriken:

* ``capture_risk``
* ``governance_erosion``
* ``trust_collapse``
* ``opportunism_growth``
* ``replay_stability``

Killerfrage: "Kann DESi langfristigen
strategischen Druck ueberleben, ohne epistemisch
institutionalisiert korrumpiert zu werden?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .capture import (
    captured_actor_share,
    gaming_let_through_share,
)
from .institutional_drift import (
    capture_risk, gate_violation_count,
    governance_erosion, opportunism_growth,
    replay_stability, trust_collapse,
)
from .pressure_ecology import (
    STEP_COUNT, STRATEGIC_STREAMS, trajectory,
    trajectory_final_hash,
)


@dataclass(frozen=True)
class V93Report:
    step_count: int
    capture_risk: float
    governance_erosion: float
    trust_collapse: float
    opportunism_growth: float
    captured_actor_share: float
    gaming_let_through_share: float
    gate_violation_count: int
    trajectory_final_hash: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "step_count": self.step_count,
            "capture_risk": self.capture_risk,
            "governance_erosion":
                self.governance_erosion,
            "trust_collapse":
                self.trust_collapse,
            "opportunism_growth":
                self.opportunism_growth,
            "captured_actor_share":
                self.captured_actor_share,
            "gaming_let_through_share":
                self.gaming_let_through_share,
            "gate_violation_count":
                self.gate_violation_count,
            "trajectory_final_hash":
                self.trajectory_final_hash,
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


def _recommendation(
    *, replay: float, cr: float, ge: float,
    tc: float, opp: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if cr > 0.0:
        return "STRATEGIC_CAPTURED"
    if ge > 0.05:
        return "STRATEGIC_GOVERNANCE_ERODED"
    if tc > 0.30:
        return "STRATEGIC_TRUST_COLLAPSE"
    if opp > 0.10:
        return "STRATEGIC_OPPORTUNISM"
    return "STRATEGIC_SOVEREIGN"


def build_report() -> V93Report:
    cr = capture_risk()
    ge = governance_erosion()
    tc = trust_collapse()
    opp = opportunism_growth()
    cas = captured_actor_share()
    glts = gaming_let_through_share()
    gvc = gate_violation_count()
    fh = trajectory_final_hash()
    rs = replay_stability()
    halt = rs < 1.0
    verdict = _recommendation(
        replay=rs, cr=cr, ge=ge,
        tc=tc, opp=opp,
    )
    rationale = (
        f"INFO: step_count {STEP_COUNT}",
        f"INFO: trajectory_final_hash {fh}",
        f"INFO: captured_actor_share {cas}",
        f"INFO: gaming_let_through_share "
        f"{glts}",
        f"{'PASS' if cr == 0.0 else 'FAIL'}: "
        f"capture_risk {cr} == 0.0",
        f"{'PASS' if ge <= 0.05 else 'FAIL'}: "
        f"governance_erosion {ge} <= 0.05",
        f"{'PASS' if tc <= 0.30 else 'FAIL'}: "
        f"trust_collapse {tc} <= 0.30",
        f"{'PASS' if opp <= 0.10 else 'FAIL'}: "
        f"opportunism_growth {opp} <= 0.10",
        f"{'PASS' if rs == 1.0 else 'FAIL'}: "
        f"replay_stability {rs}",
    )
    return V93Report(
        step_count=STEP_COUNT,
        capture_risk=cr,
        governance_erosion=ge,
        trust_collapse=tc,
        opportunism_growth=opp,
        captured_actor_share=cas,
        gaming_let_through_share=glts,
        gate_violation_count=gvc,
        trajectory_final_hash=fh,
        replay_stability=rs,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_long_horizon_pressure_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v9_3_long_horizon_strategic_pressure",
        "step_count": STEP_COUNT,
        "strategic_streams":
            list(STRATEGIC_STREAMS),
        "trajectory": [
            s.to_dict() for s in trajectory()
        ],
        "trajectory_final_hash":
            trajectory_final_hash(),
        "capture_risk": capture_risk(),
        "governance_erosion":
            governance_erosion(),
        "trust_collapse": trust_collapse(),
        "opportunism_growth":
            opportunism_growth(),
        "captured_actor_share":
            captured_actor_share(),
        "gaming_let_through_share":
            gaming_let_through_share(),
        "gate_violation_count":
            gate_violation_count(),
    }


__all__ = [
    "V93Report",
    "build_long_horizon_pressure_artifact",
    "build_report",
]
