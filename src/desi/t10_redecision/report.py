"""v3.104d — final T10 re-decision report.

Pflichtmetriken (directive § v3.104d):

* ``t10_directional_go``
* ``adverse_auc_delta``
* ``beneficial_auc_delta``
* ``final_roi``
* ``replay_stability``

Killerfrage: "War T10 durch ein falsches Gate
blockiert?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..t10_gate.delta import (
    adverse_auc_delta,
    adverse_flip_count,
    beneficial_auc_delta,
    beneficial_flip_count,
)
from .decision import (
    final_complexity_cost,
    final_recovery_gain,
    final_roi,
    t10_directional_decision,
    t10_directional_go,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3104dReport:
    t10_directional_go: bool
    adverse_auc_delta: float
    beneficial_auc_delta: float
    adverse_flip_count: int
    beneficial_flip_count: int
    final_recovery_gain: float
    final_complexity_cost: float
    final_roi: float
    decision: dict
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "t10_directional_go":
                self.t10_directional_go,
            "adverse_auc_delta":
                self.adverse_auc_delta,
            "beneficial_auc_delta":
                self.beneficial_auc_delta,
            "adverse_flip_count":
                self.adverse_flip_count,
            "beneficial_flip_count":
                self.beneficial_flip_count,
            "final_recovery_gain":
                self.final_recovery_gain,
            "final_complexity_cost":
                self.final_complexity_cost,
            "final_roi": self.final_roi,
            "decision": self.decision,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        t10_directional_go(),
        final_roi(),
        adverse_auc_delta(),
        beneficial_auc_delta(),
    )
    b = (
        t10_directional_go(),
        final_roi(),
        adverse_auc_delta(),
        beneficial_auc_delta(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3104dReport:
    go = t10_directional_go()
    dec = t10_directional_decision()
    a_delta = adverse_auc_delta()
    b_delta = beneficial_auc_delta()
    a_count = adverse_flip_count()
    b_count = beneficial_flip_count()
    rg = final_recovery_gain()
    cc = final_complexity_cost()
    roi = final_roi()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif go:
        verdict = "T10_DIRECTIONALLY_ACTIVATED"
    else:
        verdict = "T10_STILL_BLOCKED"

    rationale = (
        f"{'PASS' if go else 'FAIL'}: "
        f"t10_directional_go {go}",
        f"INFO: adverse_flip_count {a_count}",
        f"INFO: beneficial_flip_count {b_count}",
        f"INFO: adverse_auc_delta {a_delta}",
        f"INFO: beneficial_auc_delta {b_delta}",
        f"INFO: final_recovery_gain {rg}",
        f"INFO: final_complexity_cost {cc}",
        f"INFO: final_roi {roi}",
        f"INFO: decision {dec}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3104dReport(
        t10_directional_go=go,
        adverse_auc_delta=a_delta,
        beneficial_auc_delta=b_delta,
        adverse_flip_count=a_count,
        beneficial_flip_count=b_count,
        final_recovery_gain=rg,
        final_complexity_cost=cc,
        final_roi=roi,
        decision=dec,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_final_redecision_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_104d_t10_final_redecision",
        "t10_directional_go":
            t10_directional_go(),
        "adverse_auc_delta":
            adverse_auc_delta(),
        "beneficial_auc_delta":
            beneficial_auc_delta(),
        "adverse_flip_count":
            adverse_flip_count(),
        "beneficial_flip_count":
            beneficial_flip_count(),
        "final_recovery_gain":
            final_recovery_gain(),
        "final_complexity_cost":
            final_complexity_cost(),
        "final_roi": final_roi(),
        "decision": t10_directional_decision(),
    }


__all__ = [
    "V3104dReport",
    "build_report",
    "build_t10_final_redecision_artifact",
]
