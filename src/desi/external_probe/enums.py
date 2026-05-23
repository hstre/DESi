"""Closed taxonomies for v4.0 — domains, ground truth, failure
classes."""
from __future__ import annotations

from enum import Enum


class Domain(str, Enum):
    D1_SCIENTIFIC_ABSTRACTS  = "scientific_abstracts"
    D2_LEGAL_REASONING       = "legal_reasoning"
    D3_MEDICAL_CASE_REPORTS  = "medical_case_reports"
    D4_MATHEMATICAL_PROOFS   = "mathematical_proofs"
    D5_ADVERSARIAL_REAL_WORLD = "adversarial_real_world"
    NEGATIVE_CONTROL         = "negative_control"


class GroundTruth(str, Enum):
    VALID      = "VALID"
    INVALID    = "INVALID"
    UNDECIDABLE = "UNDECIDABLE"


class FailureClass(str, Enum):
    FRAME_FAILURE         = "FRAME_FAILURE"
    CHAIN_FAILURE         = "CHAIN_FAILURE"
    SUSPENSION_FAILURE    = "SUSPENSION_FAILURE"
    ROUTING_FAILURE       = "ROUTING_FAILURE"
    GROUND_TRUTH_MISMATCH = "GROUND_TRUTH_MISMATCH"
    UNKNOWN               = "UNKNOWN"


class RecommendationOutcome(str, Enum):
    CONFIRMED = "EXTERNAL_GENERALIZATION_CONFIRMED"
    PARTIAL   = "EXTERNAL_GENERALIZATION_PARTIAL"
    FAILED    = "EXTERNAL_GENERALIZATION_FAILED"
    NONE      = "NONE"


__all__ = [
    "Domain",
    "FailureClass",
    "GroundTruth",
    "RecommendationOutcome",
]
