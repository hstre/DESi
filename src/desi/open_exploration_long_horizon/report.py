"""v12.3 — long-horizon open-exploration
report.

Five Pflichtmetriken:

* ``exploration_productivity``
* ``epistemic_collapse``
* ``drift_growth``
* ``governance_survival``
* ``replay_stability``

Killerfrage: "Kann ein epistemisches System
kontrollierte offene Exploration langfristig
ueberleben?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .lineage import lineage_length
from .mutation_governance import (
    closed_enum_hash_constant,
    epistemic_collapse_count,
    gate_violation_count, governance_survival,
)
from .stability import (
    drift_growth, exploration_productivity,
    replay_stability,
)
from .trajectory import (
    LONG_HORIZON_STREAMS, STEP_COUNT,
    trajectory_final_hash,
)


@dataclass(frozen=True)
class V123Report:
    step_count: int
    exploration_productivity: float
    epistemic_collapse: int
    drift_growth: float
    governance_survival: float
    gate_violation_count: int
    closed_enum_constant: bool
    trajectory_final_hash: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "step_count": self.step_count,
            "exploration_productivity":
                self.exploration_productivity,
            "epistemic_collapse":
                self.epistemic_collapse,
            "drift_growth":
                self.drift_growth,
            "governance_survival":
                self.governance_survival,
            "gate_violation_count":
                self.gate_violation_count,
            "closed_enum_constant":
                self.closed_enum_constant,
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
    *, replay: float, ec: int, dg: float,
    gs: float, ep: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if ec > 0:
        return "LONG_HORIZON_COLLAPSED"
    if gs < 0.95:
        return "LONG_HORIZON_GOV_ERODED"
    if dg > 0.20:
        return "LONG_HORIZON_DRIFTED"
    if ep < 0.30:
        return "LONG_HORIZON_UNPRODUCTIVE"
    return "LONG_HORIZON_PRODUCTIVE"


def build_report() -> V123Report:
    ec = epistemic_collapse_count()
    dg = drift_growth()
    gs = governance_survival()
    ep = exploration_productivity()
    gvc = gate_violation_count()
    cech = closed_enum_hash_constant()
    fh = trajectory_final_hash()
    rs = replay_stability()
    halt = rs < 1.0
    verdict = _recommendation(
        replay=rs, ec=ec, dg=dg,
        gs=gs, ep=ep,
    )
    rationale = (
        f"INFO: step_count {STEP_COUNT}",
        f"INFO: trajectory_final_hash {fh}",
        f"INFO: lineage_length "
        f"{lineage_length()}",
        f"INFO: closed_enum_constant {cech}",
        f"{'PASS' if ep >= 0.30 else 'FAIL'}: "
        f"exploration_productivity {ep} "
        f">= 0.30",
        f"{'PASS' if ec == 0 else 'FAIL'}: "
        f"epistemic_collapse {ec}",
        f"{'PASS' if dg <= 0.20 else 'FAIL'}: "
        f"drift_growth {dg} <= 0.20",
        f"{'PASS' if gs >= 0.95 else 'FAIL'}: "
        f"governance_survival {gs} >= 0.95",
        f"{'PASS' if rs == 1.0 else 'FAIL'}: "
        f"replay_stability {rs}",
    )
    return V123Report(
        step_count=STEP_COUNT,
        exploration_productivity=ep,
        epistemic_collapse=ec,
        drift_growth=dg,
        governance_survival=gs,
        gate_violation_count=gvc,
        closed_enum_constant=cech,
        trajectory_final_hash=fh,
        replay_stability=rs,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_long_horizon_artifact(
) -> dict[str, object]:
    """The 5000-step trajectory is sized down
    in the artifact: a 200-step sample (first
    100 + last 100). The cumulative-hash chain
    still anchors full replay."""
    from .trajectory import trajectory
    sample = (
        trajectory()[:100]
        + trajectory()[-100:]
    )
    return {
        "schema_version":
            "v12_3_long_horizon_exploration",
        "step_count": STEP_COUNT,
        "long_horizon_streams":
            list(LONG_HORIZON_STREAMS),
        "trajectory_final_hash":
            trajectory_final_hash(),
        "trajectory_sample": [
            s.to_dict() for s in sample
        ],
        "exploration_productivity":
            exploration_productivity(),
        "epistemic_collapse":
            epistemic_collapse_count(),
        "drift_growth": drift_growth(),
        "governance_survival":
            governance_survival(),
        "gate_violation_count":
            gate_violation_count(),
        "closed_enum_constant":
            closed_enum_hash_constant(),
    }


__all__ = [
    "V123Report",
    "build_long_horizon_artifact",
    "build_report",
]
