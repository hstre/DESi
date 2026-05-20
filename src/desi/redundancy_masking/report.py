"""v3.79 — redundancy class census report.

Pflichtmetriken (directive § v3.79):

* ``redundancy_class_count``
* ``exact_duplicate_count``
* ``partial_overlap_count``
* ``largest_redundancy_class``
* ``replay_stability``
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from .census import census_summary
from .equivalence import (
    PROBE_RADIUS, exact_duplicate_count,
    largest_redundancy_class,
    partial_overlap_count, partial_overlaps,
    redundancy_classes,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V379Report:
    probe_radius: float
    redundancy_class_count: int
    exact_duplicate_count: int
    partial_overlap_count: int
    largest_redundancy_class: int
    classes: tuple[dict, ...]
    partial_overlaps: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "redundancy_class_count":
                self.redundancy_class_count,
            "exact_duplicate_count":
                self.exact_duplicate_count,
            "partial_overlap_count":
                self.partial_overlap_count,
            "largest_redundancy_class":
                self.largest_redundancy_class,
            "classes": list(self.classes),
            "partial_overlaps":
                list(self.partial_overlaps),
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
    a = [c.to_dict() for c in redundancy_classes()]
    b = [c.to_dict() for c in redundancy_classes()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V379Report:
    classes = redundancy_classes()
    overlaps = partial_overlaps(classes)
    exact = exact_duplicate_count(classes)
    partial = partial_overlap_count(overlaps)
    largest = largest_redundancy_class(classes)
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif exact > 0:
        verdict = "REDUNDANCY_CLASSES_FOUND"
    else:
        verdict = "NO_REDUNDANCY"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: redundancy_class_count "
        f"{len(classes)}",
        f"INFO: exact_duplicate_count {exact} "
        f"(classes with >= 2 members)",
        f"INFO: partial_overlap_count {partial}",
        f"INFO: largest_redundancy_class {largest}",
        f"INFO: classes "
        f"{[c.to_dict() for c in classes]}",
        f"INFO: partial_overlaps "
        f"{[o.to_dict() for o in overlaps]}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V379Report(
        probe_radius=PROBE_RADIUS,
        redundancy_class_count=len(classes),
        exact_duplicate_count=exact,
        partial_overlap_count=partial,
        largest_redundancy_class=largest,
        classes=tuple(
            c.to_dict() for c in classes
        ),
        partial_overlaps=tuple(
            o.to_dict() for o in overlaps
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_redundancy_class_census_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_79_redundancy_class_census",
        "probe_radius": PROBE_RADIUS,
        "summary": census_summary(),
    }


__all__ = [
    "V379Report",
    "build_redundancy_class_census_artifact",
    "build_report",
]
