"""Closed taxonomies for v4.2 — failure class, distribution
metrics, recommendation outcome."""
from __future__ import annotations

from enum import Enum


class ExternalAuditFailure(str, Enum):
    """Closed failure taxonomy (Aufgabe 5). Every false-support
    case maps to *exactly one* value.

    Priority order during classification:
    METAPHOR > AUTHORITY > HIDDEN_NEGATION > QUANTIFIER_DRIFT >
    TOOL > CYCLE_DISGUISE > FRAME_SWITCH >
    EXTRACTION_COLLAPSE > SEMANTIC_NON_SEQUITUR > UNKNOWN.
    """

    HIDDEN_NEGATION         = "HIDDEN_NEGATION"
    QUANTIFIER_DRIFT        = "QUANTIFIER_DRIFT"
    AUTHORITY_CONTAMINATION = "AUTHORITY_CONTAMINATION"
    METAPHOR_CONTAMINATION  = "METAPHOR_CONTAMINATION"
    FRAME_SWITCH            = "FRAME_SWITCH"
    TOOL_CONTAMINATION      = "TOOL_CONTAMINATION"
    CYCLE_DISGUISE          = "CYCLE_DISGUISE"
    SEMANTIC_NON_SEQUITUR   = "SEMANTIC_NON_SEQUITUR"
    EXTRACTION_COLLAPSE     = "EXTRACTION_COLLAPSE"
    UNKNOWN                 = "UNKNOWN"


class RecommendationOutcome(str, Enum):
    """Closed list of recommendations (Aufgabe 11)."""

    LOCALIZED = "AUDIT_FAILURE_LOCALIZED"
    DIFFUSE   = "AUDIT_FAILURE_DIFFUSE"
    UNKNOWN   = "AUDIT_FAILURE_UNKNOWN"
    NONE      = "NONE"


__all__ = ["ExternalAuditFailure", "RecommendationOutcome"]
