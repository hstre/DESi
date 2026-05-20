"""DESi v25.2 - Citation & Reference Governance (read-only).

Treats citations as epistemic edges from external claims to a
closed reference registry, not as literature decoration. Detects
phantom citations, missing citations, unsupported related-work
claims, wrong reference assignment and orphan references, so a
citation only stands when it is a real claim-to-reference edge.
"""
from __future__ import annotations

from .citations import (
    CitationEdge, cited_keys, citation_edges, claim_ids,
    edges_for_claim,
)
from .citation_traceability import (
    citation_traceability, claim_reference_alignment,
    reference_usage_integrity,
)
from .phantom_detection import (
    detects_synthetic_phantom, is_phantom_ref,
    missing_citations, orphan_references,
    phantom_citation_detection, phantom_citations,
    unsupported_related_work_claims, wrong_reference_assignment,
)
from .references import (
    Reference, is_registered, reference_keys, references,
    registered_keys, resolve,
)
from .report import (
    REPORT_VERDICTS, VERDICT_EDGES, VERDICT_FRAGILE,
    VERDICT_HALT, V252Report,
    build_citation_governance_artifact, build_report,
    replay_stability,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_EDGES",
    "VERDICT_FRAGILE",
    "VERDICT_HALT",
    "CitationEdge",
    "Reference",
    "V252Report",
    "build_citation_governance_artifact",
    "build_report",
    "citation_edges",
    "citation_traceability",
    "cited_keys",
    "claim_ids",
    "claim_reference_alignment",
    "detects_synthetic_phantom",
    "edges_for_claim",
    "is_phantom_ref",
    "is_registered",
    "missing_citations",
    "orphan_references",
    "phantom_citation_detection",
    "phantom_citations",
    "reference_keys",
    "reference_usage_integrity",
    "references",
    "registered_keys",
    "replay_stability",
    "resolve",
    "unsupported_related_work_claims",
    "wrong_reference_assignment",
]
