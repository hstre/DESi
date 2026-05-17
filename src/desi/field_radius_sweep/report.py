"""v3.44 — radius-sweep report.

Pflichtmetriken (directive):

* ``leakage_curve``     — per-radius leakage counts
* ``recall_curve``      — per-radius plateau recall
* ``optimal_radius``    — sweet-spot radius (smallest
  radius preserving full recall + zero leakage);
  ``None`` if no such radius exists in the closed set
* ``radius_stability``  — deterministic replay across
  two full sweeps

Stop rule: ``optimal_radius`` does not exist → field
hypothesis weak (the report records the failure but
does not silently substitute another metric).
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from .ablation import RadiusOutcome, run_all_radii
from .curve import (
    MIN_PLATEAU_RECALL, RadiusPoint, compute_curve,
    pick_largest_clean_radius, pick_optimal_radius,
)
from .radius import RADII


MIN_LEAKAGE_REDUCTION = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V344Report:
    plateau_population: int
    radii_tested: int
    leakage_curve: tuple[dict, ...]
    recall_curve: tuple[dict, ...]
    optimal_radius: str | None
    optimal_plateau_recall: float
    optimal_leakage_count: int
    optimal_leakage_reduction: float
    largest_clean_radius: str | None
    radius_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "plateau_population":
                self.plateau_population,
            "radii_tested": self.radii_tested,
            "leakage_curve": list(self.leakage_curve),
            "recall_curve": list(self.recall_curve),
            "optimal_radius": self.optimal_radius,
            "optimal_plateau_recall":
                self.optimal_plateau_recall,
            "optimal_leakage_count":
                self.optimal_leakage_count,
            "optimal_leakage_reduction":
                self.optimal_leakage_reduction,
            "largest_clean_radius":
                self.largest_clean_radius,
            "radius_stability": self.radius_stability,
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
    a = [o.to_dict() for o in run_all_radii()]
    b = [o.to_dict() for o in run_all_radii()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def _curve_subset(
    curve: tuple[RadiusPoint, ...], key: str,
) -> tuple[dict, ...]:
    """Project the full curve to the directive's two
    named sub-curves while keeping radius labels."""
    out: list[dict] = []
    for p in curve:
        out.append({
            "radius_label": p.radius_label,
            key: getattr(
                p,
                "leakage_count"
                if key == "leakage_count"
                else "plateau_recall",
            ),
        })
    return tuple(out)


def build_report() -> V344Report:
    pids = plateau_trajectory_ids()
    pop = len(pids)
    outcomes = run_all_radii()
    curve = compute_curve(outcomes, pop)
    leakage_curve = _curve_subset(
        curve, "leakage_count",
    )
    recall_curve = _curve_subset(
        curve, "plateau_recall",
    )
    optimal = pick_optimal_radius(curve)
    largest_clean = pick_largest_clean_radius(curve)
    replay = _replay_stability()

    halt = optimal is None
    if halt:
        verdict = "HALT_NO_OPTIMAL_RADIUS"
    elif optimal.leakage_reduction >= MIN_LEAKAGE_REDUCTION:
        verdict = "FIELD_RADIUS_RECOVERED"
    else:
        verdict = "FIELD_RADIUS_PARTIAL"

    rationale = (
        f"{'PASS' if optimal is not None else 'FAIL'}: "
        f"optimal_radius "
        f"{optimal.radius_label if optimal else 'none'}",
        f"INFO: optimal plateau_recall "
        f"{optimal.plateau_recall if optimal else 'n/a'}",
        f"INFO: optimal leakage_count "
        f"{optimal.leakage_count if optimal else 'n/a'}",
        f"INFO: optimal leakage_reduction "
        f"{optimal.leakage_reduction if optimal else 'n/a'}",
        f"INFO: largest_clean_radius "
        f"{largest_clean.radius_label if largest_clean else 'none'}",
        f"PASS: radius_stability {replay}",
    )

    return V344Report(
        plateau_population=pop,
        radii_tested=len(RADII),
        leakage_curve=leakage_curve,
        recall_curve=recall_curve,
        optimal_radius=(
            optimal.radius_label if optimal else None
        ),
        optimal_plateau_recall=(
            optimal.plateau_recall if optimal else 0.0
        ),
        optimal_leakage_count=(
            optimal.leakage_count if optimal else 0
        ),
        optimal_leakage_reduction=(
            optimal.leakage_reduction if optimal else 0.0
        ),
        largest_clean_radius=(
            largest_clean.radius_label
            if largest_clean else None
        ),
        radius_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_radius_sweep_artifact() -> dict[str, object]:
    outcomes = run_all_radii()
    pop = len(plateau_trajectory_ids())
    curve = compute_curve(outcomes, pop)
    return {
        "schema_version": "v3_44_radius_sweep",
        "radii": [
            "inf" if r == float("inf") else r
            for r in RADII
        ],
        "curve": [p.to_dict() for p in curve],
        "outcomes": [o.to_dict() for o in outcomes],
    }


__all__ = [
    "MIN_LEAKAGE_REDUCTION", "V344Report",
    "build_radius_sweep_artifact", "build_report",
]
