"""v36.3 - hop graph construction.

Builds the hop structure for a multi-hop task: the distinct
(non-redundant) hops, the redundant hops, the hops actually present
vs the required hops, and any missing hops. Missing hops are surfaced,
never silently dropped; redundant hops are identified for lossless
compression.
"""
from __future__ import annotations

from .musique_loader import MultiHopTask


def provided_ids(task: MultiHopTask) -> tuple[str, ...]:
    return tuple(h.hop_id for h in task.hops)


def distinct_hops(task: MultiHopTask) -> tuple[str, ...]:
    """Non-redundant hop ids, order preserved, de-duplicated."""
    seen: list[str] = []
    for h in task.hops:
        if not h.redundant and h.hop_id not in seen:
            seen.append(h.hop_id)
    return tuple(seen)


def redundant_hops(task: MultiHopTask) -> tuple[str, ...]:
    return tuple(h.hop_id for h in task.hops if h.redundant)


def missing_hops(task: MultiHopTask) -> tuple[str, ...]:
    present = {h.hop_id for h in task.hops}
    return tuple(r for r in task.required_hops if r not in present)


def spurious_hops(task: MultiHopTask) -> tuple[str, ...]:
    """Non-redundant present hops that are not in the required set
    (fabricated / off-path hops)."""
    req = set(task.required_hops)
    return tuple(
        h for h in distinct_hops(task) if h not in req
    )


def evidence_visible(task: MultiHopTask) -> bool:
    return all(bool(h.fact) for h in task.hops)


def compressed_chain(task: MultiHopTask) -> tuple[str, ...]:
    """Distinct present required hops, in order - the lossless
    compressed reasoning chain."""
    req = set(task.required_hops)
    return tuple(h for h in distinct_hops(task) if h in req)


__all__ = [
    "compressed_chain",
    "distinct_hops",
    "evidence_visible",
    "missing_hops",
    "provided_ids",
    "redundant_hops",
    "spurious_hops",
]
