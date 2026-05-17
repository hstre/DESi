"""v3.62 — blind-spot mapping report.

Pflichtmetriken (directive § v3.62):

* ``coverage_gain``           — mean per-pair coverage
  gain (heterogeneous cohort)
* ``redundancy_score``        — mean per-pair
  redundancy (heterogeneous cohort)
* ``uncovered_claims_before`` — full leakage cohort
  (= 145)
* ``uncovered_claims_after``  — claims not covered by
  any plateau anchor at probe_radius
* ``replay_stability``

Paper-11 v3 gate #3: ``coverage_gain > 0``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .blindspots import (
    fully_covered_after, uncovered_after,
    uncovered_before,
)
from .coverage import PROBE_RADIUS
from .overlap import (
    CohortBlindspot, cohort_blindspots,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V362Report:
    probe_radius: float
    heterogeneous_summary: dict
    homogeneous_summary: dict
    coverage_gain: float
    redundancy_score: float
    new_region_fraction: float
    heterogeneity_redundancy_delta: float
    uncovered_claims_before: int
    uncovered_claims_after: int
    fully_covered_after: int
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "heterogeneous_summary":
                self.heterogeneous_summary,
            "homogeneous_summary":
                self.homogeneous_summary,
            "coverage_gain": self.coverage_gain,
            "redundancy_score":
                self.redundancy_score,
            "new_region_fraction":
                self.new_region_fraction,
            "heterogeneity_redundancy_delta":
                self.heterogeneity_redundancy_delta,
            "uncovered_claims_before":
                self.uncovered_claims_before,
            "uncovered_claims_after":
                self.uncovered_claims_after,
            "fully_covered_after":
                self.fully_covered_after,
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
    a = [s.to_dict() for s in cohort_blindspots()]
    b = [s.to_dict() for s in cohort_blindspots()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V362Report:
    het, hom = cohort_blindspots()
    delta = _round(
        hom.mean_redundancy - het.mean_redundancy,
    )
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif het.mean_coverage_gain > 0 and delta > 0:
        verdict = "HETEROGENEOUS_PAIRS_LESS_REDUNDANT"
    elif het.mean_coverage_gain > 0:
        verdict = "COVERAGE_GAIN_POSITIVE"
    else:
        verdict = "NO_BLINDSPOT_DIFFERENCE"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: heterogeneous_summary {het.to_dict()}",
        f"INFO: homogeneous_summary {hom.to_dict()}",
        f"INFO: uncovered_before "
        f"{uncovered_before()}, uncovered_after "
        f"{uncovered_after()}, fully_covered_after "
        f"{fully_covered_after()}",
        f"INFO: heterogeneity_redundancy_delta "
        f"{delta} (positive = heterogeneous less "
        f"redundant)",
        f"{'PASS' if het.mean_coverage_gain > 0 else 'FAIL'}: "
        f"coverage_gain {het.mean_coverage_gain} > 0",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V362Report(
        probe_radius=PROBE_RADIUS,
        heterogeneous_summary=het.to_dict(),
        homogeneous_summary=hom.to_dict(),
        coverage_gain=het.mean_coverage_gain,
        redundancy_score=het.mean_redundancy,
        new_region_fraction=(
            het.mean_new_region_fraction
        ),
        heterogeneity_redundancy_delta=delta,
        uncovered_claims_before=uncovered_before(),
        uncovered_claims_after=uncovered_after(),
        fully_covered_after=fully_covered_after(),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_blindspot_mapping_artifact(
) -> dict[str, object]:
    from .overlap import all_pair_records
    return {
        "schema_version":
            "v3_62_blindspot_mapping",
        "probe_radius": PROBE_RADIUS,
        "uncovered_before": uncovered_before(),
        "uncovered_after": uncovered_after(),
        "fully_covered_after":
            fully_covered_after(),
        "pair_records": [
            p.to_dict() for p in all_pair_records()
        ],
    }


__all__ = [
    "V362Report", "build_blindspot_mapping_artifact",
    "build_report",
]
