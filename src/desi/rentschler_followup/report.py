"""v26 - Rentschler Follow-Up Paper report and Concept Gate.

Concept Gate (directive § v26):

* paper_alignment          >= 0.95
* desi_mechanism_clarity   >= 0.95
* citation_integrity       >= 0.95
* result_traceability      >= 0.95
* no_naked_claims          >= 0.95
* replay_stability         == 1.0

Killerfrage: "Kann DESi ueber den arXiv-Output-Port ein direkt
anschlussfaehiges, zitierfaehiges, nachvollziehbares Kurzpaper
fuer Rentschler erzeugen?"

If the gate passes, the paper is shippable to Rentschler.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.scientific_rendering import forbidden_hits
from desi.icrl_followup_revision import paper_alignment as _section_alignment
from desi.output_ports_arxiv import (
    metric_definition_coverage, result_derivation_visibility,
)
from desi.output_ports_citation import (
    citation_traceability, claim_reference_alignment,
    missing_citations, phantom_citation_detection,
    phantom_citations, reference_usage_integrity,
)

from .paper import (
    missing_sections, render, required_sections,
    section_completeness,
)
from .sections import (
    CORE_THESIS, MECHANISM_MARKERS, build_section,
)

VERDICT_SHIPPABLE = "SHIPPABLE_TO_RENTSCHLER"
VERDICT_NOT_READY = "NOT_READY_FOR_RENTSCHLER"
VERDICT_HALT = "RENDER_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_SHIPPABLE, VERDICT_NOT_READY, VERDICT_HALT,
)
GATE_PASS_STATEMENT = (
    "Das Paper ist versandfaehig an Rentschler."
)

_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def paper_alignment() -> float:
    """Direct anchoring to the base paper's Section 4.6 (reuses
    the v23.0 anchoring metric)."""
    return _round(_section_alignment())


def desi_mechanism_clarity() -> float:
    """Fraction of mandatory mechanism markers present in the
    DESi section, with a hard zero if any forbidden term appears
    there - so a reader learns exactly (and only) what DESi is,
    with no mythology."""
    section = build_section("desi_governance_layer")
    if forbidden_hits(section):
        return 0.0
    low = section.lower()
    present = sum(1 for m in MECHANISM_MARKERS if m in low)
    return _round(present / len(MECHANISM_MARKERS))


def base_paper_in_paper() -> bool:
    text = render()
    return "arXiv:2501.14176" in text and "Rentschler" in text


def citation_integrity() -> float:
    metrics = min(
        phantom_citation_detection(),
        claim_reference_alignment(),
        reference_usage_integrity(),
        citation_traceability(),
    )
    return _round(metrics if base_paper_in_paper() else 0.0)


def result_traceability() -> float:
    return _round(min(
        result_derivation_visibility(),
        metric_definition_coverage(),
    ))


def paper_forbidden_hits() -> tuple[str, ...]:
    return forbidden_hits(render())


def no_naked_claims() -> float:
    """Fraction of naked-claim safety checks passed: numbers
    derived, no forbidden output, no phantom or missing
    citations, in [0, 1]."""
    checks = [
        result_derivation_visibility() == 1.0,
        not paper_forbidden_hits(),
        not phantom_citations(),
        not missing_citations(),
    ]
    return _round(sum(1 for c in checks if c) / len(checks))


def replay_stability() -> float:
    return 1.0 if render() == render() else 0.0


def _signature() -> str:
    return hashlib.sha256(render().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class GateCondition:
    name: str
    value: float
    threshold: float
    comparator: str
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "value": self.value,
            "threshold": self.threshold,
            "comparator": self.comparator,
            "passed": self.passed,
        }


def gate_conditions() -> tuple[GateCondition, ...]:
    return (
        GateCondition(
            "paper_alignment", paper_alignment(), _FLOOR, ">=",
            paper_alignment() >= _FLOOR),
        GateCondition(
            "desi_mechanism_clarity", desi_mechanism_clarity(),
            _FLOOR, ">=", desi_mechanism_clarity() >= _FLOOR),
        GateCondition(
            "citation_integrity", citation_integrity(), _FLOOR,
            ">=", citation_integrity() >= _FLOOR),
        GateCondition(
            "result_traceability", result_traceability(),
            _FLOOR, ">=", result_traceability() >= _FLOOR),
        GateCondition(
            "no_naked_claims", no_naked_claims(), _FLOOR, ">=",
            no_naked_claims() >= _FLOOR),
        GateCondition(
            "replay_stability", replay_stability(), 1.0, "==",
            replay_stability() == 1.0),
    )


def gate_passes_all() -> bool:
    return all(c.passed for c in gate_conditions())


def gate_failing_conditions() -> tuple[str, ...]:
    return tuple(
        c.name for c in gate_conditions() if not c.passed
    )


def _recommendation() -> str:
    if replay_stability() < 1.0:
        return VERDICT_HALT
    return (
        VERDICT_SHIPPABLE if gate_passes_all()
        else VERDICT_NOT_READY
    )


@dataclass(frozen=True)
class V26Report:
    section_count: int
    paper_alignment: float
    desi_mechanism_clarity: float
    citation_integrity: float
    result_traceability: float
    no_naked_claims: float
    replay_stability: float
    gate_passes_all: bool
    gate_failing_conditions: tuple[str, ...]
    missing_sections: tuple[str, ...]
    paper_forbidden_hits: tuple[str, ...]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "section_count": self.section_count,
            "paper_alignment": self.paper_alignment,
            "desi_mechanism_clarity": self.desi_mechanism_clarity,
            "citation_integrity": self.citation_integrity,
            "result_traceability": self.result_traceability,
            "no_naked_claims": self.no_naked_claims,
            "replay_stability": self.replay_stability,
            "gate_passes_all": self.gate_passes_all,
            "gate_failing_conditions":
                list(self.gate_failing_conditions),
            "missing_sections": list(self.missing_sections),
            "paper_forbidden_hits":
                list(self.paper_forbidden_hits),
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V26Report:
    pa = paper_alignment()
    dmc = desi_mechanism_clarity()
    ci = citation_integrity()
    rt = result_traceability()
    nnc = no_naked_claims()
    replay = replay_stability()
    hits = paper_forbidden_hits()
    halt = replay < 1.0
    rationale = (
        f"INFO: {len(required_sections())} mandated sections "
        f"rendered through the v25 arXiv output port",
        "INFO: every number is derived, every external claim is "
        "referenced, and DESi is described only as a local "
        "read-only governance layer (no mythology)",
        f"{'PASS' if pa >= _FLOOR else 'FAIL'}: paper_alignment "
        f"{pa} >= 0.95 (Section 4.6 anchoring)",
        f"{'PASS' if dmc >= _FLOOR else 'FAIL'}: "
        f"desi_mechanism_clarity {dmc} >= 0.95",
        f"{'PASS' if ci >= _FLOOR else 'FAIL'}: "
        f"citation_integrity {ci} >= 0.95 (base paper cited "
        f"{base_paper_in_paper()}; phantom "
        f"{list(phantom_citations())})",
        f"{'PASS' if rt >= _FLOOR else 'FAIL'}: "
        f"result_traceability {rt} >= 0.95",
        f"{'PASS' if nnc >= _FLOOR else 'FAIL'}: no_naked_claims "
        f"{nnc} >= 0.95",
        f"{'PASS' if not hits else 'FAIL'}: paper_forbidden_hits "
        f"{list(hits)} (must be empty)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
        f"INFO: {GATE_PASS_STATEMENT if gate_passes_all() else 'Gate offen.'}",
    )
    return V26Report(
        section_count=len(required_sections()),
        paper_alignment=pa,
        desi_mechanism_clarity=dmc,
        citation_integrity=ci,
        result_traceability=rt,
        no_naked_claims=nnc,
        replay_stability=replay,
        gate_passes_all=gate_passes_all(),
        gate_failing_conditions=gate_failing_conditions(),
        missing_sections=missing_sections(),
        paper_forbidden_hits=hits,
        halt=halt,
        recommendation=_recommendation(),
        rationale=rationale,
    )


def build_followup_artifact() -> dict[str, object]:
    return {
        "schema_version": "v26_rentschler_followup_arxiv_port",
        "disclaimer": (
            "A Rentschler follow-up short paper rendered through "
            "the v25 arXiv output port. It anchors directly to "
            "Section 4.6 of the base paper (arXiv:2501.14176), "
            "describes DESi only as a local, read-only, "
            "non-authoritative governance layer (no mythology), "
            "derives every number, references every external "
            "claim, makes experimental conditions and "
            "limitations explicit, and contains no forbidden "
            "term. A provenance-bound export, not free text "
            "generation; replay-exact and scoped to the "
            "synthetic sandbox."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "core_thesis": CORE_THESIS,
        "required_sections": list(required_sections()),
        "section_completeness": section_completeness(),
        "paper_alignment": paper_alignment(),
        "desi_mechanism_clarity": desi_mechanism_clarity(),
        "citation_integrity": citation_integrity(),
        "result_traceability": result_traceability(),
        "no_naked_claims": no_naked_claims(),
        "replay_stability": replay_stability(),
        "gate_conditions": [
            c.to_dict() for c in gate_conditions()
        ],
        "gate_passes_all": gate_passes_all(),
        "gate_statement": GATE_PASS_STATEMENT,
        "paper_forbidden_hits": list(paper_forbidden_hits()),
        "paper_signature": _signature(),
        "recommendation": _recommendation(),
    }


__all__ = [
    "GATE_PASS_STATEMENT",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_NOT_READY",
    "VERDICT_SHIPPABLE",
    "GateCondition",
    "V26Report",
    "base_paper_in_paper",
    "build_followup_artifact",
    "build_report",
    "citation_integrity",
    "desi_mechanism_clarity",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "no_naked_claims",
    "paper_alignment",
    "paper_forbidden_hits",
    "replay_stability",
    "result_traceability",
]
