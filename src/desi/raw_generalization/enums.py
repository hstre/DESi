"""Closed enums for v5.4 raw-corpus split evaluation."""
from __future__ import annotations

from enum import Enum


class RawEvalChannel(str, Enum):
    """Closed enumeration of evaluation channels — the
    directive forbids aggregation, so every claim must
    declare which channel produced it."""

    TAXONOMY_ONLY = "taxonomy_only"
    PROBE_ONLY    = "probe_only"


class RawRecommendation(str, Enum):
    """Aufgabe 10 closed gate."""

    BOTH_GENERALIZE      = "TAXONOMY_AND_PROBES_GENERALIZE"
    TAXONOMY_ONLY        = "TAXONOMY_GENERALIZES_PROBES_FAIL"
    TAXONOMY_FAILS       = "TAXONOMY_FAILS"
    NONE                 = "NONE"


class NCKind(str, Enum):
    """Aufgabe 9 closed NC kinds."""

    RAW_VALID_PROBE_TRAP       = "raw_valid_probe_trap"
    RAW_INVALID_PARAPHRASE     = "raw_invalid_paraphrase"
    AMBIGUITY_DECOY            = "ambiguity_decoy"
    OVERLAP_ILLUSION           = "overlap_illusion"
    DOMAIN_HYBRID              = "domain_hybrid"


__all__ = ["NCKind", "RawEvalChannel", "RawRecommendation"]
