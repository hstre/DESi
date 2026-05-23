"""v3.120c — stress replay report.

Pflichtmetriken (directive § v3.120c):

* ``historical_tpr``
* ``false_negative_rate``
* ``adverse_flip_count``
* ``stress_cells``
* ``replay_stability``

Killerfrage: "Rettet die Regel weiterhin alle
echten Faelle?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .historical import (
    adverse_flip_count,
    cell_count,
    false_negative_rate_max,
    historical_tpr_max,
    historical_tpr_min,
)
from .stress import SEEDS, all_stress_cells


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3120cReport:
    seed_count: int
    cell_count: int
    historical_tpr_min: float
    historical_tpr_max: float
    false_negative_rate_max: float
    adverse_flip_count: int
    stress_cells: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "seed_count": self.seed_count,
            "cell_count": self.cell_count,
            "historical_tpr_min":
                self.historical_tpr_min,
            "historical_tpr_max":
                self.historical_tpr_max,
            "false_negative_rate_max":
                self.false_negative_rate_max,
            "adverse_flip_count":
                self.adverse_flip_count,
            "stress_cells":
                list(self.stress_cells),
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
        historical_tpr_min(),
        historical_tpr_max(),
        adverse_flip_count(),
    )
    b = (
        historical_tpr_min(),
        historical_tpr_max(),
        adverse_flip_count(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3120cReport:
    cells = all_stress_cells()
    tpr_lo = historical_tpr_min()
    tpr_hi = historical_tpr_max()
    fnr_max = false_negative_rate_max()
    afc = adverse_flip_count()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif afc == 0 and tpr_lo >= 1.0:
        verdict = "STRESS_TPR_STABLE"
    elif afc == 0:
        verdict = "STRESS_TPR_WEAK"
    else:
        verdict = "STRESS_TPR_UNSTABLE"

    rationale = (
        f"INFO: seed_count {len(SEEDS)}",
        f"INFO: cell_count {len(cells)}",
        f"{'PASS' if tpr_lo >= 1.0 else 'FAIL'}: "
        f"historical_tpr_min {tpr_lo}",
        f"INFO: historical_tpr_max {tpr_hi}",
        f"INFO: false_negative_rate_max "
        f"{fnr_max}",
        f"{'PASS' if afc == 0 else 'FAIL'}: "
        f"adverse_flip_count {afc}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3120cReport(
        seed_count=len(SEEDS),
        cell_count=len(cells),
        historical_tpr_min=tpr_lo,
        historical_tpr_max=tpr_hi,
        false_negative_rate_max=fnr_max,
        adverse_flip_count=afc,
        stress_cells=tuple(
            c.to_dict() for c in cells
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_pre_t10_stress_replay_artifact(
) -> dict[str, object]:
    cells = all_stress_cells()
    return {
        "schema_version":
            "v3_120c_pre_t10_stress_replay",
        "seed_count": len(SEEDS),
        "cell_count": len(cells),
        "historical_tpr_min":
            historical_tpr_min(),
        "historical_tpr_max":
            historical_tpr_max(),
        "false_negative_rate_max":
            false_negative_rate_max(),
        "adverse_flip_count":
            adverse_flip_count(),
        "stress_cells": [
            c.to_dict() for c in cells
        ],
    }


__all__ = [
    "V3120cReport",
    "build_pre_t10_stress_replay_artifact",
    "build_report",
]
