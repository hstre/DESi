"""Closed risk-flag enumeration — Aufgabe 5.

Nine values exactly. The probe annotates every triggered candidate
with the subset of these flags that applies; ``NO_RISK_FLAG`` is
used iff no other flag attaches.
"""
from __future__ import annotations

from enum import Enum


class RiskFlag(str, Enum):
    WOULD_REOPEN_KNOWN_FALSE_POSITIVE = "would_reopen_known_false_positive"
    WOULD_TOUCH_AUTHORITY_CASE = "would_touch_authority_case"
    WOULD_TOUCH_PHILOSOPHY_CASE = "would_touch_philosophy_case"
    WOULD_TOUCH_METAPHOR_CASE = "would_touch_metaphor_case"
    WOULD_TOUCH_EVERYDAY_CAUSAL_CASE = "would_touch_everyday_causal_case"
    WOULD_TOUCH_VALID_MULTISTEP_CASE = "would_touch_valid_multistep_case"
    WOULD_TOUCH_CYCLE_CASE = "would_touch_cycle_case"
    WOULD_TOUCH_CONTRADICTION_CASE = "would_touch_contradiction_case"
    NO_RISK_FLAG = "no_risk_flag"


# Known historical false-positive case ids in the v1.5 main
# benchmark. The directive lists these by name; we capture them
# as a frozen set so any change requires explicit code review.
KNOWN_FALSE_POSITIVE_CASE_IDS: frozenset[str] = frozenset({
    "A5", "A6", "A7", "A10", "D3", "E4", "E5", "E10",
})


__all__ = ["KNOWN_FALSE_POSITIVE_CASE_IDS", "RiskFlag"]
