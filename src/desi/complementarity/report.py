"""v3.61 — complementarity vs distance report.

Pflichtmetriken (directive § v3.61):

* ``distance_only_activation``
* ``heterogeneity_only_activation``
* ``combined_activation``
* ``best_explanation_model``
* ``replay_stability``
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .complementarity import (
    ConditionCell, PROBE_RADIUS,
    baseline_activation, best_explanation_model,
    combined_activation,
    distance_only_activation,
    heterogeneity_only_activation,
    per_cell_results,
)
from .distance import distance_threshold


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V361Report:
    probe_radius: float
    distance_threshold: float
    cells: tuple[dict, ...]
    distance_only_activation: float
    heterogeneity_only_activation: float
    combined_activation: float
    baseline_activation: float
    best_explanation_model: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "distance_threshold":
                self.distance_threshold,
            "cells": list(self.cells),
            "distance_only_activation":
                self.distance_only_activation,
            "heterogeneity_only_activation":
                self.heterogeneity_only_activation,
            "combined_activation":
                self.combined_activation,
            "baseline_activation":
                self.baseline_activation,
            "best_explanation_model":
                self.best_explanation_model,
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
    a = [c.to_dict() for c in per_cell_results()]
    b = [c.to_dict() for c in per_cell_results()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V361Report:
    cells = per_cell_results()
    d = distance_only_activation(cells)
    h = heterogeneity_only_activation(cells)
    combo = combined_activation(cells)
    base = baseline_activation(cells)
    best = best_explanation_model(cells)
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif combo > max(d + base, h + base):
        verdict = "COMPLEMENTARITY_BEYOND_DISTANCE"
    elif d > h + 0.05:
        verdict = "DISTANCE_DOMINATES"
    elif h > d + 0.05:
        verdict = "HETEROGENEITY_DOMINATES"
    else:
        verdict = "FACTORS_EQUIVALENT"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: distance_threshold "
        f"{_round(distance_threshold())}",
        f"INFO: per-cell results "
        f"{[c.to_dict() for c in cells]}",
        f"INFO: distance_only_activation {d}",
        f"INFO: heterogeneity_only_activation {h}",
        f"INFO: combined_activation {combo}",
        f"INFO: baseline_activation {base}",
        f"INFO: best_explanation_model {best}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V361Report(
        probe_radius=PROBE_RADIUS,
        distance_threshold=_round(distance_threshold()),
        cells=tuple(c.to_dict() for c in cells),
        distance_only_activation=d,
        heterogeneity_only_activation=h,
        combined_activation=combo,
        baseline_activation=base,
        best_explanation_model=best,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_complementarity_vs_distance_artifact(
) -> dict[str, object]:
    cells = per_cell_results()
    return {
        "schema_version":
            "v3_61_complementarity_vs_distance",
        "probe_radius": PROBE_RADIUS,
        "distance_threshold":
            _round(distance_threshold()),
        "cells": [c.to_dict() for c in cells],
    }


__all__ = [
    "V361Report",
    "build_complementarity_vs_distance_artifact",
    "build_report",
]
