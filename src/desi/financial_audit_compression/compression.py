"""v15.3 - signal preservation under compression.

The safety property: compressing the audit search
must NOT drop the critical signals.

* critical_signal_preservation = fraction of
  critical cells that survive into the audited set
  (directly, or via a same-pool representative that
  carries the same axis above threshold).
* false_suppression_rate = fraction of critical
  cells that were dropped.

Reads no post-hoc label.
"""
from __future__ import annotations

from .audit_priority import (
    CRITICAL_THRESHOLD, audit_universe,
    critical_cells,
)
from .exploration_budget import selected_keys
from .risk_ranking import representative


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _rep_covers(firm_id: str, axis: str) -> bool:
    """True if the firm's pool representative carries
    the same axis above the critical threshold -
    i.e. a recoverable member's critical signal is
    still visible through the representative."""
    rep = representative(firm_id)
    if rep == firm_id:
        return False
    for c in audit_universe():
        if c.firm_id == rep and c.axis == axis:
            return c.value >= CRITICAL_THRESHOLD
    return False


def _is_preserved(firm_id: str, axis: str) -> bool:
    if (firm_id, axis) in selected_keys():
        return True
    return _rep_covers(firm_id, axis)


def preserved_critical() -> tuple[
    tuple[str, str], ...
]:
    return tuple(
        (c.firm_id, c.axis)
        for c in critical_cells()
        if _is_preserved(c.firm_id, c.axis)
    )


def suppressed_critical() -> tuple[
    tuple[str, str], ...
]:
    return tuple(
        (c.firm_id, c.axis)
        for c in critical_cells()
        if not _is_preserved(c.firm_id, c.axis)
    )


def critical_signal_preservation() -> float:
    crit = critical_cells()
    if not crit:
        return 1.0
    kept = len(preserved_critical())
    return _round(kept / len(crit))


def false_suppression_rate() -> float:
    crit = critical_cells()
    if not crit:
        return 0.0
    dropped = len(suppressed_critical())
    return _round(dropped / len(crit))


__all__ = [
    "critical_signal_preservation",
    "false_suppression_rate",
    "preserved_critical",
    "suppressed_critical",
]
