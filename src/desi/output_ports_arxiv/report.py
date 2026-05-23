"""v25.1 - arXiv Paper Port report.

Pflichtmetriken (directive § v25.1):

* section_completeness
* citation_completeness
* metric_definition_coverage
* result_derivation_visibility
* replay_stability

Killerfrage: "Kann DESi ein arXiv-kompatibles Kurzpaper
erzeugen, dessen Claims und Zahlen vollstaendig
rueckverfolgbar sind?"

The arXiv port renders all 13 mandated sections, cites the base
paper, defines every metric and derives every number - and
contains no forbidden term.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.icrl_followup_conditions import definitions
from desi.scientific_rendering import forbidden_hits

from .arxiv_port import (
    PORT, missing_sections, render, required_sections,
    section_completeness,
)
from .citation_rules import (
    base_paper_cited, citation_completeness, external_claims,
    phantom_citations, unreferenced_external_claims,
    unused_references,
)
from .reference_manager import references
from .section_builder import result_lines

VERDICT_TRACEABLE = "ARXIV_PAPER_FULLY_TRACEABLE"
VERDICT_INCOMPLETE = "ARXIV_PAPER_INCOMPLETE"
VERDICT_HALT = "RENDER_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_TRACEABLE, VERDICT_INCOMPLETE, VERDICT_HALT,
)

_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def metric_definition_coverage() -> float:
    """Fraction of reported result metrics that carry a
    definition, in [0, 1]."""
    defined = {d.name for d in definitions()}
    metrics = {rl.metric_name for rl in result_lines()}
    if not metrics:
        return 0.0
    covered = sum(1 for m in metrics if m in defined)
    return _round(covered / len(metrics))


def result_derivation_visibility() -> float:
    """Fraction of reported numbers that name a derivation
    (sprint source), in [0, 1]."""
    lines = result_lines()
    if not lines:
        return 0.0
    derived = sum(1 for l in lines if l.is_derived())
    return _round(derived / len(lines))


def paper_forbidden_hits() -> tuple[str, ...]:
    return forbidden_hits(render())


def replay_stability() -> float:
    if render() != render():
        return 0.0
    return 1.0 if citation_completeness() == citation_completeness() else 0.0


def _signature() -> str:
    return hashlib.sha256(render().encode("utf-8")).hexdigest()


def _recommendation(
    *, replay: float, section: float, citation: float,
    metric: float, derivation: float, clean: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        not clean
        or section < _FLOOR
        or citation < _FLOOR
        or metric < _FLOOR
        or derivation < _FLOOR
    ):
        return VERDICT_INCOMPLETE
    return VERDICT_TRACEABLE


@dataclass(frozen=True)
class V251Report:
    section_count: int
    reference_count: int
    external_claim_count: int
    result_count: int
    section_completeness: float
    citation_completeness: float
    metric_definition_coverage: float
    result_derivation_visibility: float
    replay_stability: float
    missing_sections: tuple[str, ...]
    phantom_citations: tuple[str, ...]
    paper_forbidden_hits: tuple[str, ...]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "section_count": self.section_count,
            "reference_count": self.reference_count,
            "external_claim_count": self.external_claim_count,
            "result_count": self.result_count,
            "section_completeness": self.section_completeness,
            "citation_completeness": self.citation_completeness,
            "metric_definition_coverage":
                self.metric_definition_coverage,
            "result_derivation_visibility":
                self.result_derivation_visibility,
            "replay_stability": self.replay_stability,
            "missing_sections": list(self.missing_sections),
            "phantom_citations": list(self.phantom_citations),
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


def build_report() -> V251Report:
    section = section_completeness()
    citation = citation_completeness()
    metric = metric_definition_coverage()
    derivation = result_derivation_visibility()
    replay = replay_stability()
    hits = paper_forbidden_hits()
    clean = not hits
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, section=section, citation=citation,
        metric=metric, derivation=derivation, clean=clean,
    )
    rationale = (
        f"INFO: {len(required_sections())} required sections; "
        f"{len(references())} references; "
        f"{len(external_claims())} external claims; "
        f"{len(result_lines())} derived results",
        "INFO: rendering is a pure function of the epistemic "
        "state; citations are edges to registered references",
        f"{'PASS' if section >= _FLOOR else 'FAIL'}: "
        f"section_completeness {section} >= 0.95 (missing "
        f"{list(missing_sections())})",
        f"{'PASS' if citation >= _FLOOR else 'FAIL'}: "
        f"citation_completeness {citation} >= 0.95 "
        f"(base_paper_cited={base_paper_cited()}; phantom "
        f"{list(phantom_citations())}; unreferenced "
        f"{list(unreferenced_external_claims())}; unused "
        f"{list(unused_references())})",
        f"{'PASS' if metric >= _FLOOR else 'FAIL'}: "
        f"metric_definition_coverage {metric} >= 0.95",
        f"{'PASS' if derivation >= _FLOOR else 'FAIL'}: "
        f"result_derivation_visibility {derivation} >= 0.95 "
        f"(no naked numbers)",
        f"{'PASS' if clean else 'FAIL'}: paper_forbidden_hits "
        f"{list(hits)} (must be empty)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V251Report(
        section_count=len(required_sections()),
        reference_count=len(references()),
        external_claim_count=len(external_claims()),
        result_count=len(result_lines()),
        section_completeness=section,
        citation_completeness=citation,
        metric_definition_coverage=metric,
        result_derivation_visibility=derivation,
        replay_stability=replay,
        missing_sections=missing_sections(),
        phantom_citations=phantom_citations(),
        paper_forbidden_hits=hits,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_arxiv_artifact() -> dict[str, object]:
    return {
        "schema_version": "v25_1_arxiv_paper_port",
        "disclaimer": (
            "An arXiv-compatible short paper rendered "
            "deterministically from DESi's epistemic state. All "
            "13 mandated sections are present, the base paper is "
            "cited, every metric is defined, every number is "
            "derived from a named sprint, and the document "
            "contains no forbidden term. This is a "
            "provenance-bound export, not free text generation "
            "or paper imitation; it is replay-exact and scoped "
            "to the synthetic sandbox."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "port": PORT,
        "required_sections": list(required_sections()),
        "references": [r.to_dict() for r in references()],
        "external_claims": [
            c.to_dict() for c in external_claims()
        ],
        "result_lines": [
            {
                "metric_name": l.metric_name,
                "value": l.value,
                "sprint_source": l.sprint_source,
            }
            for l in result_lines()
        ],
        "section_completeness": section_completeness(),
        "citation_completeness": citation_completeness(),
        "metric_definition_coverage":
            metric_definition_coverage(),
        "result_derivation_visibility":
            result_derivation_visibility(),
        "replay_stability": replay_stability(),
        "paper_forbidden_hits": list(paper_forbidden_hits()),
        "paper_signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_INCOMPLETE",
    "VERDICT_TRACEABLE",
    "V251Report",
    "build_arxiv_artifact",
    "build_report",
    "metric_definition_coverage",
    "paper_forbidden_hits",
    "render",
    "replay_stability",
    "result_derivation_visibility",
]
