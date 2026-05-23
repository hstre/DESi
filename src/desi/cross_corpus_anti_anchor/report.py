"""v3.55 — cross-corpus anti-anchor transfer report.

Pflichtmetriken (directive § v3.55):

* ``suppression_per_corpus``
* ``recall_per_corpus``
* ``anti_anchor_transfer_rate``
* ``repulsion_per_corpus``
* ``replay_stability``

Paper-11 v2 gate #3: ``anti_anchor_transfer_rate
>= 0.75``.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from ..anti_anchor.anchors import (
    ANTI_COUNT, ANTI_RADIUS,
)
from ..anti_anchor.ablation import PLATEAU_RADIUS
from .anti_anchor_transfer import (
    MIN_SUPPRESSION, MIN_TARGET_RECALL, aggregate,
    transfer_rate,
)
from .suppression import (
    CorpusSuppressionRecord,
    all_corpus_suppression_records,
)


PAPER11_TRANSFER_FLOOR: float = 0.75


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V355Report:
    plateau_radius: float
    anti_radius: float
    anti_count: int
    records: tuple[dict, ...]
    suppression_per_corpus: dict[str, float]
    recall_per_corpus: dict[str, float]
    repulsion_per_corpus: dict[str, int]
    anti_anchor_transfer_rate: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "plateau_radius": self.plateau_radius,
            "anti_radius": self.anti_radius,
            "anti_count": self.anti_count,
            "records": list(self.records),
            "suppression_per_corpus":
                dict(self.suppression_per_corpus),
            "recall_per_corpus":
                dict(self.recall_per_corpus),
            "repulsion_per_corpus":
                dict(self.repulsion_per_corpus),
            "anti_anchor_transfer_rate":
                self.anti_anchor_transfer_rate,
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
        r.to_dict()
        for r in all_corpus_suppression_records()
    ]
    b = [
        r.to_dict()
        for r in all_corpus_suppression_records()
    ]
    if not a:
        return 1.0
    matches = sum(1 for x, y in zip(a, b) if x == y)
    return _round(matches / len(a))


def build_report() -> V355Report:
    records, rate = aggregate()
    suppression = {
        r.corpus: r.suppression_fraction
        for r in records
    }
    recall = {
        r.corpus: r.plateau_recall for r in records
    }
    repulsion = {
        r.corpus: r.repulsion_count for r in records
    }
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif rate >= PAPER11_TRANSFER_FLOOR:
        verdict = "ANTI_ANCHOR_UNIVERSAL"
    elif rate > 0:
        verdict = "ANTI_ANCHOR_PARTIAL"
    else:
        verdict = "ANTI_ANCHOR_LOCAL"

    rationale = (
        f"INFO: plateau_radius {PLATEAU_RADIUS}, "
        f"anti_radius {ANTI_RADIUS}, "
        f"anti_count {ANTI_COUNT}",
        f"INFO: suppression_per_corpus "
        f"{sorted(suppression.items())}",
        f"INFO: recall_per_corpus "
        f"{sorted(recall.items())}",
        f"INFO: repulsion_per_corpus "
        f"{sorted(repulsion.items())}",
        f"{'PASS' if rate >= PAPER11_TRANSFER_FLOOR else 'FAIL'}: "
        f"anti_anchor_transfer_rate {rate} >= "
        f"{PAPER11_TRANSFER_FLOOR}",
        f"INFO: per-corpus min recall = "
        f"{min(recall.values()) if recall else 'n/a'} "
        f"(target >= {MIN_TARGET_RECALL})",
        f"INFO: per-corpus min suppression = "
        f"{min(suppression.values()) if suppression else 'n/a'} "
        f"(target >= {MIN_SUPPRESSION})",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V355Report(
        plateau_radius=PLATEAU_RADIUS,
        anti_radius=ANTI_RADIUS,
        anti_count=ANTI_COUNT,
        records=tuple(
            r.to_dict() for r in records
        ),
        suppression_per_corpus=suppression,
        recall_per_corpus=recall,
        repulsion_per_corpus=repulsion,
        anti_anchor_transfer_rate=rate,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_cross_corpus_anti_anchor_artifact(
) -> dict[str, object]:
    records = all_corpus_suppression_records()
    return {
        "schema_version":
            "v3_55_cross_corpus_anti_anchor",
        "plateau_radius": PLATEAU_RADIUS,
        "anti_radius": ANTI_RADIUS,
        "anti_count": ANTI_COUNT,
        "records": [r.to_dict() for r in records],
    }


__all__ = [
    "PAPER11_TRANSFER_FLOOR", "V355Report",
    "build_cross_corpus_anti_anchor_artifact",
    "build_report",
]
