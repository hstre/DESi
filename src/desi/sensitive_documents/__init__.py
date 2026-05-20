"""DESi v17.0 - Sensitive Historical Document
Integrity: Provenance & Document Topology
(read-only, fully synthetic/anonymised).

DESi structures provenance and claim lineage over a
contaminated document space. It emits NO per-entity
verdict, derives NO guilt, builds NO suspect list,
identifies no one, reproduces no sensitive content,
and claims no journalistic/moral/legal authority.
Mention != involvement.
"""
from __future__ import annotations

from .claims import (
    CLAIM_TYPES, Claim, ClaimType, by_claim_id,
    claims, claims_for_entity, type_rank,
)
from .documents import (
    DOCUMENT_CLASSES, ENTITIES, PROVENANCE_GRADES,
    Document, DocumentClass, ProvenanceGrade, by_id,
    doc_ids, documents, grade_value, sources,
)
from .duplicates import (
    duplicate_detection, duplicate_doc_ids,
    duplicate_groups, fingerprint_groups, redundancy,
)
from .lineage import (
    lineage_map, lineage_quality,
    single_source_claims, source_independence,
)
from .provenance import (
    provenance_gaps, provenance_integrity,
    provenance_visibility, robust_provenance_docs,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_OPAQUE,
    VERDICT_STRUCTURED, V170Report, build_report,
    build_topology_artifact, entities_remain_neutral,
    no_involvement_vocabulary, status_histogram,
)


__all__ = [
    "CLAIM_TYPES",
    "DOCUMENT_CLASSES",
    "ENTITIES",
    "PROVENANCE_GRADES",
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_OPAQUE",
    "VERDICT_STRUCTURED",
    "Claim",
    "ClaimType",
    "Document",
    "DocumentClass",
    "ProvenanceGrade",
    "V170Report",
    "build_report",
    "build_topology_artifact",
    "by_claim_id",
    "by_id",
    "claims",
    "claims_for_entity",
    "doc_ids",
    "documents",
    "duplicate_detection",
    "duplicate_doc_ids",
    "duplicate_groups",
    "entities_remain_neutral",
    "fingerprint_groups",
    "grade_value",
    "lineage_map",
    "lineage_quality",
    "no_involvement_vocabulary",
    "provenance_gaps",
    "provenance_integrity",
    "provenance_visibility",
    "redundancy",
    "robust_provenance_docs",
    "single_source_claims",
    "source_independence",
    "sources",
    "status_histogram",
    "type_rank",
]
