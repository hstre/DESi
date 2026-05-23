"""v3.74 — missing region localization report.

Pflichtmetriken (directive § v3.74):

* ``localization_accuracy``
* ``hole_region_distance``
* ``false_holes``
* ``replay_stability``

Neptun concept gate #2:
``localization_accuracy >= 0.70``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .holes import hole_summary
from .localize import (
    all_localizations,
    correct_localizations, false_holes,
    hole_region_distance_mean,
    localizable_count, localization_accuracy,
)


NEPTUN_LOCALIZATION_FLOOR: float = 0.70


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V374Report:
    localizable_count: int
    correct_localizations: int
    localization_accuracy: float
    false_holes: int
    hole_region_distance: float
    per_removal_records: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "localizable_count":
                self.localizable_count,
            "correct_localizations":
                self.correct_localizations,
            "localization_accuracy":
                self.localization_accuracy,
            "false_holes": self.false_holes,
            "hole_region_distance":
                self.hole_region_distance,
            "per_removal_records":
                list(self.per_removal_records),
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
    a = [l.to_dict() for l in all_localizations()]
    b = [l.to_dict() for l in all_localizations()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V374Report:
    locs = all_localizations()
    acc = localization_accuracy(locs)
    n_loc = localizable_count(locs)
    n_corr = correct_localizations(locs)
    n_false = false_holes(locs)
    dist = hole_region_distance_mean(locs)
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif acc >= NEPTUN_LOCALIZATION_FLOOR:
        verdict = "LOCALIZATION_USABLE"
    elif acc > 0:
        verdict = "LOCALIZATION_WEAK"
    else:
        verdict = "LOCALIZATION_FAILED"

    rationale = (
        f"INFO: localizable_count {n_loc} of "
        f"{len(locs)} removals produced an orphan "
        f"signal",
        f"INFO: correct_localizations {n_corr}",
        f"{'PASS' if acc >= NEPTUN_LOCALIZATION_FLOOR else 'FAIL'}: "
        f"localization_accuracy {acc} >= "
        f"{NEPTUN_LOCALIZATION_FLOOR}",
        f"INFO: false_holes {n_false}",
        f"INFO: hole_region_distance "
        f"{dist if dist != float('inf') else 'inf'}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V374Report(
        localizable_count=n_loc,
        correct_localizations=n_corr,
        localization_accuracy=acc,
        false_holes=n_false,
        hole_region_distance=dist
            if dist != float("inf") else -1.0,
        per_removal_records=tuple(
            l.to_dict() for l in locs
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_missing_region_localization_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_74_missing_region_localization",
        "summary": hole_summary(),
    }


__all__ = [
    "NEPTUN_LOCALIZATION_FLOOR", "V374Report",
    "build_missing_region_localization_artifact",
    "build_report",
]
