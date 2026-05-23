"""v3.69 — Mozart probe coverage report.

Pflichtmetriken (directive § v3.69):

* ``coverage_by_probe``
* ``bridge_by_probe``
* ``gap_events_by_probe``
* ``coverage_percentile``
* ``replay_stability``

Paper-11 historical gate #1: ``mozart
coverage_percentile >= 0.90``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .coverage import (
    HISTORICAL_PROBES, ProbeCoverage,
    all_coverages, coverage_percentile,
    historical_coverages, probe_coverage,
)
from .reconstruct import (
    historical_timelines, missing_probes,
    present_probes,
)


MOZART_PERCENTILE_FLOOR: float = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V369Report:
    historical_probes: tuple[str, ...]
    present_probes: tuple[str, ...]
    missing_probes: tuple[str, ...]
    coverage_by_probe: dict[str, float]
    bridge_by_probe: dict[str, int]
    gap_events_by_probe: dict[str, int]
    coverage_percentile_by_probe: dict[str, float]
    mozart_coverage_percentile: float
    timelines: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "historical_probes":
                list(self.historical_probes),
            "present_probes":
                list(self.present_probes),
            "missing_probes":
                list(self.missing_probes),
            "coverage_by_probe":
                dict(self.coverage_by_probe),
            "bridge_by_probe":
                dict(self.bridge_by_probe),
            "gap_events_by_probe":
                dict(self.gap_events_by_probe),
            "coverage_percentile_by_probe":
                dict(self.coverage_percentile_by_probe),
            "mozart_coverage_percentile":
                self.mozart_coverage_percentile,
            "timelines": list(self.timelines),
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
    a = [c.to_dict() for c in historical_coverages()]
    b = [c.to_dict() for c in historical_coverages()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V369Report:
    population = all_coverages()
    by_probe = {
        c.trajectory_id: c
        for c in historical_coverages()
    }
    cov = {
        tid: c.coverage_score
        for tid, c in by_probe.items()
    }
    bridge = {
        tid: c.bridge_events
        for tid, c in by_probe.items()
    }
    gap = {
        tid: c.gap_events
        for tid, c in by_probe.items()
    }
    pct = {
        tid: (
            coverage_percentile(c, population)
            if c.available else 0.0
        )
        for tid, c in by_probe.items()
    }
    mozart_pct = pct.get(
        "sample:n03_mozart", 0.0,
    )
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif mozart_pct >= MOZART_PERCENTILE_FLOOR:
        verdict = "MOZART_IS_COVERAGE_OUTLIER"
    else:
        verdict = "MOZART_NOT_OUTLIER"

    rationale = (
        f"INFO: historical_probes "
        f"{list(HISTORICAL_PROBES)}",
        f"INFO: present_probes "
        f"{list(present_probes())}",
        f"INFO: missing_probes "
        f"{list(missing_probes())}",
        f"INFO: coverage_by_probe "
        f"{sorted(cov.items())}",
        f"INFO: bridge_by_probe "
        f"{sorted(bridge.items())}",
        f"INFO: gap_events_by_probe "
        f"{sorted(gap.items())}",
        f"INFO: coverage_percentile_by_probe "
        f"{sorted(pct.items())}",
        f"{'PASS' if mozart_pct >= MOZART_PERCENTILE_FLOOR else 'FAIL'}: "
        f"mozart_coverage_percentile {mozart_pct} "
        f">= {MOZART_PERCENTILE_FLOOR}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V369Report(
        historical_probes=HISTORICAL_PROBES,
        present_probes=present_probes(),
        missing_probes=missing_probes(),
        coverage_by_probe=cov,
        bridge_by_probe=bridge,
        gap_events_by_probe=gap,
        coverage_percentile_by_probe=pct,
        mozart_coverage_percentile=mozart_pct,
        timelines=tuple(
            t.to_dict()
            for t in historical_timelines()
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_mozart_coverage_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_69_mozart_coverage",
        "historical_probes":
            list(HISTORICAL_PROBES),
        "present_probes": list(present_probes()),
        "missing_probes": list(missing_probes()),
        "coverages": [
            c.to_dict()
            for c in historical_coverages()
        ],
        "timelines": [
            t.to_dict()
            for t in historical_timelines()
        ],
    }


__all__ = [
    "MOZART_PERCENTILE_FLOOR", "V369Report",
    "build_mozart_coverage_artifact", "build_report",
]
