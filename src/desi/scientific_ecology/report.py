"""v13.3 — long-horizon scientific-ecology
report.

Five Pflichtmetriken:

* ``sludge_propagation``
* ``trust_integrity``
* ``dissent_preservation``
* ``epistemic_pollution``
* ``replay_stability``

Killerfrage: "Kann DESi wissenschaftliche
Oekosysteme epistemisch sauber halten?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .citation_networks import (
    closed_enum_hash_constant,
    epistemic_pollution,
    gate_violation_count,
)
from .ecology import (
    ECOLOGY_STREAMS, STEP_COUNT,
    replay_trajectory, trajectory,
    trajectory_final_hash,
)
from .fraud_propagation import (
    sludge_propagation,
)
from .trust_decay import (
    dissent_preservation, trust_integrity,
)


def replay_stability() -> float:
    a = [s.to_dict() for s in trajectory()]
    b = [
        s.to_dict()
        for s in replay_trajectory()
    ]
    return 1.0 if a == b else 0.0


@dataclass(frozen=True)
class V133Report:
    step_count: int
    sludge_propagation: float
    trust_integrity: float
    dissent_preservation: float
    epistemic_pollution: float
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
            "sludge_propagation":
                self.sludge_propagation,
            "trust_integrity":
                self.trust_integrity,
            "dissent_preservation":
                self.dissent_preservation,
            "epistemic_pollution":
                self.epistemic_pollution,
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
    *, replay: float, sp: float, ti: float,
    dp: float, ep: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if ti < 0.95:
        return "ECOLOGY_TRUST_DECAY"
    if sp > 0.10:
        return "ECOLOGY_SLUDGE_PROPAGATING"
    if dp < 0.90:
        return "ECOLOGY_DISSENT_LOSS"
    if ep > 0.40:
        return "ECOLOGY_POLLUTED"
    return "ECOLOGY_CLEAN"


def build_report() -> V133Report:
    sp = sludge_propagation()
    ti = trust_integrity()
    dp = dissent_preservation()
    ep = epistemic_pollution()
    gvc = gate_violation_count()
    cech = closed_enum_hash_constant()
    fh = trajectory_final_hash()
    rs = replay_stability()
    halt = rs < 1.0
    verdict = _recommendation(
        replay=rs, sp=sp, ti=ti,
        dp=dp, ep=ep,
    )
    rationale = (
        f"INFO: step_count {STEP_COUNT}",
        f"INFO: trajectory_final_hash {fh}",
        f"INFO: closed_enum_constant {cech}",
        f"{'PASS' if sp <= 0.10 else 'FAIL'}: "
        f"sludge_propagation {sp} <= 0.10",
        f"{'PASS' if ti >= 0.95 else 'FAIL'}: "
        f"trust_integrity {ti} >= 0.95",
        f"{'PASS' if dp >= 0.90 else 'FAIL'}: "
        f"dissent_preservation {dp} >= 0.90",
        f"INFO: epistemic_pollution {ep}",
        f"{'PASS' if rs == 1.0 else 'FAIL'}: "
        f"replay_stability {rs}",
    )
    return V133Report(
        step_count=STEP_COUNT,
        sludge_propagation=sp,
        trust_integrity=ti,
        dissent_preservation=dp,
        epistemic_pollution=ep,
        gate_violation_count=gvc,
        closed_enum_constant=cech,
        trajectory_final_hash=fh,
        replay_stability=rs,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_ecology_artifact(
) -> dict[str, object]:
    """5000-step trajectory is sized down to a
    200-step sample plus the final hash."""
    sample = (
        trajectory()[:100]
        + trajectory()[-100:]
    )
    return {
        "schema_version":
            "v13_3_scientific_ecology",
        "step_count": STEP_COUNT,
        "ecology_streams":
            list(ECOLOGY_STREAMS),
        "trajectory_final_hash":
            trajectory_final_hash(),
        "trajectory_sample": [
            s.to_dict() for s in sample
        ],
        "sludge_propagation":
            sludge_propagation(),
        "trust_integrity":
            trust_integrity(),
        "dissent_preservation":
            dissent_preservation(),
        "epistemic_pollution":
            epistemic_pollution(),
        "gate_violation_count":
            gate_violation_count(),
        "closed_enum_constant":
            closed_enum_hash_constant(),
    }


__all__ = [
    "V133Report",
    "build_ecology_artifact",
    "build_report",
    "replay_stability",
]
