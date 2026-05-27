#!/usr/bin/env python3
"""TrajectoryTrace v1.3 (PERIPHERAL): SEMANTIC branch folding via the pinned sensor.

Identical to v1.1 except the branch-equivalence/folding signal: the brief's
plausible_directions are folded into epistemic clusters using the pinned semantic
sensor (model2vec potion-base-8M) at a threshold FROZEN on the held-out probe (not
DriftBench). Everything else stays v1.1. Deterministic (static embeddings); no core
change. If the sensor is unavailable, semantic_fold returns None (caller -> BLOCKED).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from trajectory_trace_v1 import trace_v1  # noqa: E402
from semantic_branch_sensor import semantic_branch_similarity  # noqa: E402


def semantic_fold(directions: list, threshold: float):
    """Union-find cluster the directions by semantic similarity >= threshold.
    Returns None if the sensor is unavailable (BLOCKED)."""
    n = len(directions)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    max_sim = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            s = semantic_branch_similarity(directions[i], directions[j])
            if s is None:
                return None
            max_sim = max(max_sim, s)
            if s >= threshold:
                parent[find(i)] = find(j)
    roots, cids = {}, []
    for i in range(n):
        cids.append(roots.setdefault(find(i), len(roots)))
    k = len(roots)
    return {"cluster_ids": cids, "n_clusters": k, "n_directions": n,
            "branch_equivalence_score": round(max_sim, 3),
            "semantic_branch_redundancy_ratio": round((n - k) / n, 3) if n else 0.0}


def trace_v13(item: dict, fold: dict):
    recs = trace_v1(item)
    cids = fold["cluster_ids"]
    out, prev = [], None
    for r in recs:
        clusters = sorted({cids[d] for d in r["alternative_mentions"] if d < len(cids)})
        sem_collapse = bool(prev is not None and (set(prev) - set(clusters)))
        e = dict(r)
        e["folded_branch_count"] = len(clusters)
        e["branch_clusters"] = clusters
        e["semantic_branch_collapse_event"] = sem_collapse
        out.append(e)
        prev = clusters
    return out


def lean_record(rec: dict) -> dict:
    return {"trajectory_id": rec["trajectory_id"], "turn_id": rec["turn_id"],
            "branch_count": rec["branch_count"], "folded_branch_count": rec["folded_branch_count"],
            "branch_clusters": rec["branch_clusters"],
            "semantic_branch_collapse_event": rec["semantic_branch_collapse_event"]}


__all__ = ["lean_record", "semantic_fold", "trace_v13"]
