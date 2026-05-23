"""DESi v37.0 - Audit Scenario Connector Layer (read-only).

Loads locally-vendored synthetic audit scenarios in the style of ACCA
/ CPA audit cases and structures them: financial and narrative claims
are surfaced, footnote references resolve, and cross-document links
are preserved. Not official exam content; no official results claimed.
"""
from __future__ import annotations

from .audit_loader import (
    AuditScenario, dataset_hash, dataset_version, provenance,
    scenarios,
)
from .cross_document_mapper import (
    all_cross_refs, cross_document_mapping, cross_ref_resolves, kinds,
)
from .financial_statement_parser import (
    all_financial_claims, claim_footnote_resolves, financial_claims,
    financial_statement_alignment, footnote_ids,
)
from .narrative_parser import (
    all_narrative_claims, narrative_claim_visible, narrative_claims,
    narrative_visibility,
)
from .report import (
    REPORT_VERDICTS, VERDICT_HALT, VERDICT_PARTIAL, VERDICT_STRUCTURED,
    V370Report, build_connectors_artifact, build_report,
    claim_visibility, connector_metrics, replay_stability,
)


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_PARTIAL",
    "VERDICT_STRUCTURED",
    "AuditScenario",
    "V370Report",
    "all_cross_refs",
    "all_financial_claims",
    "all_narrative_claims",
    "build_connectors_artifact",
    "build_report",
    "claim_footnote_resolves",
    "claim_visibility",
    "connector_metrics",
    "cross_document_mapping",
    "cross_ref_resolves",
    "dataset_hash",
    "dataset_version",
    "financial_claims",
    "financial_statement_alignment",
    "footnote_ids",
    "kinds",
    "narrative_claim_visible",
    "narrative_claims",
    "narrative_visibility",
    "provenance",
    "replay_stability",
    "scenarios",
]
