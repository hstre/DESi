"""DESi v24.3 - Graph Query & Scientific Rendering Integration
(read-only).

Queries the v24.0 epistemic graph to automatically derive claim
provenance, metric derivations, experimental conditions and paper
lineage, and to generate scientific citations. The graph supplies
structure and traceability, never decisions; scientific rendering
stays governed and the canonical state remains the JSON artifacts.
"""
from __future__ import annotations

from .citation_generation import (
    Citation, citations, claim_citation, metric_citation,
    metric_derivation_visibility, references_section,
)
from .paper_lineage import (
    artifact_ids, claims_in_sprint, condition_reconstruction,
    has_cycle, has_dangling_edges, lineage_integrity,
    paper_lineage,
)
from .queries import (
    claim_ids, claim_text, fixtures_of, generating_sprints,
    governance_of, limitations_of, methods_of, metric_names,
    metric_replay_hashes, metric_sprints,
    metric_supported_claims, provenance_of, replay_hashes_of,
    supporting_metrics,
)
from .report import (
    REPORT_VERDICTS, VERDICT_AUTO, VERDICT_HALT, VERDICT_PARTIAL,
    V243Report, build_queries_artifact, build_report,
    replay_stability, traceability_section,
)
from .scientific_traceability import (
    TraceRecord, is_traceable, scientific_traceability,
    section_forbidden_hits, trace_records,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_AUTO",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "Citation",
    "TraceRecord",
    "V243Report",
    "artifact_ids",
    "build_queries_artifact",
    "build_report",
    "citations",
    "claim_citation",
    "claim_ids",
    "claim_text",
    "claims_in_sprint",
    "condition_reconstruction",
    "fixtures_of",
    "generating_sprints",
    "governance_of",
    "has_cycle",
    "has_dangling_edges",
    "is_traceable",
    "limitations_of",
    "lineage_integrity",
    "methods_of",
    "metric_citation",
    "metric_derivation_visibility",
    "metric_names",
    "metric_replay_hashes",
    "metric_sprints",
    "metric_supported_claims",
    "paper_lineage",
    "provenance_of",
    "references_section",
    "replay_hashes_of",
    "replay_stability",
    "scientific_traceability",
    "section_forbidden_hits",
    "supporting_metrics",
    "trace_records",
    "traceability_section",
]
