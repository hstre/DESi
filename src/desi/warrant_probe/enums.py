"""Closed taxonomies for v4.6 — warrant failure class +
counterfactual warrant probes + recommendation outcome."""
from __future__ import annotations

from enum import Enum


class WarrantFailure(str, Enum):
    """Closed warrant-failure taxonomy (Aufgabe 5). Every
    residual false-support case maps to exactly one value.

    Priority order during classification (most specific
    first):

    1. CONCLUSION_RESTATEMENT  (conclusion ≈ paraphrase of premise)
    2. ALIAS_EQUIVALENCE       (premise/conclusion alias the same entity)
    3. MODALITY_SHIFT          (past → future / descriptive → normative)
    4. CORRELATION_TO_CAUSATION (correlation premise → causal conclusion)
    5. SAMPLE_TO_UNIVERSAL     (one observation → general claim)
    6. SCOPE_EXTENSION         (premise scope ⊊ conclusion scope)
    7. EXCEPTION_SUPPRESSION   (categorical without handling exceptions)
    8. MISSING_BRIDGE_RULE     (no general rule connecting premise → conclusion)
    9. UNKNOWN
    """

    MISSING_BRIDGE_RULE     = "MISSING_BRIDGE_RULE"
    SCOPE_EXTENSION         = "SCOPE_EXTENSION"
    SAMPLE_TO_UNIVERSAL     = "SAMPLE_TO_UNIVERSAL"
    CORRELATION_TO_CAUSATION = "CORRELATION_TO_CAUSATION"
    EXCEPTION_SUPPRESSION   = "EXCEPTION_SUPPRESSION"
    MODALITY_SHIFT          = "MODALITY_SHIFT"
    CONCLUSION_RESTATEMENT  = "CONCLUSION_RESTATEMENT"
    ALIAS_EQUIVALENCE       = "ALIAS_EQUIVALENCE"
    UNKNOWN                 = "UNKNOWN"


class WarrantProbe(str, Enum):
    """Five closed counterfactual warrant probes (Aufgabe 6)."""

    W1_EXPLICIT_BRIDGE_REQUIRED       = "W1_explicit_bridge_required"
    W2_UNIVERSAL_QUANTIFIER_GUARD     = "W2_universal_quantifier_guard"
    W3_MODALITY_CONSISTENCY_CHECK     = "W3_modality_consistency_check"
    W4_EXCEPTION_TRACE_REQUIRED       = "W4_exception_trace_required"
    W5_PREMISE_CONCLUSION_NONIDENTITY = "W5_premise_conclusion_nonidentity"


class RecommendationOutcome(str, Enum):
    LOCALIZED = "WARRANT_FAILURE_LOCALIZED"
    DIFFUSE   = "WARRANT_FAILURE_DIFFUSE"
    UNKNOWN   = "WARRANT_FAILURE_UNKNOWN"
    NONE      = "NONE"


__all__ = [
    "RecommendationOutcome",
    "WarrantFailure",
    "WarrantProbe",
]
