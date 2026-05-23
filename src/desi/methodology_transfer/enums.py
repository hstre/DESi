"""Closed taxonomies for v5.0 — domain enum + ground truth +
recommendation outcome.

The v5.0 methodology transfer probe forbids importing v4
taxonomy. Every closed-enum value here is *newly named*;
it does not reproduce any v4 class identifier.
"""
from __future__ import annotations

from enum import Enum


class TransferDomain(str, Enum):
    """Five previously-unseen domains for v5.0."""

    D1_TECHNICAL_INCIDENT_REPORTS  = "technical_incident_reports"
    D2_LEGAL_CASE_SUMMARIES        = "legal_case_summaries"
    D3_MEDICAL_GUIDELINES          = "medical_guidelines"
    D4_SCIENTIFIC_PEER_REVIEWS     = "scientific_peer_reviews"
    D5_MATHEMATICAL_PROOF_SKETCHES = "mathematical_proof_sketches"


class TransferGroundTruth(str, Enum):
    VALID     = "VALID"
    INVALID   = "INVALID"
    AMBIGUOUS = "AMBIGUOUS"


class PatchabilityRecommendation(str, Enum):
    """Per-cluster patchability (Aufgabe 11). v5.0 may
    recommend but never patch."""

    PATCHABLE   = "PATCHABLE"
    UNPATCHABLE = "UNPATCHABLE"
    AMBIGUOUS   = "AMBIGUOUS"


class TransferRecommendation(str, Enum):
    """Aufgabe 12 closed gate."""

    CONFIRMED = "METHODOLOGY_TRANSFER_CONFIRMED"
    PARTIAL   = "METHODOLOGY_TRANSFER_PARTIAL"
    FAILED    = "METHODOLOGY_TRANSFER_FAILED"
    NONE      = "NONE"


__all__ = [
    "PatchabilityRecommendation",
    "TransferDomain",
    "TransferGroundTruth",
    "TransferRecommendation",
]
