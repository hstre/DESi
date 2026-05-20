"""v3.120a — threshold sweep report.

Pflichtmetriken (directive § v3.120a):

* ``optimal_threshold``
* ``threshold_window``
* ``best_far``
* ``best_tpr``
* ``replay_stability``

Killerfrage: "War das nur 0.011
Kalibrierungsfehler?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .sweep import (
    best_far_at_full_tpr,
    best_tpr_at_zero_far,
    feasible_cells,
    optimal_threshold,
    threshold_window,
    window_width,
)
from .threshold import all_sweep_cells


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3120aReport:
    sweep_cell_count: int
    feasible_cell_count: int
    optimal_threshold: float
    threshold_window: tuple[float, float]
    window_width: float
    best_far_at_full_tpr: float
    best_tpr_at_zero_far: float
    sweep_cells: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "sweep_cell_count":
                self.sweep_cell_count,
            "feasible_cell_count":
                self.feasible_cell_count,
            "optimal_threshold":
                self.optimal_threshold,
            "threshold_window":
                list(self.threshold_window),
            "window_width": self.window_width,
            "best_far_at_full_tpr":
                self.best_far_at_full_tpr,
            "best_tpr_at_zero_far":
                self.best_tpr_at_zero_far,
            "sweep_cells":
                list(self.sweep_cells),
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
        optimal_threshold(),
        threshold_window(),
        best_far_at_full_tpr(),
        best_tpr_at_zero_far(),
    )
    b = (
        optimal_threshold(),
        threshold_window(),
        best_far_at_full_tpr(),
        best_tpr_at_zero_far(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3120aReport:
    cells = all_sweep_cells()
    feas = feasible_cells()
    opt = optimal_threshold()
    win = threshold_window()
    ww = window_width()
    bf = best_far_at_full_tpr()
    bt = best_tpr_at_zero_far()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif feas:
        verdict = "CALIBRATION_WINDOW_FOUND"
    else:
        verdict = "NO_CALIBRATION_WINDOW"

    rationale = (
        f"INFO: sweep_cell_count {len(cells)}",
        f"INFO: feasible_cell_count {len(feas)} "
        f"(FAR <= 0.10 AND TPR == 1.0)",
        f"INFO: optimal_threshold {opt}",
        f"INFO: threshold_window "
        f"{list(win)} width={ww}",
        f"INFO: best_far_at_full_tpr {bf}",
        f"INFO: best_tpr_at_zero_far {bt}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3120aReport(
        sweep_cell_count=len(cells),
        feasible_cell_count=len(feas),
        optimal_threshold=opt,
        threshold_window=win,
        window_width=ww,
        best_far_at_full_tpr=bf,
        best_tpr_at_zero_far=bt,
        sweep_cells=tuple(
            c.to_dict() for c in cells
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_pre_t10_threshold_sweep_artifact(
) -> dict[str, object]:
    cells = all_sweep_cells()
    return {
        "schema_version":
            "v3_120a_pre_t10_threshold_sweep",
        "sweep_cell_count": len(cells),
        "feasible_cell_count":
            len(feasible_cells()),
        "optimal_threshold":
            optimal_threshold(),
        "threshold_window":
            list(threshold_window()),
        "window_width": window_width(),
        "best_far_at_full_tpr":
            best_far_at_full_tpr(),
        "best_tpr_at_zero_far":
            best_tpr_at_zero_far(),
        "sweep_cells": [
            c.to_dict() for c in cells
        ],
    }


__all__ = [
    "V3120aReport",
    "build_pre_t10_threshold_sweep_artifact",
    "build_report",
]
