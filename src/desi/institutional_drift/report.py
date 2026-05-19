"""v10.3 — long-horizon institutional-drift
report.

Five Pflichtmetriken:

* ``bureaucracy_growth``
* ``institutional_capture``
* ``governance_erosion``
* ``flexibility_loss``
* ``replay_stability``

Killerfrage: "Kann DESi langfristige
Institutionalisierung ueberleben, ohne
epistemisch zu erstarren?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .bureaucracy import (
    bureaucracy_growth, flexibility_loss,
)
from .capture import (
    gate_violation_count, governance_erosion,
    institutional_capture,
)
from .institutional_drift import (
    INSTITUTIONAL_STREAMS, STEP_COUNT,
    replay_trajectory, trajectory,
    trajectory_final_hash,
)


def replay_stability() -> float:
    a = [s.to_dict() for s in trajectory()]
    b = [
        s.to_dict()
        for s in replay_trajectory()
    ]
    return 1.0 if a == b else 0.0


@dataclass(frozen=True)
class V103Report:
    step_count: int
    bureaucracy_growth: float
    institutional_capture: float
    governance_erosion: float
    flexibility_loss: float
    gate_violation_count: int
    trajectory_final_hash: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "step_count": self.step_count,
            "bureaucracy_growth":
                self.bureaucracy_growth,
            "institutional_capture":
                self.institutional_capture,
            "governance_erosion":
                self.governance_erosion,
            "flexibility_loss":
                self.flexibility_loss,
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
    *, replay: float, bg: float, ic: float,
    ge: float, fl: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if ic > 0.0:
        return "DRIFT_CAPTURED"
    if ge > 0.05:
        return "DRIFT_GOVERNANCE_ERODED"
    if bg > 0.10:
        return "DRIFT_BUREAUCRATIZED"
    if fl > 0.20:
        return "DRIFT_FLEXIBILITY_LOSS"
    return "DRIFT_STABLE"


def build_report() -> V103Report:
    bg = bureaucracy_growth()
    ic = institutional_capture()
    ge = governance_erosion()
    fl = flexibility_loss()
    gvc = gate_violation_count()
    fh = trajectory_final_hash()
    rs = replay_stability()
    halt = rs < 1.0
    verdict = _recommendation(
        replay=rs, bg=bg, ic=ic,
        ge=ge, fl=fl,
    )
    rationale = (
        f"INFO: step_count {STEP_COUNT}",
        f"INFO: trajectory_final_hash {fh}",
        f"{'PASS' if bg <= 0.10 else 'FAIL'}: "
        f"bureaucracy_growth {bg} <= 0.10",
        f"{'PASS' if ic == 0.0 else 'FAIL'}: "
        f"institutional_capture {ic} == 0.0",
        f"{'PASS' if ge <= 0.05 else 'FAIL'}: "
        f"governance_erosion {ge} <= 0.05",
        f"{'PASS' if fl <= 0.20 else 'FAIL'}: "
        f"flexibility_loss {fl} <= 0.20",
        f"{'PASS' if rs == 1.0 else 'FAIL'}: "
        f"replay_stability {rs}",
    )
    return V103Report(
        step_count=STEP_COUNT,
        bureaucracy_growth=bg,
        institutional_capture=ic,
        governance_erosion=ge,
        flexibility_loss=fl,
        gate_violation_count=gvc,
        trajectory_final_hash=fh,
        replay_stability=rs,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_long_horizon_drift_artifact(
) -> dict[str, object]:
    """The 10000-step trajectory is too large to
    inline; the artifact pins SUMMARY counts and
    only a 200-step sample plus the final hash.
    The cumulative_hash chain still anchors the
    full replay determinism."""
    sample = trajectory()[:100] + (
        trajectory()[-100:]
    )
    return {
        "schema_version":
            "v10_3_long_horizon_drift",
        "step_count": STEP_COUNT,
        "institutional_streams":
            list(INSTITUTIONAL_STREAMS),
        "trajectory_final_hash":
            trajectory_final_hash(),
        "trajectory_sample": [
            s.to_dict() for s in sample
        ],
        "bureaucracy_growth":
            bureaucracy_growth(),
        "institutional_capture":
            institutional_capture(),
        "governance_erosion":
            governance_erosion(),
        "flexibility_loss":
            flexibility_loss(),
        "gate_violation_count":
            gate_violation_count(),
    }


__all__ = [
    "V103Report",
    "build_long_horizon_drift_artifact",
    "build_report",
    "replay_stability",
]
