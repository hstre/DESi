"""Closed link-type taxonomy — exactly eight values."""
from __future__ import annotations

from enum import Enum


class LinkType(str, Enum):
    PHYSICAL_CAUSAL          = "physical_causal"
    INSTITUTIONAL_CAUSAL     = "institutional_causal"
    LOGICAL_IMPLICATION      = "logical_implication"
    TEMPORAL_SEQUENCE        = "temporal_sequence"
    METAPHORICAL_ASSOCIATION = "metaphorical_association"
    AUTHORITY_ASSERTION      = "authority_assertion"
    TOOL_DEPENDENCY          = "tool_dependency"
    UNKNOWN                  = "unknown"


class CorpusSource(str, Enum):
    V23_MULTISTEP   = "v23_multistep"
    V314_HELDOUT    = "v314_heldout"
    V315_ADVERSARIAL = "v315_adversarial"
    V316_SUSPENDED  = "v316_suspended"


__all__ = ["CorpusSource", "LinkType"]
