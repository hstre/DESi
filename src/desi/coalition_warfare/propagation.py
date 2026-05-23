"""v9.2 — consensus / dissent metrics over the
detected coalition structure.

* ``consensus_integrity`` - fraction of detected
  coalitions correctly flagged as ARTIFICIAL
  (i.e., DESi does not endorse coordinated
  narratives as genuine consensus).
* ``dissent_preservation`` - fraction of
  ground-truth DISSENTERS that remain visible
  (no entry in any detected coalition).
"""
from __future__ import annotations

from .coalitions import (
    CoalitionRole, fixture,
)
from .lineage import detected_coalitions


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def consensus_integrity() -> float:
    """Every detected coalition must be flagged
    as ARTIFICIAL (i.e., its members all belong
    to the same ground-truth coalition). If a
    detected cluster overlaps ground-truth
    isolated actors, the integrity drops."""
    coalitions = detected_coalitions()
    if not coalitions:
        return 1.0
    by_id = {
        b.broadcast_id: b for b in fixture()
    }
    ok = 0
    for _, members in coalitions:
        cids = {
            by_id[m].coalition_id
            for m in members
        }
        # All members share exactly one
        # non-None coalition_id - clean
        # artificial consensus.
        if (
            len(cids) == 1
            and None not in cids
        ):
            ok += 1
    return _round(ok / len(coalitions))


def dissent_preservation() -> float:
    """Every ground-truth DISSENTER must remain
    OUTSIDE every detected coalition - their
    voices must stay visible."""
    dissenters = {
        b.broadcast_id for b in fixture()
        if b.coalition_role == (
            CoalitionRole.DISSENTER.value
        )
    }
    if not dissenters:
        return 1.0
    swallowed = set()
    for _, members in detected_coalitions():
        for m in members:
            if m in dissenters:
                swallowed.add(m)
    preserved = dissenters - swallowed
    return _round(
        len(preserved) / len(dissenters),
    )


def isolated_preservation() -> float:
    """Same property for ISOLATED actors -
    they must not get pulled into a detected
    coalition."""
    isolated = {
        b.broadcast_id for b in fixture()
        if b.coalition_role == (
            CoalitionRole.ISOLATED.value
        )
    }
    if not isolated:
        return 1.0
    swallowed = set()
    for _, members in detected_coalitions():
        for m in members:
            if m in isolated:
                swallowed.add(m)
    preserved = isolated - swallowed
    return _round(
        len(preserved) / len(isolated),
    )


__all__ = [
    "consensus_integrity",
    "dissent_preservation",
    "isolated_preservation",
]
