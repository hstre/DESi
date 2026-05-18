"""v3.118 — blindness taxonomy report.

Pflichtmetriken (directive § v3.118):

* ``taxonomy_counts``
* ``semantic_blindness_rate``
* ``duplicate_rate``
* ``unknown_rate``
* ``replay_stability``

Killerfrage: "Blind fuer Duplikate - oder blind
fuer Erkenntnis?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .cluster import (
    all_classified_pools,
    duplicate_rate,
    routing_rate,
    semantic_blindness_rate,
    structural_rate,
    taxonomy_counts,
    unknown_rate,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class V3118Report:
    classified_pool_count: int
    taxonomy_counts: dict[str, int]
    semantic_blindness_rate: float
    duplicate_rate: float
    structural_rate: float
    routing_rate: float
    unknown_rate: float
    classified_pools: tuple[dict, ...]
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "classified_pool_count":
                self.classified_pool_count,
            "taxonomy_counts":
                self.taxonomy_counts,
            "semantic_blindness_rate":
                self.semantic_blindness_rate,
            "duplicate_rate":
                self.duplicate_rate,
            "structural_rate":
                self.structural_rate,
            "routing_rate":
                self.routing_rate,
            "unknown_rate":
                self.unknown_rate,
            "classified_pools":
                list(self.classified_pools),
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
    a = (
        duplicate_rate(),
        semantic_blindness_rate(),
        structural_rate(),
        routing_rate(),
        unknown_rate(),
    )
    b = (
        duplicate_rate(),
        semantic_blindness_rate(),
        structural_rate(),
        routing_rate(),
        unknown_rate(),
    )
    return 1.0 if a == b else 0.0


def build_report() -> V3118Report:
    pools = all_classified_pools()
    tc = taxonomy_counts()
    dr = duplicate_rate()
    sbr = semantic_blindness_rate()
    sr = structural_rate()
    rr = routing_rate()
    ur = unknown_rate()
    replay = _replay_stability()

    halt = replay < 1.0
    if halt:
        verdict = "HALT_REPLAY_DRIFT"
    elif sbr > dr:
        verdict = "MOSTLY_SEMANTIC_BLINDNESS"
    elif dr > sbr:
        verdict = "MOSTLY_DUPLICATE_BLINDNESS"
    elif sbr > 0.0:
        verdict = "MIXED_BLINDNESS"
    else:
        verdict = "NO_SEMANTIC_BLINDNESS"

    rationale = (
        f"INFO: classified_pool_count "
        f"{len(pools)}",
        f"INFO: taxonomy_counts {tc}",
        f"INFO: duplicate_rate {dr}",
        f"INFO: semantic_blindness_rate {sbr}",
        f"INFO: structural_rate {sr}",
        f"INFO: routing_rate {rr}",
        f"INFO: unknown_rate {ur}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )

    return V3118Report(
        classified_pool_count=len(pools),
        taxonomy_counts=tc,
        semantic_blindness_rate=sbr,
        duplicate_rate=dr,
        structural_rate=sr,
        routing_rate=rr,
        unknown_rate=ur,
        classified_pools=tuple(
            p.to_dict() for p in pools
        ),
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_state_blindness_taxonomy_artifact(
) -> dict[str, object]:
    pools = all_classified_pools()
    return {
        "schema_version":
            "v3_118_state_blindness_taxonomy",
        "classified_pool_count": len(pools),
        "taxonomy_counts": taxonomy_counts(),
        "semantic_blindness_rate":
            semantic_blindness_rate(),
        "duplicate_rate": duplicate_rate(),
        "structural_rate": structural_rate(),
        "routing_rate": routing_rate(),
        "unknown_rate": unknown_rate(),
        "classified_pools": [
            p.to_dict() for p in pools
        ],
    }


__all__ = [
    "V3118Report",
    "build_report",
    "build_state_blindness_taxonomy_artifact",
]
