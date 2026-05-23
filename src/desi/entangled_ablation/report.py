"""v3.94 — dimension ablation search report.

Pflichtmetriken (directive § v3.94):

* ``best_dim_set``
* ``best_purity``
* ``dimensionality_cost``
* ``stability``
* ``replay_stability``

Concept Gate condition #2: best_purity >= 0.70.
Killerfrage: "Reichen 1-3 zusaetzliche Dims?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .ablation import baseline_purity
from .search import (
    all_subset_outcomes, best_dim_set,
    best_outcome, best_purity,
    dimensionality_cost,
    purity_above_baseline_count,
    stability,
)


PURITY_THRESHOLD: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V394Report:
    subset_count: int
    baseline_purity: float
    best_dim_set: tuple[str, ...]
    best_purity: float
    dimensionality_cost: int
    stability: float
    purity_above_baseline_count: int
    subset_outcomes: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "subset_count": self.subset_count,
            "baseline_purity":
                self.baseline_purity,
            "best_dim_set":
                list(self.best_dim_set),
            "best_purity": self.best_purity,
            "dimensionality_cost":
                self.dimensionality_cost,
            "stability": self.stability,
            "purity_above_baseline_count":
                self.purity_above_baseline_count,
            "subset_outcomes":
                list(self.subset_outcomes),
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
        best_dim_set(), best_purity(),
        dimensionality_cost(), stability(),
    )
    b = (
        best_dim_set(), best_purity(),
        dimensionality_cost(), stability(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V394Report:
    outs = all_subset_outcomes()
    base = baseline_purity()
    best_set = best_dim_set()
    best_p = best_purity()
    dim_cost = dimensionality_cost()
    stab = stability()
    above = purity_above_baseline_count()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif best_p >= PURITY_THRESHOLD:
        verdict = "SEPARATING_DIM_SET_FOUND"
    elif above > 0:
        verdict = "WEAK_SEPARATING_DIM_SET"
    else:
        verdict = "NO_SEPARATING_DIM_SET"

    rationale = (
        f"INFO: subset_count {len(outs)} "
        f"(sizes 1..3 over 9 dims)",
        f"INFO: baseline_purity {base} "
        f"(majority class)",
        f"INFO: best_dim_set {list(best_set)}",
        f"{'PASS' if best_p >= PURITY_THRESHOLD else 'FAIL'}: "
        f"best_purity {best_p} "
        f"(threshold {PURITY_THRESHOLD})",
        f"INFO: dimensionality_cost {dim_cost}",
        f"INFO: stability {stab} "
        f"(fraction tying the ceiling)",
        f"INFO: purity_above_baseline_count "
        f"{above} (subsets beating majority)",
        f"INFO: subset_outcomes "
        f"{[o.to_dict() for o in outs[:5]]}"
        f"...({len(outs) - 5} more)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V394Report(
        subset_count=len(outs),
        baseline_purity=base,
        best_dim_set=best_set,
        best_purity=best_p,
        dimensionality_cost=dim_cost,
        stability=stab,
        purity_above_baseline_count=above,
        subset_outcomes=tuple(
            o.to_dict() for o in outs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_entangled_ablation_artifact(
) -> dict[str, object]:
    outs = all_subset_outcomes()
    return {
        "schema_version":
            "v3_94_entangled_ablation",
        "subset_count": len(outs),
        "baseline_purity": baseline_purity(),
        "best_dim_set": list(best_dim_set()),
        "best_purity": best_purity(),
        "dimensionality_cost":
            dimensionality_cost(),
        "stability": stability(),
        "purity_above_baseline_count":
            purity_above_baseline_count(),
        "subset_outcomes": [
            o.to_dict() for o in outs
        ],
    }


__all__ = [
    "PURITY_THRESHOLD", "V394Report",
    "build_entangled_ablation_artifact",
    "build_report",
]
