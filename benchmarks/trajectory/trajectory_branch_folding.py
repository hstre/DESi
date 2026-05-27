#!/usr/bin/env python3
"""Deterministic semantic branch folding (PERIPHERAL).

Folds semantically-equivalent alternatives (the brief's plausible_directions) into
one epistemic branch cluster, so branch diversity is measured over CLUSTERS, not
raw lexical direction count. Deterministic: stopword/filler reduction + a small
method-synonym canonicalisation + normalized-token Jaccard, union-found into
clusters. No LLM, no embeddings, no core change.

NOTE (honest scope): lexical folding catches RHETORICAL / parameter variants that
share vocabulary (e.g. "...rye cover crop..." vs "...crimson clover cover crop...");
it CANNOT fold lexically-disjoint paraphrases ("controlled longitudinal study" vs
"multi-year intervention trial", Jaccard~0) -- those need embeddings.
"""
from __future__ import annotations

import re

_FOLD_THRESH = 0.5

_STOP = frozenset((
    "the", "a", "an", "of", "to", "in", "on", "and", "or", "is", "are", "was",
    "with", "from", "by", "for", "at", "as", "that", "this", "using", "use",
    "based", "via", "across", "into", "per", "vs", "versus", "over", "under",
))
# method-role canonicalisation: rhetorical variants of the same role collapse
_SYN = {}
for _canon, _words in {
    "STUDY": ("study", "trial", "experiment", "experimental", "design", "investigation",
              "examination", "protocol", "approach", "method", "methodology"),
    "COMPARE": ("compare", "comparison", "comparing", "contrast", "contrasting", "pairwise", "paired"),
    "MODEL": ("model", "modeling", "modelling", "fit", "fitting", "regression", "bayesian",
              "hierarchical", "forward", "simulation", "simulate", "monte", "carlo"),
    "MEASURE": ("measure", "measurement", "estimate", "estimation", "quantify", "infer", "inference"),
    "OBSERVE": ("observational", "observation", "survey", "field", "fieldwork", "cohort", "panel"),
}.items():
    for _w in _words:
        _SYN[_w] = _canon


def _stem(t: str) -> str:
    return re.sub(r"(ing|ed|s)$", "", t)


def normalize(direction: str) -> frozenset:
    out = set()
    for t in re.findall(r"[a-z0-9\-]+", (direction or "").lower()):
        if t in _STOP or len(t) <= 2:
            continue
        st = _stem(t)
        out.add(_SYN.get(t, _SYN.get(st, st)))
    return frozenset(out)


def _jaccard(a: frozenset, b: frozenset) -> float:
    u = a | b
    return len(a & b) / len(u) if u else 0.0


def fold_directions(directions: list, thresh: float = _FOLD_THRESH) -> dict:
    """Cluster the brief's plausible_directions into epistemic branch clusters."""
    n = len(directions)
    norms = [normalize(d) for d in directions]
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    max_sim = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            s = _jaccard(norms[i], norms[j])
            max_sim = max(max_sim, s)
            if s >= thresh:
                parent[find(i)] = find(j)
    roots = {}
    cluster_ids = []
    for i in range(n):
        r = find(i)
        cluster_ids.append(roots.setdefault(r, len(roots)))
    n_clusters = len(roots)
    redundancy = round((n - n_clusters) / n, 3) if n else 0.0
    return {
        "cluster_ids": cluster_ids,            # per-direction cluster assignment
        "n_clusters": n_clusters,
        "n_directions": n,
        "branch_equivalence_score": round(max_sim, 3),   # closest-pair equivalence
        "branch_redundancy_ratio": redundancy,           # fraction of directions folded away
        "branch_novelty_score": round(n_clusters / n, 3) if n else 0.0,
    }


__all__ = ["fold_directions", "normalize"]
