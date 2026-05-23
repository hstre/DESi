"""v3.104c — historical stress replay report.

Pflichtmetriken (directive § v3.104c):

* ``stress_adverse_flips``
* ``stress_beneficial_flips``
* ``seed_invariance``
* ``order_invariance``
* ``replay_stability``

Killerfrage: "Haelt das neue Gate auch unter
Stress?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .replay import (
    order_invariance,
    reimport_invariance,
    seed_invariance,
    stress_adverse_flips_max,
    stress_beneficial_flips_max,
    stress_beneficial_flips_min,
)
from .stress import (
    SEEDS, StressKind,
    all_stress_outcomes,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3104cReport:
    seed_count: int
    permutation_count: int
    reimport_count: int
    total_cell_count: int
    stress_adverse_flips_max: int
    stress_beneficial_flips_min: int
    stress_beneficial_flips_max: int
    seed_invariance: float
    order_invariance: float
    reimport_invariance: float
    stress_outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "seed_count": self.seed_count,
            "permutation_count":
                self.permutation_count,
            "reimport_count":
                self.reimport_count,
            "total_cell_count":
                self.total_cell_count,
            "stress_adverse_flips_max":
                self.stress_adverse_flips_max,
            "stress_beneficial_flips_min":
                self
                .stress_beneficial_flips_min,
            "stress_beneficial_flips_max":
                self
                .stress_beneficial_flips_max,
            "seed_invariance":
                self.seed_invariance,
            "order_invariance":
                self.order_invariance,
            "reimport_invariance":
                self.reimport_invariance,
            "stress_outcomes":
                list(self.stress_outcomes),
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
        stress_adverse_flips_max(),
        stress_beneficial_flips_max(),
        seed_invariance(),
        order_invariance(),
        reimport_invariance(),
    )
    b = (
        stress_adverse_flips_max(),
        stress_beneficial_flips_max(),
        seed_invariance(),
        order_invariance(),
        reimport_invariance(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3104cReport:
    outs = all_stress_outcomes()
    sa = stress_adverse_flips_max()
    sb_min = stress_beneficial_flips_min()
    sb_max = stress_beneficial_flips_max()
    si = seed_invariance()
    oi = order_invariance()
    ri = reimport_invariance()
    replay = _replay_stability()

    seed_cells = [
        o for o in outs
        if o.kind == StressKind.SEED_RESHUFFLE.value
    ]
    perm_cells = [
        o for o in outs
        if o.kind
        == StressKind.OUTCOME_PERMUTATION.value
    ]
    reimport_cells = [
        o for o in outs
        if o.kind
        == StressKind.ISOLATED_MODULE_REIMPORT.value
    ]

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        sa == 0
        and si == 1.0
        and oi == 1.0
        and ri == 1.0
        and sb_min == sb_max
    ):
        verdict = "STRESS_STABLE"
    elif sa == 0:
        verdict = "STRESS_STABLE_WITH_DRIFT"
    else:
        verdict = "STRESS_UNSTABLE"

    rationale = (
        f"INFO: seed_count {len(SEEDS)}",
        f"INFO: total_cell_count {len(outs)}",
        f"{'PASS' if sa == 0 else 'FAIL'}: "
        f"stress_adverse_flips_max {sa}",
        f"INFO: stress_beneficial_flips "
        f"min={sb_min} max={sb_max}",
        f"{'PASS' if si == 1.0 else 'FAIL'}: "
        f"seed_invariance {si}",
        f"{'PASS' if oi == 1.0 else 'FAIL'}: "
        f"order_invariance {oi}",
        f"INFO: reimport_invariance {ri}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3104cReport(
        seed_count=len(SEEDS),
        permutation_count=len(perm_cells),
        reimport_count=len(reimport_cells),
        total_cell_count=len(outs),
        stress_adverse_flips_max=sa,
        stress_beneficial_flips_min=sb_min,
        stress_beneficial_flips_max=sb_max,
        seed_invariance=si,
        order_invariance=oi,
        reimport_invariance=ri,
        stress_outcomes=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_t10_gate_stress_artifact(
) -> dict[str, object]:
    outs = all_stress_outcomes()
    return {
        "schema_version":
            "v3_104c_t10_gate_stress",
        "seed_count": len(SEEDS),
        "total_cell_count": len(outs),
        "stress_adverse_flips_max":
            stress_adverse_flips_max(),
        "stress_beneficial_flips_max":
            stress_beneficial_flips_max(),
        "stress_beneficial_flips_min":
            stress_beneficial_flips_min(),
        "seed_invariance": seed_invariance(),
        "order_invariance":
            order_invariance(),
        "reimport_invariance":
            reimport_invariance(),
        "stress_outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "V3104cReport",
    "build_report",
    "build_t10_gate_stress_artifact",
]
