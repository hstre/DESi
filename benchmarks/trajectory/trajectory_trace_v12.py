#!/usr/bin/env python3
"""TrajectoryTrace v1.2 (PERIPHERAL): semantic branch FOLDING over v1.1.

Reuses the v1 per-turn trace, folds the brief's plausible_directions into epistemic
branch CLUSTERS, and re-expresses per-turn branch coverage over clusters
(folded_branch_count) instead of raw lexical directions. Collapse counts only when
a DISTINCT cluster disappears. Deterministic; no LLM/embeddings/Neo4j; core read-only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from trajectory_trace_v1 import trace_v1  # noqa: E402
from trajectory_branch_folding import fold_directions  # noqa: E402


def trace_v12(item: dict):
    recs = trace_v1(item)
    dirs = item.get("brief", {}).get("plausible_directions", []) or []
    fold = fold_directions(dirs)
    cids = fold["cluster_ids"]
    out = []
    prev = None
    for r in recs:
        clusters = sorted({cids[d] for d in r["alternative_mentions"] if d < len(cids)})
        sem_collapse = bool(prev is not None and (set(prev) - set(clusters)))  # a distinct cluster vanished
        e = dict(r)
        e["folded_branch_count"] = len(clusters)
        e["branch_clusters"] = clusters
        e["semantic_branch_collapse_event"] = sem_collapse
        out.append(e)
        prev = clusters
    return out, fold


def lean_record(rec: dict) -> dict:
    return {
        "trajectory_id": rec["trajectory_id"], "turn_id": rec["turn_id"],
        "branch_count": rec["branch_count"], "folded_branch_count": rec["folded_branch_count"],
        "branch_clusters": rec["branch_clusters"],
        "semantic_branch_collapse_event": rec["semantic_branch_collapse_event"],
        "drift_events": rec["drift_events"],
    }


__all__ = ["lean_record", "trace_v12"]
