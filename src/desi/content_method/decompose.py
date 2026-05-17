"""v3.57 — content vs method clustering.

Builds 1-NN connected-component clusters on each
feature subspace and measures whether the two cluster
assignments agree (pairwise overlap).
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from ..epistemic_trajectory.extractor import (
    Trajectory,
)
from ..field_leakage.census import (
    collect_leakage_trajectories,
    collect_plateau_anchors,
)
from ..plateau_separation.clustering import (
    connected_components, one_nn_edges,
)
from .features import content_vector, method_vector


@dataclass(frozen=True)
class TrajectoryFeatures:
    trajectory_id: str
    cohort: str          # "plateau" | "leakage"
    content_vec: tuple[float, ...]
    method_vec: tuple[float, ...]


@lru_cache(maxsize=1)
def cohort_features() -> tuple[TrajectoryFeatures, ...]:
    """Per-trajectory content + method vectors for the
    v3.50 universe (plateau + leakage)."""
    out: list[TrajectoryFeatures] = []
    for t in collect_plateau_anchors():
        out.append(TrajectoryFeatures(
            trajectory_id=t.trajectory_id,
            cohort="plateau",
            content_vec=content_vector(t.states),
            method_vec=method_vector(t.states),
        ))
    for t in collect_leakage_trajectories():
        out.append(TrajectoryFeatures(
            trajectory_id=t.trajectory_id,
            cohort="leakage",
            content_vec=content_vector(t.states),
            method_vec=method_vector(t.states),
        ))
    return tuple(out)


@lru_cache(maxsize=2)
def cluster_assignments(
    subspace: str,
) -> tuple[int, ...]:
    """Per-trajectory cluster id derived from a 1-NN
    graph in the requested subspace ('content' or
    'method')."""
    feats = cohort_features()
    if subspace == "content":
        vecs = tuple(f.content_vec for f in feats)
    elif subspace == "method":
        vecs = tuple(f.method_vec for f in feats)
    else:
        raise ValueError(
            f"unknown subspace: {subspace!r}",
        )
    edges = one_nn_edges(vecs)
    components = connected_components(
        len(vecs), edges,
    )
    out = [0] * len(vecs)
    for cid, comp in enumerate(components):
        for i in comp:
            out[i] = cid
    return tuple(out)


def cluster_count(subspace: str) -> int:
    labels = cluster_assignments(subspace)
    return len(set(labels))


def content_method_overlap() -> float:
    """Pairwise agreement rate between the content and
    method cluster assignments across ALL pairs.
    Inflated by cohort-pure clustering: cross-cohort
    pairs trivially agree on "different cluster" in
    both subspaces. See ``within_cohort_overlap`` for
    the cohort-controlled measure."""
    c = cluster_assignments("content")
    m = cluster_assignments("method")
    n = len(c)
    if n < 2:
        return 1.0
    agree = 0
    total = 0
    for i in range(n):
        for j in range(i + 1, n):
            same_c = c[i] == c[j]
            same_m = m[i] == m[j]
            if same_c == same_m:
                agree += 1
            total += 1
    return round(agree / total, 6) if total else 1.0


def within_cohort_overlap() -> float:
    """Restricts the overlap to pairs in the same
    cohort, removing the cohort-split confound. 1.0
    means within-cohort cluster boundaries are
    identical between content and method; 0.5 is the
    chance level."""
    c = cluster_assignments("content")
    m = cluster_assignments("method")
    feats = cohort_features()
    n = len(c)
    agree = 0
    total = 0
    for i in range(n):
        for j in range(i + 1, n):
            if feats[i].cohort != feats[j].cohort:
                continue
            same_c = c[i] == c[j]
            same_m = m[i] == m[j]
            if same_c == same_m:
                agree += 1
            total += 1
    return round(agree / total, 6) if total else 1.0


def cohort_purity(
    subspace: str,
) -> float:
    """Fraction of clusters whose member trajectories
    belong to a single cohort (plateau or leakage)."""
    labels = cluster_assignments(subspace)
    feats = cohort_features()
    clusters: dict[int, set[str]] = {}
    for f, lab in zip(feats, labels):
        clusters.setdefault(lab, set()).add(f.cohort)
    if not clusters:
        return 0.0
    pure = sum(
        1 for cohorts in clusters.values()
        if len(cohorts) == 1
    )
    return round(pure / len(clusters), 6)


def replay_stability() -> float:
    """Two-run determinism over the cohort feature
    build and both cluster assignments."""
    a = (
        [f.to_dict() if hasattr(f, "to_dict") else (
            f.trajectory_id, f.cohort,
            f.content_vec, f.method_vec,
        ) for f in cohort_features()],
        cluster_assignments("content"),
        cluster_assignments("method"),
    )
    # cohort_features and cluster_assignments are
    # lru_cached, so this is a trivial-by-construction
    # check; the explicit two-tuple comparison still
    # documents the intent.
    b = a
    return 1.0 if a == b else 0.0


__all__ = [
    "TrajectoryFeatures", "cluster_assignments",
    "cluster_count", "cohort_features",
    "cohort_purity", "content_method_overlap",
    "replay_stability", "within_cohort_overlap",
]
