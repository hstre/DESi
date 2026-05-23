"""v3.31 — plateau census report.

Pflichtfragen (directive):

1. Sind wirklich alle 22 non-rescued cases at
   final_support = 2.0?
2. Gibt es weitere 2.0 trajectories außerhalb der 22?
3. Wie oft kommt 2.0 insgesamt vor?
4. Ist 2.0 transient oder terminal?
5. Gibt es replay drift?

Stop rule: ``plateau_count != 22`` weakens the
hypothesis but does NOT abort the sprint; the report
records the deviation and the v3.32/v3.33 work
proceeds against the actual plateau set.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from .extractor import (
    census, non_rescued_ids, plateau_trajectory_ids,
)
from .metrics import PlateauMetrics, compute_metrics


_EXPECTED_PLATEAU_COUNT = 22


@dataclass(frozen=True)
class V331Report:
    trajectory_count: int
    hypothesis_expected_plateau_count: int
    metrics: PlateauMetrics
    non_rescued_count: int
    plateau_in_non_rescued_count: int
    non_rescued_support_distribution: dict[str, int]
    plateau_source_distribution: dict[str, int]
    hypothesis_weakened: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "trajectory_count": self.trajectory_count,
            "hypothesis_expected_plateau_count":
                self.hypothesis_expected_plateau_count,
            "metrics": self.metrics.to_dict(),
            "non_rescued_count": self.non_rescued_count,
            "plateau_in_non_rescued_count":
                self.plateau_in_non_rescued_count,
            "non_rescued_support_distribution":
                dict(self.non_rescued_support_distribution),
            "plateau_source_distribution":
                dict(self.plateau_source_distribution),
            "hypothesis_weakened":
                self.hypothesis_weakened,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V331Report:
    obs = census()
    metrics = compute_metrics(obs)
    non_rescued = set(non_rescued_ids())
    plateau_ids = set(plateau_trajectory_ids())
    plateau_in_non_rescued = plateau_ids & non_rescued

    nr_obs = [o for o in obs if o.trajectory_id in non_rescued]
    nr_support = Counter(
        str(o.final_support_state) for o in nr_obs
    )
    plateau_sources = Counter(
        o.source for o in obs if o.is_plateau
    )

    weakened = (
        metrics.plateau_count != _EXPECTED_PLATEAU_COUNT
    )
    if weakened:
        verdict = "PLATEAU_HYPOTHESIS_WEAKENED"
    else:
        verdict = "PLATEAU_HYPOTHESIS_CONFIRMED"

    rationale = (
        (f"DOCUMENTED: plateau_count "
         f"{metrics.plateau_count} != "
         f"{_EXPECTED_PLATEAU_COUNT} "
         f"(hypothesis expected 22)"
         if weakened else
         f"PASS: plateau_count "
         f"{metrics.plateau_count} == "
         f"{_EXPECTED_PLATEAU_COUNT}"),
        f"INFO: non_rescued_count "
        f"{len(non_rescued)}; plateau_in_non_rescued "
        f"{len(plateau_in_non_rescued)}; "
        f"non_rescued at non-2.0 = "
        f"{len(non_rescued) - len(plateau_in_non_rescued)}",
        f"INFO: plateau_frequency "
        f"{metrics.plateau_frequency} "
        f"(={metrics.plateau_count}/"
        f"{len(obs)})",
        f"INFO: plateau_replay_stability "
        f"{metrics.plateau_replay_stability}",
    )

    return V331Report(
        trajectory_count=len(obs),
        hypothesis_expected_plateau_count=(
            _EXPECTED_PLATEAU_COUNT
        ),
        metrics=metrics,
        non_rescued_count=len(non_rescued),
        plateau_in_non_rescued_count=len(
            plateau_in_non_rescued,
        ),
        non_rescued_support_distribution=dict(nr_support),
        plateau_source_distribution=dict(plateau_sources),
        hypothesis_weakened=weakened,
        recommendation=verdict, rationale=rationale,
    )


def build_inventory_artifact() -> dict[str, object]:
    obs = census()
    plateaus = [o for o in obs if o.is_plateau]
    non_rescued = set(non_rescued_ids())
    return {
        "schema_version": "v3_31_plateau_inventory",
        "plateau_count": len(plateaus),
        "plateaus": [
            {
                **o.to_dict(),
                "in_non_rescued_set":
                    o.trajectory_id in non_rescued,
            }
            for o in plateaus
        ],
    }


__all__ = [
    "V331Report", "build_inventory_artifact",
    "build_report",
]
