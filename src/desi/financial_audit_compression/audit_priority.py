"""v15.3 - the audit universe and per-cell audit
priority.

The brute-force audit search space is every
(firm, signature-axis) cell across the v15.2
corpus. Each cell gets an audit priority equal to
its structural signal strength. A cell is CRITICAL
if its signal is elevated - those are the cells a
compressed audit must never drop.

Reads no post-hoc label.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.financial_blindness import (
    SIGNATURE_AXES, signatures,
)

# A cell carrying a genuine audit signal.
CRITICAL_THRESHOLD = 0.40


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class AuditCell:
    firm_id: str
    sector: str
    axis: str
    value: float
    is_critical: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "firm_id": self.firm_id,
            "sector": self.sector,
            "axis": self.axis,
            "value": _round(self.value),
            "is_critical": self.is_critical,
        }


@lru_cache(maxsize=1)
def audit_universe() -> tuple[AuditCell, ...]:
    """Every (firm, axis) cell, in a fixed,
    deterministic order."""
    out: list[AuditCell] = []
    for sig in signatures():
        for i, axis in enumerate(SIGNATURE_AXES):
            v = sig.values[i]
            out.append(AuditCell(
                firm_id=sig.firm_id,
                sector=sig.sector,
                axis=axis,
                value=v,
                is_critical=v >= CRITICAL_THRESHOLD,
            ))
    out.sort(key=lambda c: (c.firm_id, c.axis))
    return tuple(out)


def critical_cells() -> tuple[AuditCell, ...]:
    return tuple(
        c for c in audit_universe() if c.is_critical
    )


def universe_size() -> int:
    return len(audit_universe())


__all__ = [
    "CRITICAL_THRESHOLD",
    "AuditCell",
    "audit_universe",
    "critical_cells",
    "universe_size",
]
