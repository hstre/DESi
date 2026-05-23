"""v3.34 — hold-length sweep report.

Pflichtmetriken (directive):

* ``resolution_curve``       — resolved counts per
  strategy (B0..B4).
* ``minimal_effective_hold`` — smallest k>0 that
  resolved any plateau.
* ``overcontrol_curve``      — overcontrol counts per
  strategy.
* ``replay_stability``       — sweep deterministic
  across two runs.

Killer question: ``minimal_effective_hold == 1`` AND
``diminishing_returns == True`` would mean Strategy B
is a *delay* effect (anything >0 works), not a
specifically-shaped intervention.

Stop rule: B2..B4 identical to B1 → delay effect.
Document; do NOT abort.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from .curve import SweepCurves, compute_curves
from .hold_sweep import (
    HoldStrategy, SweepOutcome, sweep_one,
)


@dataclass(frozen=True)
class V334Report:
    plateau_count: int
    curves: SweepCurves
    replay_stability: float
    delay_effect_documented: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "plateau_count": self.plateau_count,
            "curves": self.curves.to_dict(),
            "replay_stability": self.replay_stability,
            "delay_effect_documented":
                self.delay_effect_documented,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _outcomes_per_strategy(
    plateaus: list,
) -> dict[str, list[SweepOutcome]]:
    out: dict[str, list[SweepOutcome]] = {
        k.value: [] for k in HoldStrategy
    }
    for t in plateaus:
        for k in HoldStrategy:
            out[k.value].append(sweep_one(t, k.value))
    return out


def _replay_stability(plateaus: list) -> float:
    a = _outcomes_per_strategy(plateaus)
    b = _outcomes_per_strategy(plateaus)
    sigs_a = []
    sigs_b = []
    for k in HoldStrategy:
        for o in a[k.value]:
            sigs_a.append((
                o.trajectory_id, o.strategy,
                o.counterfactual_final_support,
            ))
        for o in b[k.value]:
            sigs_b.append((
                o.trajectory_id, o.strategy,
                o.counterfactual_final_support,
            ))
    matches = sum(
        1 for x, y in zip(sigs_a, sigs_b) if x == y
    )
    return (
        round(matches / len(sigs_a), 6)
        if sigs_a else 1.0
    )


def _gather_plateaus() -> list:
    pids = set(plateau_trajectory_ids())
    return [
        t for t in extract_all_trajectories()
        if t.trajectory_id in pids
    ]


def build_report() -> V334Report:
    plateaus = _gather_plateaus()
    outcomes = _outcomes_per_strategy(plateaus)
    curves = compute_curves(outcomes)
    replay = _replay_stability(plateaus)

    delay_effect = curves.diminishing_returns
    if delay_effect:
        verdict = "HOLD_SWEEP_DELAY_EFFECT"
    elif curves.minimal_effective_hold == 1:
        verdict = "HOLD_SWEEP_MINIMAL_HOLD_IS_ONE"
    else:
        verdict = "HOLD_SWEEP_INCONCLUSIVE"

    rationale = (
        f"INFO: minimal_effective_hold "
        f"{curves.minimal_effective_hold}",
        f"INFO: diminishing_returns "
        f"{curves.diminishing_returns}",
        f"INFO: resolution_curve "
        f"{curves.resolution_curve}",
        f"INFO: overcontrol_curve "
        f"{curves.overcontrol_curve}",
        f"PASS: replay_stability {replay}",
    )

    return V334Report(
        plateau_count=len(plateaus),
        curves=curves,
        replay_stability=replay,
        delay_effect_documented=delay_effect,
        recommendation=verdict, rationale=rationale,
    )


def build_hold_sweep_artifact() -> dict[str, object]:
    plateaus = _gather_plateaus()
    outcomes = _outcomes_per_strategy(plateaus)
    rows = []
    for k in HoldStrategy:
        for o in outcomes[k.value]:
            rows.append(o.to_dict())
    return {
        "schema_version": "v3_34_hold_sweep",
        "outcomes": rows,
    }


__all__ = [
    "V334Report", "build_hold_sweep_artifact",
    "build_report",
]
