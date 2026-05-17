"""v3.63 — failure diversity report.

Pflichtmetriken (directive § v3.63):

* ``failure_diversity_score``
* ``redundancy_score``
* ``diversity_activation_correlation``
* ``replay_stability``

Paper-11 v3 gate #4:
``diversity_activation_correlation > 0``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .diversity import (
    DIVERSITY_AXES, PROBE_RADIUS, PairDiversityRecord,
    diversity_activation_correlation,
    failure_diversity_score,
    mean_diversity_by_resonance, per_pair_records,
    redundancy_score,
)
from .failures import plateau_failure_profiles


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V363Report:
    probe_radius: float
    diversity_axes: tuple[str, ...]
    failure_diversity_score: float
    redundancy_score: float
    diversity_activation_correlation: float
    mean_diversity_resonant: float
    mean_diversity_non_resonant: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "diversity_axes":
                list(self.diversity_axes),
            "failure_diversity_score":
                self.failure_diversity_score,
            "redundancy_score":
                self.redundancy_score,
            "diversity_activation_correlation":
                self.diversity_activation_correlation,
            "mean_diversity_resonant":
                self.mean_diversity_resonant,
            "mean_diversity_non_resonant":
                self.mean_diversity_non_resonant,
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
    a = [
        r.to_dict() for r in per_pair_records()
    ]
    b = [
        r.to_dict() for r in per_pair_records()
    ]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V363Report:
    div = failure_diversity_score()
    red = redundancy_score()
    corr = diversity_activation_correlation()
    mean_res, mean_non = mean_diversity_by_resonance()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif corr > 0:
        verdict = "DIVERSITY_PREDICTS_ACTIVATION"
    elif corr < 0:
        verdict = "DIVERSITY_SUPPRESSES_ACTIVATION"
    else:
        verdict = "DIVERSITY_UNINFORMATIVE"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: diversity_axes {list(DIVERSITY_AXES)}",
        f"INFO: failure_diversity_score {div} "
        f"(global average, normalised)",
        f"INFO: redundancy_score {red}",
        f"INFO: mean_diversity_resonant {mean_res}, "
        f"mean_diversity_non_resonant {mean_non}",
        f"{'PASS' if corr > 0 else 'FAIL'}: "
        f"diversity_activation_correlation {corr} > 0",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V363Report(
        probe_radius=PROBE_RADIUS,
        diversity_axes=DIVERSITY_AXES,
        failure_diversity_score=div,
        redundancy_score=red,
        diversity_activation_correlation=corr,
        mean_diversity_resonant=mean_res,
        mean_diversity_non_resonant=mean_non,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_failure_diversity_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_63_failure_diversity",
        "probe_radius": PROBE_RADIUS,
        "diversity_axes": list(DIVERSITY_AXES),
        "profiles": [
            p.to_dict()
            for p in plateau_failure_profiles()
        ],
        "pair_records": [
            r.to_dict() for r in per_pair_records()
        ],
    }


__all__ = [
    "V363Report", "build_failure_diversity_artifact",
    "build_report",
]
