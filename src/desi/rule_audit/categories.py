"""Closed enumerations for the v2.5 rule-coverage audit (Aufgabe 5).

* :class:`AttemptedRule` — mirrors the v1.2 ``InferenceRule`` closed
  set. Used by the read-only proxy to record which existing rules
  were tried for each case.

* :class:`MissingRuleClass` — closed seven-value classifier of
  *what kind of rule is structurally missing* for cases the
  existing rule library cannot satisfy.

Neither enum is consumed by any production module. They live only
in the audit pipeline.
"""
from __future__ import annotations

from enum import Enum


class AttemptedRule(str, Enum):
    SYLLOGISM = "syllogism"
    IMPLICATION = "implication"
    TRANSITIVITY = "transitivity"
    CONTRADICTION = "contradiction"
    EQUIVALENCE = "equivalence"


class MissingRuleClass(str, Enum):
    NONE = "none"
    CAUSAL_CHAIN = "causal_chain"
    MULTI_HOP_IMPLICATION = "multi_hop_implication"
    CHAINED_TEMPORAL = "chained_temporal"
    CHAINED_CONDITIONAL = "chained_conditional"
    CYCLE_STRUCTURAL = "cycle_structural"
    UNKNOWN = "unknown"


__all__ = ["AttemptedRule", "MissingRuleClass"]
