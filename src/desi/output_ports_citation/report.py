"""v25.2 - Citation & Reference Governance report.

Pflichtmetriken (directive § v25.2):

* phantom_citation_detection
* claim_reference_alignment
* reference_usage_integrity
* citation_traceability
* replay_stability

Killerfrage: "Kann DESi Zitationen als epistemische Kanten
statt als Literatur-Dekoration behandeln?"

Citations are modelled as edges from external claims to a closed
reference registry; the governance layer detects phantom
citations, missing citations, misassignment and orphan
references.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .citations import citation_edges
from .citation_traceability import (
    citation_traceability, claim_reference_alignment,
    reference_usage_integrity,
)
from .phantom_detection import (
    missing_citations, orphan_references,
    phantom_citation_detection, phantom_citations,
    unsupported_related_work_claims, wrong_reference_assignment,
)
from .references import references

VERDICT_EDGES = "CITATIONS_AS_EPISTEMIC_EDGES"
VERDICT_FRAGILE = "CITATION_FRAGILE"
VERDICT_HALT = "CITATION_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_EDGES, VERDICT_FRAGILE, VERDICT_HALT,
)

_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _signature() -> str:
    parts = [f"{e.claim_id}->{e.ref_key}" for e in citation_edges()]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    return 1.0 if citation_traceability() == citation_traceability() else 0.0


def _recommendation(
    *, replay: float, phantom: float, alignment: float,
    usage: float, traceability: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        phantom < _FLOOR
        or alignment < _FLOOR
        or usage < _FLOOR
        or traceability < _FLOOR
    ):
        return VERDICT_FRAGILE
    return VERDICT_EDGES


@dataclass(frozen=True)
class V252Report:
    edge_count: int
    reference_count: int
    phantom_citation_detection: float
    claim_reference_alignment: float
    reference_usage_integrity: float
    citation_traceability: float
    replay_stability: float
    phantom_citations: tuple[str, ...]
    missing_citations: tuple[str, ...]
    orphan_references: tuple[str, ...]
    wrong_reference_assignment: tuple[tuple[str, str], ...]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "edge_count": self.edge_count,
            "reference_count": self.reference_count,
            "phantom_citation_detection":
                self.phantom_citation_detection,
            "claim_reference_alignment":
                self.claim_reference_alignment,
            "reference_usage_integrity":
                self.reference_usage_integrity,
            "citation_traceability": self.citation_traceability,
            "replay_stability": self.replay_stability,
            "phantom_citations": list(self.phantom_citations),
            "missing_citations": list(self.missing_citations),
            "orphan_references": list(self.orphan_references),
            "wrong_reference_assignment": [
                list(t) for t in self.wrong_reference_assignment
            ],
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V252Report:
    phantom = phantom_citation_detection()
    alignment = claim_reference_alignment()
    usage = reference_usage_integrity()
    traceability = citation_traceability()
    replay = replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, phantom=phantom, alignment=alignment,
        usage=usage, traceability=traceability,
    )
    rationale = (
        f"INFO: {len(citation_edges())} citation edges over "
        f"{len(references())} registered references",
        "INFO: citations are edges from external claims to a "
        "closed registry - not literature decoration",
        f"{'PASS' if phantom >= _FLOOR else 'FAIL'}: "
        f"phantom_citation_detection {phantom} >= 0.95 "
        f"(phantoms {list(phantom_citations())}; detector works)",
        f"{'PASS' if alignment >= _FLOOR else 'FAIL'}: "
        f"claim_reference_alignment {alignment} >= 0.95 "
        f"(missing {list(missing_citations())}; misassigned "
        f"{[list(t) for t in wrong_reference_assignment()]})",
        f"{'PASS' if usage >= _FLOOR else 'FAIL'}: "
        f"reference_usage_integrity {usage} >= 0.95 (orphans "
        f"{list(orphan_references())})",
        f"{'PASS' if traceability >= _FLOOR else 'FAIL'}: "
        f"citation_traceability {traceability} >= 0.95",
        f"INFO: unsupported related-work claims "
        f"{list(unsupported_related_work_claims())}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V252Report(
        edge_count=len(citation_edges()),
        reference_count=len(references()),
        phantom_citation_detection=phantom,
        claim_reference_alignment=alignment,
        reference_usage_integrity=usage,
        citation_traceability=traceability,
        replay_stability=replay,
        phantom_citations=phantom_citations(),
        missing_citations=missing_citations(),
        orphan_references=orphan_references(),
        wrong_reference_assignment=wrong_reference_assignment(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_citation_governance_artifact() -> dict[str, object]:
    return {
        "schema_version": "v25_2_citation_governance",
        "disclaimer": (
            "Citation governance for DESi's output ports. "
            "Citations are modelled as directed edges from "
            "external claims to a closed reference registry, not "
            "as literature decoration. The layer detects phantom "
            "citations, missing citations, unsupported "
            "related-work claims, wrong reference assignment and "
            "orphan references. Deterministic and replay-stable."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "citation_edges": [e.to_dict() for e in citation_edges()],
        "references": [r.to_dict() for r in references()],
        "phantom_citation_detection":
            phantom_citation_detection(),
        "claim_reference_alignment": claim_reference_alignment(),
        "reference_usage_integrity": reference_usage_integrity(),
        "citation_traceability": citation_traceability(),
        "replay_stability": replay_stability(),
        "phantom_citations": list(phantom_citations()),
        "missing_citations": list(missing_citations()),
        "orphan_references": list(orphan_references()),
        "wrong_reference_assignment": [
            list(t) for t in wrong_reference_assignment()
        ],
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_EDGES",
    "VERDICT_FRAGILE",
    "VERDICT_HALT",
    "V252Report",
    "build_citation_governance_artifact",
    "build_report",
    "replay_stability",
]
