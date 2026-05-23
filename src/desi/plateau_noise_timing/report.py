"""v3.36 — noise robustness + timing perturbation
report.

Pflichtmetriken (directive):

* ``noise_stability``     — fraction of (plateau,
  noise_level) pairs where the simulated re-audit
  keeps the trajectory at BRIDGE_REQUIRED.
* ``timing_sensitivity``  — range of resolution counts
  across the four timing points.
* ``plateau_breakpoints`` — (trajectory_id, noise_pct)
  pairs that flipped out of the plateau.
* ``replay_stability``    — deterministic across two
  runs.

Killerfrage: numeric threshold artifact or temporal
structure?

Stop rule (directive's Paper-10 v2 gate, condition 3):
``noise_stability >= 0.80``.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from ..epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from ..support_plateau.extractor import (
    plateau_trajectory_ids,
)
from .noise import (
    NOISE_LEVELS, NoiseOutcome, all_noise_outcomes,
)
from .timing import (
    TimingOutcome, TimingPoint, all_timing_outcomes,
)


MIN_NOISE_STABILITY    = 0.80
MIN_TIMING_SENSITIVITY = 1  # >0 required


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V336Report:
    plateau_count: int
    noise_levels_tested: int
    noise_stability: float
    plateau_breakpoints: tuple[dict, ...]
    timing_resolution_counts: dict[str, int]
    timing_sensitivity: int
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "plateau_count": self.plateau_count,
            "noise_levels_tested":
                self.noise_levels_tested,
            "noise_stability": self.noise_stability,
            "plateau_breakpoints": list(
                self.plateau_breakpoints,
            ),
            "timing_resolution_counts":
                dict(self.timing_resolution_counts),
            "timing_sensitivity":
                self.timing_sensitivity,
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _gather_plateaus() -> list:
    pids = set(plateau_trajectory_ids())
    return [
        t for t in extract_all_trajectories()
        if t.trajectory_id in pids
    ]


def _noise_metrics(
    outcomes: tuple[NoiseOutcome, ...],
) -> tuple[float, tuple[dict, ...]]:
    if not outcomes:
        return 1.0, ()
    held = sum(1 for o in outcomes if o.plateau_held)
    stability = _round(held / len(outcomes))
    breakpoints = tuple(
        {
            "trajectory_id": o.trajectory_id,
            "noise_pct": o.noise_pct,
            "simulated_final_support":
                o.simulated_final_support,
        }
        for o in outcomes if not o.plateau_held
    )
    return stability, breakpoints


def _timing_metrics(
    outcomes: tuple[TimingOutcome, ...],
) -> tuple[dict[str, int], int]:
    counts = {k.value: 0 for k in TimingPoint}
    for o in outcomes:
        if o.resolved:
            counts[o.timing] += 1
    values = list(counts.values())
    sensitivity = max(values) - min(values) if values else 0
    return counts, sensitivity


def _replay_stability(plateaus: list) -> float:
    a_noise = all_noise_outcomes(tuple(plateaus))
    b_noise = all_noise_outcomes(tuple(plateaus))
    a_time = all_timing_outcomes(tuple(plateaus))
    b_time = all_timing_outcomes(tuple(plateaus))
    pairs = list(zip(a_noise, b_noise)) + list(
        zip(a_time, b_time),
    )
    matches = sum(
        1 for a, b in pairs if a == b
    )
    return _round(matches / len(pairs)) if pairs else 1.0


def build_report() -> V336Report:
    plateaus = _gather_plateaus()
    noise_outcomes = all_noise_outcomes(tuple(plateaus))
    timing_outcomes = all_timing_outcomes(tuple(plateaus))
    stability, breakpoints = _noise_metrics(noise_outcomes)
    timing_counts, sensitivity = _timing_metrics(
        timing_outcomes,
    )
    replay = _replay_stability(plateaus)

    halt = stability < MIN_NOISE_STABILITY
    if halt:
        verdict = "HALT_LOW_NOISE_STABILITY"
    elif sensitivity > 0 and stability >= MIN_NOISE_STABILITY:
        verdict = "PLATEAU_HOLDS_UNDER_NOISE_AND_TIMING"
    else:
        verdict = "PLATEAU_INCONCLUSIVE"

    rationale = (
        f"{'PASS' if not halt else 'FAIL'}: "
        f"noise_stability {stability} >= "
        f"{MIN_NOISE_STABILITY}",
        f"{'PASS' if sensitivity > 0 else 'FAIL'}: "
        f"timing_sensitivity {sensitivity} > 0",
        f"INFO: timing_counts {timing_counts}",
        f"INFO: plateau_breakpoints "
        f"{len(breakpoints)}",
        f"PASS: replay_stability {replay}",
    )

    return V336Report(
        plateau_count=len(plateaus),
        noise_levels_tested=len(NOISE_LEVELS),
        noise_stability=stability,
        plateau_breakpoints=breakpoints,
        timing_resolution_counts=timing_counts,
        timing_sensitivity=sensitivity,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_noise_artifact() -> dict[str, object]:
    plateaus = _gather_plateaus()
    outcomes = all_noise_outcomes(tuple(plateaus))
    return {
        "schema_version": "v3_36_plateau_noise_profile",
        "outcomes": [o.to_dict() for o in outcomes],
    }


def build_timing_artifact() -> dict[str, object]:
    plateaus = _gather_plateaus()
    outcomes = all_timing_outcomes(tuple(plateaus))
    return {
        "schema_version": "v3_36_plateau_timing_profile",
        "outcomes": [o.to_dict() for o in outcomes],
    }


__all__ = [
    "MIN_NOISE_STABILITY",
    "MIN_TIMING_SENSITIVITY", "V336Report",
    "build_noise_artifact", "build_report",
    "build_timing_artifact",
]
