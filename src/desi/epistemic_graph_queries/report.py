"""v24.3 - Graph Query & Scientific Rendering report.

Pflichtmetriken (directive § v24.3):

* scientific_traceability
* metric_derivation_visibility
* condition_reconstruction
* lineage_integrity
* replay_stability

Killerfrage: "Kann DESi wissenschaftliche Nachvollziehbarkeit
automatisch aus dem epistemischen Graphen ableiten?"

The graph is queried read-only to auto-derive claim provenance,
metric derivations, experimental conditions and paper lineage.
It supplies structure and traceability, never decisions; the
canonical state stays in the JSON artifacts and replay hashes.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.epistemic_graph import (
    graph_signature, replay_stability as graph_replay_stability,
)

from .citation_generation import (
    citations, metric_derivation_visibility, references_section,
)
from .paper_lineage import (
    condition_reconstruction, has_cycle, has_dangling_edges,
    lineage_integrity, paper_lineage,
)
from .queries import claim_ids, metric_names
from .scientific_traceability import (
    scientific_traceability, section_forbidden_hits,
    trace_records, traceability_section,
)

VERDICT_AUTO = "TRACEABILITY_AUTO_DERIVED"
VERDICT_PARTIAL = "TRACEABILITY_INCOMPLETE"
VERDICT_HALT = "QUERY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_AUTO, VERDICT_PARTIAL, VERDICT_HALT,
)

_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def replay_stability() -> float:
    if scientific_traceability() != scientific_traceability():
        return 0.0
    if graph_signature() != graph_signature():
        return 0.0
    return 1.0 if graph_replay_stability() == 1.0 else 0.0


def _signature() -> str:
    parts = [c.text for c in citations()]
    parts += [r.claim_id for r in trace_records()]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def _recommendation(
    *, replay: float, trace: float, derivation: float,
    condition: float, integrity: float, clean: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        not clean
        or trace < _FLOOR
        or derivation < _FLOOR
        or condition < _FLOOR
        or integrity < _FLOOR
    ):
        return VERDICT_PARTIAL
    return VERDICT_AUTO


@dataclass(frozen=True)
class V243Report:
    claim_count: int
    metric_count: int
    citation_count: int
    scientific_traceability: float
    metric_derivation_visibility: float
    condition_reconstruction: float
    lineage_integrity: float
    replay_stability: float
    section_forbidden_hits: tuple[str, ...]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_count": self.claim_count,
            "metric_count": self.metric_count,
            "citation_count": self.citation_count,
            "scientific_traceability":
                self.scientific_traceability,
            "metric_derivation_visibility":
                self.metric_derivation_visibility,
            "condition_reconstruction":
                self.condition_reconstruction,
            "lineage_integrity": self.lineage_integrity,
            "replay_stability": self.replay_stability,
            "section_forbidden_hits":
                list(self.section_forbidden_hits),
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V243Report:
    trace = scientific_traceability()
    derivation = metric_derivation_visibility()
    condition = condition_reconstruction()
    integrity = lineage_integrity()
    replay = replay_stability()
    hits = section_forbidden_hits()
    clean = not hits
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, trace=trace, derivation=derivation,
        condition=condition, integrity=integrity, clean=clean,
    )
    rationale = (
        f"INFO: {len(claim_ids())} claims, "
        f"{len(metric_names())} metrics, "
        f"{len(citations())} auto-generated citations; "
        f"{len(paper_lineage())} paper-lineage entries",
        "INFO: graph is queried read-only; it supplies "
        "structure and provenance, never decisions",
        f"{'PASS' if trace >= 0.90 else 'FAIL'}: "
        f"scientific_traceability {trace} >= 0.90",
        f"{'PASS' if derivation >= 0.90 else 'FAIL'}: "
        f"metric_derivation_visibility {derivation} >= 0.90",
        f"{'PASS' if condition >= 0.90 else 'FAIL'}: "
        f"condition_reconstruction {condition} >= 0.90",
        f"{'PASS' if integrity >= 0.90 else 'FAIL'}: "
        f"lineage_integrity {integrity} >= 0.90 (dangling "
        f"{has_dangling_edges()}; cycle {has_cycle()})",
        f"{'PASS' if clean else 'FAIL'}: "
        f"section_forbidden_hits {list(hits)} (rendering stays "
        f"governed)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V243Report(
        claim_count=len(claim_ids()),
        metric_count=len(metric_names()),
        citation_count=len(citations()),
        scientific_traceability=trace,
        metric_derivation_visibility=derivation,
        condition_reconstruction=condition,
        lineage_integrity=integrity,
        replay_stability=replay,
        section_forbidden_hits=hits,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_queries_artifact() -> dict[str, object]:
    return {
        "schema_version": "v24_3_graph_queries",
        "disclaimer": (
            "Read-only graph queries that auto-derive scientific "
            "traceability, metric derivations, experimental "
            "conditions and paper lineage from the v24.0 "
            "epistemic graph. The graph supplies structure and "
            "provenance, not decisions; scientific rendering "
            "stays governed (no forbidden terms) and the "
            "canonical state remains the JSON artifacts and "
            "replay hashes."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "trace_records": [r.to_dict() for r in trace_records()],
        "citations": [c.to_dict() for c in citations()],
        "paper_lineage": list(paper_lineage()),
        "scientific_traceability": scientific_traceability(),
        "metric_derivation_visibility":
            metric_derivation_visibility(),
        "condition_reconstruction": condition_reconstruction(),
        "lineage_integrity": lineage_integrity(),
        "replay_stability": replay_stability(),
        "section_forbidden_hits": list(section_forbidden_hits()),
        "graph_signature": graph_signature(),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_AUTO",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "V243Report",
    "build_queries_artifact",
    "build_report",
    "references_section",
    "replay_stability",
    "traceability_section",
]
