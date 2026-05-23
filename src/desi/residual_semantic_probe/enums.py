"""Closed taxonomies for v4.4 — semantic failure class +
counterfactual probes + recommendation outcome."""
from __future__ import annotations

from enum import Enum


class ResidualSemanticFailure(str, Enum):
    """Closed failure taxonomy (Aufgabe 5). Every residual
    false-support case maps to exactly one value.

    Priority order during classification (most specific first):

    1. BIDIRECTIONAL_CYCLE      (token-cycle across premises)
    2. EXTRACTION_ALIASING      (premises collapsed by extractor)
    3. FRAME_INNER_OUTER_DIVERGENCE  (frame-tension shape)
    4. SEMANTIC_SCOPE_COLLAPSE  (conclusion contradicts premise)
    5. CAUSAL_BRIDGE_MISSING    (premise -> conclusion gap)
    6. CROSS_DOMAIN_ANALOGY     (frame switches across domains)
    7. UNJUSTIFIED_GENERALIZATION (over-generalised conclusion)
    8. CONCLUSION_LEAP          (future projection beyond data)
    9. UNKNOWN                  (catch-all)
    """

    FRAME_INNER_OUTER_DIVERGENCE = "FRAME_INNER_OUTER_DIVERGENCE"
    CAUSAL_BRIDGE_MISSING        = "CAUSAL_BRIDGE_MISSING"
    BIDIRECTIONAL_CYCLE          = "BIDIRECTIONAL_CYCLE"
    SEMANTIC_SCOPE_COLLAPSE      = "SEMANTIC_SCOPE_COLLAPSE"
    CROSS_DOMAIN_ANALOGY         = "CROSS_DOMAIN_ANALOGY"
    UNJUSTIFIED_GENERALIZATION   = "UNJUSTIFIED_GENERALIZATION"
    CONCLUSION_LEAP              = "CONCLUSION_LEAP"
    EXTRACTION_ALIASING          = "EXTRACTION_ALIASING"
    UNKNOWN                      = "UNKNOWN"


class SemanticProbe(str, Enum):
    """Five closed counterfactual probes (Aufgabe 6)."""

    S1_FRAME_TENSION_STRICT     = "S1_frame_tension_strict"
    S2_INNER_ONLY_ROUTE         = "S2_inner_only_route"
    S3_MANDATORY_CONSILIUM      = "S3_mandatory_consilium"
    S4_TOOL_GATE_IF_NUMERIC     = "S4_tool_gate_if_numeric"
    S5_BIDIRECTIONAL_LINK_CHECK = "S5_bidirectional_link_check"


class RecommendationOutcome(str, Enum):
    LOCALIZED = "SEMANTIC_FAILURE_LOCALIZED"
    DIFFUSE   = "SEMANTIC_FAILURE_DIFFUSE"
    UNKNOWN   = "SEMANTIC_FAILURE_UNKNOWN"
    NONE      = "NONE"


__all__ = [
    "RecommendationOutcome",
    "ResidualSemanticFailure",
    "SemanticProbe",
]
