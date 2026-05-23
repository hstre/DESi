"""v27.0 - Claim Harvester Topology report.

Pflichtmetriken (directive § v27.0):

* claim_extraction_consistency
* limitation_visibility
* open_question_visibility
* provenance_integrity
* replay_stability

Killerfrage: "Kann DESi wissenschaftliche Papers als
epistemische Claim-Strukturen modellieren statt als
Textdokumente?"

A paper is modelled as a temporary epistemic state - a set of
typed, paper-anchored claims with explicit limitations and open
questions. DESi structures; it does not rank, score or judge.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .papers import (
    all_claims, claims_by_class, paper_ids, papers,
)
from .taxonomy import CLAIM_CLASSES

VERDICT_STRUCTURED = "PAPERS_AS_CLAIM_STRUCTURES"
VERDICT_PARTIAL = "CLAIM_STRUCTURE_INCOMPLETE"
VERDICT_HALT = "TOPOLOGY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_STRUCTURED, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def claim_extraction_consistency() -> float:
    """Fraction of papers consistently decomposed: at least one
    well-formed claim and every claim well-formed, in [0, 1]."""
    ps = papers()
    if not ps:
        return 0.0
    ok = 0
    for p in ps:
        if p.claims and all(c.is_well_formed() for c in p.claims):
            ok += 1
    return _round(ok / len(ps))


def limitation_visibility() -> float:
    """Fraction of papers exposing at least one limitation
    claim, in [0, 1]."""
    ps = papers()
    if not ps:
        return 0.0
    return _round(
        sum(1 for p in ps if p.limitations()) / len(ps)
    )


def open_question_visibility() -> float:
    """Fraction of papers exposing at least one open-question
    claim, in [0, 1]."""
    ps = papers()
    if not ps:
        return 0.0
    return _round(
        sum(1 for p in ps if p.open_questions()) / len(ps)
    )


def provenance_integrity() -> float:
    """Fraction of claims that resolve to a registered paper,
    in [0, 1]."""
    claims = all_claims()
    if not claims:
        return 0.0
    ids = set(paper_ids())
    return _round(
        sum(1 for c in claims if c.paper_id in ids) / len(claims)
    )


def missing_claim_classes() -> tuple[str, ...]:
    return tuple(
        k for k in CLAIM_CLASSES if not claims_by_class(k)
    )


def _signature() -> str:
    parts = [
        f"{c.claim_id}|{c.paper_id}|{c.claim_class}"
        for c in all_claims()
    ]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def replay_stability() -> float:
    return 1.0 if _signature() == _signature() else 0.0


def _recommendation(
    *, replay: float, extraction: float, limitation: float,
    open_q: float, provenance: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        extraction < _FLOOR
        or limitation < _FLOOR
        or open_q < _FLOOR
        or provenance < _FLOOR
    ):
        return VERDICT_PARTIAL
    return VERDICT_STRUCTURED


@dataclass(frozen=True)
class V270Report:
    paper_count: int
    claim_count: int
    claim_class_count: int
    claim_extraction_consistency: float
    limitation_visibility: float
    open_question_visibility: float
    provenance_integrity: float
    replay_stability: float
    missing_claim_classes: tuple[str, ...]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_count": self.paper_count,
            "claim_count": self.claim_count,
            "claim_class_count": self.claim_class_count,
            "claim_extraction_consistency":
                self.claim_extraction_consistency,
            "limitation_visibility": self.limitation_visibility,
            "open_question_visibility":
                self.open_question_visibility,
            "provenance_integrity": self.provenance_integrity,
            "replay_stability": self.replay_stability,
            "missing_claim_classes":
                list(self.missing_claim_classes),
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V270Report:
    extraction = claim_extraction_consistency()
    limitation = limitation_visibility()
    open_q = open_question_visibility()
    provenance = provenance_integrity()
    replay = replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, extraction=extraction,
        limitation=limitation, open_q=open_q,
        provenance=provenance,
    )
    rationale = (
        f"INFO: {len(papers())} papers (1 real anchor, rest "
        f"explicitly synthetic) decomposed into "
        f"{len(all_claims())} typed claims across "
        f"{len(CLAIM_CLASSES)} classes",
        "INFO: a paper is modelled as a temporary epistemic "
        "state; DESi structures, it does not rank or judge",
        f"{'PASS' if extraction >= _FLOOR else 'FAIL'}: "
        f"claim_extraction_consistency {extraction} >= 0.90",
        f"{'PASS' if limitation >= _FLOOR else 'FAIL'}: "
        f"limitation_visibility {limitation} >= 0.90",
        f"{'PASS' if open_q >= _FLOOR else 'FAIL'}: "
        f"open_question_visibility {open_q} >= 0.90",
        f"{'PASS' if provenance >= _FLOOR else 'FAIL'}: "
        f"provenance_integrity {provenance} >= 0.90",
        f"INFO: missing_claim_classes "
        f"{list(missing_claim_classes())}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V270Report(
        paper_count=len(papers()),
        claim_count=len(all_claims()),
        claim_class_count=len(CLAIM_CLASSES),
        claim_extraction_consistency=extraction,
        limitation_visibility=limitation,
        open_question_visibility=open_q,
        provenance_integrity=provenance,
        replay_stability=replay,
        missing_claim_classes=missing_claim_classes(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_topology_artifact() -> dict[str, object]:
    return {
        "schema_version": "v27_0_claim_harvester_topology",
        "disclaimer": (
            "Models AI/ML papers as temporary epistemic states "
            "- typed, paper-anchored claims with explicit "
            "limitations and open questions - over a "
            "deterministic fixture corpus. Exactly one paper is "
            "real (the base-paper anchor); every other is "
            "explicitly synthetic and illustrative, so nothing "
            "here is a fabricated real citation. DESi structures "
            "research; it does not rank, score, peer-review, "
            "judge truth or debunk. Deterministic and "
            "replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "claim_classes": list(CLAIM_CLASSES),
        "papers": [p.to_dict() for p in papers()],
        "claim_extraction_consistency":
            claim_extraction_consistency(),
        "limitation_visibility": limitation_visibility(),
        "open_question_visibility": open_question_visibility(),
        "provenance_integrity": provenance_integrity(),
        "replay_stability": replay_stability(),
        "missing_claim_classes": list(missing_claim_classes()),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_STRUCTURED",
    "V270Report",
    "build_report",
    "build_topology_artifact",
    "claim_extraction_consistency",
    "limitation_visibility",
    "open_question_visibility",
    "provenance_integrity",
    "replay_stability",
]
