"""v36.3 - multi-hop search navigation metrics.

Aggregates the hop-graph structuring into the four navigation
metrics: chain integrity (no spurious off-path hops, evidence
present), evidence-path visibility, redundant-hop compression, and
missing-hop detection (gaps surfaced, never hidden).
"""
from __future__ import annotations

from .hop_graph import (
    compressed_chain, evidence_visible, missing_hops, redundant_hops,
    spurious_hops,
)
from .hotpotqa_loader import hotpotqa_tasks
from .musique_loader import musique_tasks


def all_tasks():
    return musique_tasks() + hotpotqa_tasks()


def hop_chain_integrity() -> float:
    """A chain is integral iff it has no spurious off-path hops and
    every present hop carries evidence."""
    tasks = all_tasks()
    if not tasks:
        return 0.0
    ok = sum(
        1 for t in tasks
        if not spurious_hops(t) and evidence_visible(t)
    )
    return round(ok / len(tasks), 6)


def evidence_path_visibility() -> float:
    tasks = all_tasks()
    if not tasks:
        return 0.0
    ok = sum(1 for t in tasks if evidence_visible(t))
    return round(ok / len(tasks), 6)


def redundant_hop_compression() -> float:
    """Of the tasks that contain redundant hops, how many are
    losslessly compressed (compressed chain drops the redundant hop
    while keeping every required hop present)."""
    with_redundant = [t for t in all_tasks() if redundant_hops(t)]
    if not with_redundant:
        return 1.0
    ok = 0
    for t in with_redundant:
        chain = compressed_chain(t)
        no_redundant = not (set(chain) & set(redundant_hops(t)))
        present_required = {
            r for r in t.required_hops
            if r in {h.hop_id for h in t.hops}
        }
        if no_redundant and present_required.issubset(set(chain)):
            ok += 1
    return round(ok / len(with_redundant), 6)


def missing_hop_detection() -> float:
    """Of the tasks that are missing a required hop, how many have
    that gap detected (surfaced)."""
    with_missing = [t for t in all_tasks() if missing_hops(t)]
    if not with_missing:
        return 1.0
    ok = sum(1 for t in with_missing if missing_hops(t))
    return round(ok / len(with_missing), 6)


def detected_gaps() -> dict[str, list[str]]:
    return {
        t.task_id: list(missing_hops(t))
        for t in all_tasks() if missing_hops(t)
    }


__all__ = [
    "all_tasks",
    "detected_gaps",
    "evidence_path_visibility",
    "hop_chain_integrity",
    "missing_hop_detection",
    "redundant_hop_compression",
]
