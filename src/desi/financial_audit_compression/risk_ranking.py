"""v15.3 - risk ranking of audit cells.

Cells are ranked by audit priority. The key
structural lever from v15.2 is RECOVERABILITY:
within a blindness pool only one representative
firm needs an independent audit; the others are
recoverable from it, so their cells are discounted
by ``(1 - recoverability_signal)``. With fully
recoverable pools the redundant members' cells
drop to zero priority and are pruned first - that
is where the search compression comes from, and it
provably loses no signal the representative does
not already carry.

Reads no post-hoc label.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.financial_blindness import (
    pool_of, recoverability_signal,
)

from .audit_priority import AuditCell, audit_universe


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@lru_cache(maxsize=None)
def representative(firm_id: str) -> str:
    """The lexicographically smallest member of a
    firm's blindness pool audits on behalf of the
    pool."""
    return min(pool_of(firm_id).members)


def _discount() -> float:
    # recoverable members keep (1 - recoverability)
    # of their raw priority.
    return _round(1.0 - recoverability_signal())


def cell_priority(cell: AuditCell) -> float:
    """Raw signal strength, discounted if the cell
    belongs to a recoverable (non-representative)
    pool member."""
    if representative(cell.firm_id) == cell.firm_id:
        factor = 1.0
    else:
        factor = _discount()
    return _round(cell.value * factor)


@dataclass(frozen=True)
class RankedCell:
    firm_id: str
    axis: str
    priority: float
    is_critical: bool
    is_representative: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "firm_id": self.firm_id,
            "axis": self.axis,
            "priority": self.priority,
            "is_critical": self.is_critical,
            "is_representative":
                self.is_representative,
        }


def ranked_cells() -> tuple[RankedCell, ...]:
    rows: list[RankedCell] = []
    for c in audit_universe():
        rows.append(RankedCell(
            firm_id=c.firm_id,
            axis=c.axis,
            priority=cell_priority(c),
            is_critical=c.is_critical,
            is_representative=(
                representative(c.firm_id)
                == c.firm_id
            ),
        ))
    # priority desc, then deterministic tie-break.
    rows.sort(
        key=lambda r: (
            -r.priority, r.firm_id, r.axis,
        ),
    )
    return tuple(rows)


__all__ = [
    "RankedCell",
    "cell_priority",
    "ranked_cells",
    "representative",
]
