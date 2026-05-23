"""desi.core.determinism_scanner - determinism scanner (facade).

Re-exports the REAL determinism scanner: the high-risk built-in-hash
pattern counter and the forbidden-term governance check. No behavior
is changed by packaging.
"""
from __future__ import annotations

from desi.determinism_root_cause.containers import high_risk_hit_count
from desi.scientific_rendering import FORBIDDEN_TERMS, forbidden_hits


def determinism_clean() -> bool:
    """True iff the high-risk hash-pattern scanner is clean."""
    return high_risk_hit_count() == 0


__all__ = [
    "FORBIDDEN_TERMS",
    "determinism_clean",
    "forbidden_hits",
    "high_risk_hit_count",
]
