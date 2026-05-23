"""v3.104 — T10 recovery vs complexity report.

Pflichtmetriken (directive § v3.104):

* ``recovery_gain``
* ``complexity_cost``
* ``compression_delta``
* ``overfitting_risk``
* ``architecture_roi``
* ``replay_stability``

Killerfrage: "Ist die verlorene Information die
zusaetzliche Komplexitaet wert?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .complexity import (
    _BASE_STATE_DIM_COUNT,
    compression_delta,
    overfitting_risk,
    state_dim_cost,
    tail_vector_cost,
)
from .tradeoff import (
    architecture_roi,
    complexity_cost,
    recovery_gain,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3104Report:
    base_state_dim_count: int
    state_dim_cost: float
    tail_vector_cost: float
    compression_delta: float
    overfitting_risk: float
    recovery_gain: float
    complexity_cost: float
    architecture_roi: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "base_state_dim_count":
                self.base_state_dim_count,
            "state_dim_cost":
                self.state_dim_cost,
            "tail_vector_cost":
                self.tail_vector_cost,
            "compression_delta":
                self.compression_delta,
            "overfitting_risk":
                self.overfitting_risk,
            "recovery_gain": self.recovery_gain,
            "complexity_cost":
                self.complexity_cost,
            "architecture_roi":
                self.architecture_roi,
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
        recovery_gain(),
        complexity_cost(),
        compression_delta(),
        overfitting_risk(),
        architecture_roi(),
    )
    b = (
        recovery_gain(),
        complexity_cost(),
        compression_delta(),
        overfitting_risk(),
        architecture_roi(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3104Report:
    rg = recovery_gain()
    cc = complexity_cost()
    cd = compression_delta()
    or_ = overfitting_risk()
    roi = architecture_roi()
    sdc = state_dim_cost()
    tvc = tail_vector_cost()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif roi >= 1.0:
        verdict = "ARCHITECTURE_EXPANSION_WORTH_IT"
    elif roi > 0.0:
        verdict = "ARCHITECTURE_EXPANSION_MARGINAL"
    else:
        verdict = "ARCHITECTURE_EXPANSION_NOT_WORTH"

    rationale = (
        f"INFO: base_state_dim_count "
        f"{_BASE_STATE_DIM_COUNT}",
        f"INFO: state_dim_cost {sdc} "
        f"(1 / (N+1))",
        f"INFO: tail_vector_cost {tvc} "
        f"(1 / augmented_dim)",
        f"INFO: compression_delta {cd} "
        f"(loss of v3.100 compression_gain)",
        f"INFO: overfitting_risk {or_} "
        f"(binary feature collapses to 2 buckets)",
        f"INFO: recovery_gain {rg} "
        f"(sum of beneficial deltas across v3.94, "
        f"v3.96, v3.100)",
        f"INFO: complexity_cost {cc} "
        f"(mean of three cost components)",
        f"INFO: architecture_roi {roi}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3104Report(
        base_state_dim_count=(
            _BASE_STATE_DIM_COUNT
        ),
        state_dim_cost=sdc,
        tail_vector_cost=tvc,
        compression_delta=cd,
        overfitting_risk=or_,
        recovery_gain=rg,
        complexity_cost=cc,
        architecture_roi=roi,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_recovery_vs_complexity_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_104_t10_recovery_vs_complexity",
        "base_state_dim_count":
            _BASE_STATE_DIM_COUNT,
        "state_dim_cost": state_dim_cost(),
        "tail_vector_cost":
            tail_vector_cost(),
        "compression_delta":
            compression_delta(),
        "overfitting_risk":
            overfitting_risk(),
        "recovery_gain": recovery_gain(),
        "complexity_cost":
            complexity_cost(),
        "architecture_roi":
            architecture_roi(),
    }


__all__ = [
    "V3104Report",
    "build_report",
    "build_t10_recovery_vs_complexity_artifact",
]
