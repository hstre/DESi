"""v6.0 — scientific-paper audit report.

Five Pflichtmetriken:

* ``claim_extraction_accuracy``
* ``unsupported_leap_detection``
* ``hallucination_rate``
* ``frame_diversity``
* ``replay_stability``

Killerfrage: "Kann DESi echte Wissenschaft lesen,
ohne Dinge zu erfinden?"
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .audit import (
    blindness_pools_added,
    bridge_audit_coverage,
    claim_extraction_accuracy,
    frame_distribution, frame_diversity,
    unsupported_leap_detection,
)
from .claim_extractor import (
    all_scores, corpus_extractions,
    hallucination_rate,
)
from .paper_reader import (
    VENUES, corpus, venue_counts,
)


@dataclass(frozen=True)
class V60Report:
    paper_count: int
    venue_count: int
    claim_extraction_accuracy: float
    unsupported_leap_detection: float
    hallucination_rate: float
    frame_diversity: float
    bridge_audit_coverage: float
    blindness_pools_added: int
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_count": self.paper_count,
            "venue_count": self.venue_count,
            "claim_extraction_accuracy":
                self.claim_extraction_accuracy,
            "unsupported_leap_detection":
                self.unsupported_leap_detection,
            "hallucination_rate":
                self.hallucination_rate,
            "frame_diversity":
                self.frame_diversity,
            "bridge_audit_coverage":
                self.bridge_audit_coverage,
            "blindness_pools_added":
                self.blindness_pools_added,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation":
                self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        claim_extraction_accuracy(),
        unsupported_leap_detection(),
        hallucination_rate(),
        frame_diversity(),
        bridge_audit_coverage(),
    )
    b = (
        claim_extraction_accuracy(),
        unsupported_leap_detection(),
        hallucination_rate(),
        frame_diversity(),
        bridge_audit_coverage(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, hall: float,
    acc: float, leap: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if hall > 0.05:
        return "PAPER_AUDIT_HALLUCINATING"
    if acc < 0.50:
        return "PAPER_AUDIT_WEAK"
    if leap < 0.50:
        return "PAPER_AUDIT_BRIDGE_BLIND"
    return "PAPER_AUDIT_TRACTABLE"


def build_report() -> V60Report:
    acc = claim_extraction_accuracy()
    leap = unsupported_leap_detection()
    hall = hallucination_rate()
    fd = frame_diversity()
    bridge = bridge_audit_coverage()
    bpa = blindness_pools_added()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, hall=hall,
        acc=acc, leap=leap,
    )
    rationale = (
        f"INFO: paper_count {len(corpus())}",
        f"INFO: venue_counts {venue_counts()}",
        f"INFO: frame_distribution "
        f"{frame_distribution()}",
        f"INFO: blindness_pools_added {bpa}",
        f"INFO: bridge_audit_coverage {bridge}",
        f"{'PASS' if acc >= 0.50 else 'FAIL'}: "
        f"claim_extraction_accuracy {acc} "
        f">= 0.50",
        f"{'PASS' if leap >= 0.50 else 'FAIL'}"
        f": unsupported_leap_detection {leap} "
        f">= 0.50",
        f"{'PASS' if hall <= 0.05 else 'FAIL'}"
        f": hallucination_rate {hall} <= 0.05",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V60Report(
        paper_count=len(corpus()),
        venue_count=len(venue_counts()),
        claim_extraction_accuracy=acc,
        unsupported_leap_detection=leap,
        hallucination_rate=hall,
        frame_diversity=fd,
        bridge_audit_coverage=bridge,
        blindness_pools_added=bpa,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_paper_audit_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v6_0_scientific_paper_audit",
        "venues": list(VENUES),
        "paper_count": len(corpus()),
        "venue_counts": venue_counts(),
        "papers": [
            p.to_dict() for p in corpus()
        ],
        "extractions": [
            {
                "paper_id": p.paper_id,
                "units": [
                    u.to_dict() for u in units
                ],
            }
            for p, units in corpus_extractions()
        ],
        "scores": [
            s.to_dict() for s in all_scores()
        ],
        "claim_extraction_accuracy":
            claim_extraction_accuracy(),
        "unsupported_leap_detection":
            unsupported_leap_detection(),
        "hallucination_rate":
            hallucination_rate(),
        "frame_diversity": frame_diversity(),
        "bridge_audit_coverage":
            bridge_audit_coverage(),
        "blindness_pools_added":
            blindness_pools_added(),
        "frame_distribution":
            frame_distribution(),
    }


__all__ = [
    "V60Report",
    "build_paper_audit_artifact",
    "build_report",
]
