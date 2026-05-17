"""v3.35 — cross-class transfer report.

Pflichtmetriken (directive):

* ``cross_class_effects`` — count of trajectories per
  target_class where Strategy B changed the final
  support state.
* ``false_rescues``       — non-plateau REJECTED
  trajectories whose final moved out of REJECTED.
* ``overcontrol``         — SUPPORTED trajectories
  whose final moved out of SUPPORTED. By construction
  this is zero in the v3.35 universe (cliff classes
  only); reported for paranoia.
* ``specificity_score``   — plateau_resolutions
  divided by (plateau_resolutions + cross-class
  changes). High = the action's effect concentrates on
  plateau; low = the action is generic.

Killer question: ``Ist Strategy B plateau-spezifisch?``

Stop rule: ``specificity_score < 0.80`` halts Paper 10.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from .transfer import (
    CrossClassOutcome, TargetClass, collect_universe,
    per_class_counts,
)


MIN_SPECIFICITY_SCORE          = 0.80


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V335Report:
    plateau_count: int
    universe_size: int
    cross_class_effects: dict[str, int]
    plateau_resolutions: int
    false_rescues: int
    overcontrol: int
    specificity_score: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "plateau_count": self.plateau_count,
            "universe_size": self.universe_size,
            "cross_class_effects":
                dict(self.cross_class_effects),
            "plateau_resolutions":
                self.plateau_resolutions,
            "false_rescues": self.false_rescues,
            "overcontrol": self.overcontrol,
            "specificity_score": self.specificity_score,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V335Report:
    outcomes = collect_universe()
    plateau_count = sum(
        1 for o in outcomes
        if o.target_class == TargetClass.PLATEAU.value
    )
    # Per-class change counts.
    effects: Counter = Counter()
    for o in outcomes:
        if o.changed:
            effects[o.target_class] += 1

    plateau_resolutions = sum(
        1 for o in outcomes if o.resolved_plateau
    )
    false_rescues = sum(
        1 for o in outcomes if o.false_rescue
    )
    overcontrol = sum(
        1 for o in outcomes if o.overcontrol
    )

    # specificity = plateau_resolutions
    #   / (plateau_resolutions + false_rescues
    #      + overcontrol). Healthy if Strategy B's
    # effect concentrates on plateau and rarely on
    # other classes.
    denom = (
        plateau_resolutions + false_rescues + overcontrol
    )
    specificity = (
        _round(plateau_resolutions / denom)
        if denom else 0.0
    )

    halt = specificity < MIN_SPECIFICITY_SCORE
    if halt:
        verdict = "HALT_LOW_SPECIFICITY"
    else:
        verdict = "STRATEGY_B_IS_PLATEAU_SPECIFIC"

    rationale = (
        f"{'FAIL' if halt else 'PASS'}: "
        f"specificity_score {specificity} >= "
        f"{MIN_SPECIFICITY_SCORE}",
        f"INFO: plateau_resolutions "
        f"{plateau_resolutions}",
        f"INFO: false_rescues {false_rescues}",
        f"INFO: overcontrol {overcontrol}",
        f"INFO: cross_class_effects {dict(effects)}",
    )

    return V335Report(
        plateau_count=plateau_count,
        universe_size=len(outcomes),
        cross_class_effects=dict(effects),
        plateau_resolutions=plateau_resolutions,
        false_rescues=false_rescues,
        overcontrol=overcontrol,
        specificity_score=specificity,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_specificity_artifact() -> dict[str, object]:
    outcomes = collect_universe()
    return {
        "schema_version": "v3_35_cross_class_specificity",
        "outcomes": [o.to_dict() for o in outcomes],
    }


__all__ = [
    "MIN_SPECIFICITY_SCORE", "V335Report",
    "build_report", "build_specificity_artifact",
]
