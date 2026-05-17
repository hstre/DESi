"""v3.83 — cross-corpus doppelganger report.

Pflichtmetriken (directive § v3.83):

* ``intra_corpus_classes``
* ``cross_corpus_classes``
* ``transfer_accuracy``
* ``class_stability``
* ``replay_stability``

Stop rule: ``transfer_accuracy < 0.70`` -> the
cross-corpus doppelganger hypothesis is weak;
document and continue.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..doppelgaenger.report import (
    PURITY_THRESHOLD,
)
from ..redundancy_masking.equivalence import (
    PROBE_RADIUS,
)
from .corpus_clustering import (
    intra_corpus_classes, joint_clusters,
    per_corpus_summaries,
)
from .transfer import (
    class_stability, cross_corpus_classes,
    restricted_classes, total_cross_corpus_pairs,
    transfer_accuracy,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V383Report:
    probe_radius: float
    per_corpus_summaries: tuple[dict, ...]
    intra_corpus_classes: tuple[int, ...]
    joint_clusters: tuple[dict, ...]
    cross_corpus_classes: int
    cross_corpus_pair_count: int
    transfer_accuracy: float
    class_stability: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_radius": self.probe_radius,
            "per_corpus_summaries":
                list(self.per_corpus_summaries),
            "intra_corpus_classes":
                list(self.intra_corpus_classes),
            "joint_clusters":
                list(self.joint_clusters),
            "cross_corpus_classes":
                self.cross_corpus_classes,
            "cross_corpus_pair_count":
                self.cross_corpus_pair_count,
            "transfer_accuracy":
                self.transfer_accuracy,
            "class_stability":
                self.class_stability,
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
    a = [s.to_dict() for s in per_corpus_summaries()]
    b = [s.to_dict() for s in per_corpus_summaries()]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V383Report:
    summaries = per_corpus_summaries()
    intra = intra_corpus_classes()
    joints = joint_clusters()
    cross_n = cross_corpus_classes()
    pair_n = total_cross_corpus_pairs()
    transfer = transfer_accuracy()
    stab = class_stability()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif (
        transfer >= PURITY_THRESHOLD
        and stab >= PURITY_THRESHOLD
    ):
        verdict = "CROSS_CORPUS_DOPPELGAENGER_DETECTED"
    elif transfer >= PURITY_THRESHOLD:
        verdict = (
            "CROSS_CORPUS_DOPPELGAENGER_UNSTABLE"
        )
    else:
        verdict = "CROSS_CORPUS_HYPOTHESIS_WEAK"

    rationale = (
        f"INFO: probe_radius {PROBE_RADIUS}",
        f"INFO: per_corpus_summaries "
        f"{[s.to_dict() for s in summaries]}",
        f"INFO: intra_corpus_classes "
        f"{list(intra)}",
        f"INFO: joint_clusters "
        f"{[c.to_dict() for c in joints]}",
        f"INFO: cross_corpus_classes {cross_n}",
        f"INFO: cross_corpus_pair_count {pair_n}",
        f"{'PASS' if transfer >= PURITY_THRESHOLD else 'FAIL'}: "
        f"transfer_accuracy {transfer} "
        f"(threshold {PURITY_THRESHOLD})",
        f"{'PASS' if stab >= PURITY_THRESHOLD else 'FAIL'}: "
        f"class_stability {stab}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V383Report(
        probe_radius=PROBE_RADIUS,
        per_corpus_summaries=tuple(
            s.to_dict() for s in summaries
        ),
        intra_corpus_classes=intra,
        joint_clusters=tuple(
            c.to_dict() for c in joints
        ),
        cross_corpus_classes=cross_n,
        cross_corpus_pair_count=pair_n,
        transfer_accuracy=transfer,
        class_stability=stab,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_cross_corpus_doppelgaenger_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v3_83_cross_corpus_doppelgaenger",
        "probe_radius": PROBE_RADIUS,
        "per_corpus_summaries": [
            s.to_dict()
            for s in per_corpus_summaries()
        ],
        "joint_clusters": [
            c.to_dict() for c in joint_clusters()
        ],
        "restricted_v3_79_classes": [
            list(r) for r in restricted_classes()
        ],
        "cross_corpus_classes":
            cross_corpus_classes(),
        "cross_corpus_pair_count":
            total_cross_corpus_pairs(),
        "transfer_accuracy": transfer_accuracy(),
        "class_stability": class_stability(),
    }


__all__ = [
    "V383Report",
    "build_cross_corpus_doppelgaenger_artifact",
    "build_report",
]
