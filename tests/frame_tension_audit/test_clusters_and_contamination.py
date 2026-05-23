"""Aufgaben 5 + 6 + 7 — cluster analysis + contamination probe."""
from __future__ import annotations

from desi.frame_tension_audit.clusters import (
    MIN_PATCHABLE_SIZE,
    build_clusters,
    summarise_clusters,
)
from desi.frame_tension_audit.contamination import (
    probe_all_clusters,
    probe_cluster,
)
from desi.frame_tension_audit.extractor import extract_tension_targets
from desi.frame_tension_audit.splitter import split_tension_targets


def _outcomes():
    return split_tension_targets(extract_tension_targets())


def test_clusters_exclude_true_tension() -> None:
    # Only FALSE / AMBIGUOUS cases participate in clustering.
    clusters = build_clusters(_outcomes())
    cluster_case_ids = {
        cid for c in clusters for cid in c.case_ids
    }
    for o in _outcomes():
        if o.audit_class.value == "true_tension":
            assert o.target.case_id not in cluster_case_ids


def test_cluster_summary_consistent_with_cluster_list() -> None:
    clusters = build_clusters(_outcomes())
    summary = summarise_clusters(clusters)
    assert summary.cluster_count == len(clusters)
    if clusters:
        assert summary.largest_cluster_size == max(
            c.size for c in clusters
        )


def test_contamination_probe_runs_for_every_cluster() -> None:
    clusters = build_clusters(_outcomes())
    results = probe_all_clusters(clusters)
    assert len(results) == len(clusters)
    cluster_ids = {c.cluster_id for c in clusters}
    result_ids = {r.cluster_id for r in results}
    assert cluster_ids == result_ids


def test_contamination_probes_six_pools() -> None:
    clusters = build_clusters(_outcomes())
    if not clusters:
        return  # nothing to probe
    r = probe_cluster(clusters[0])
    assert set(r.pool_hits) == {
        "v1_5_main",
        "v3_4_frame_benchmark",
        "v3_5_invariance",
        "v3_8_false_inheritance",
        "v3_9_manipulation_set",
        "v3_9_corpus_tension",
    }


def test_min_patchable_size_is_at_least_three() -> None:
    assert MIN_PATCHABLE_SIZE >= 3


def test_probe_is_deterministic() -> None:
    clusters = build_clusters(_outcomes())
    a = [r.to_dict() for r in probe_all_clusters(clusters)]
    b = [r.to_dict() for r in probe_all_clusters(clusters)]
    assert a == b


def test_manipulation_absorption_zero_for_known_safe_cluster() -> None:
    # The v3.9 corpus tension pair (info ↔ metaphor) does not
    # touch any v3.9 manipulation case, so absorption must be 0
    # for that cluster. If a future change makes the manipulation
    # set overlap a clustered pair, this test catches it.
    clusters = build_clusters(_outcomes())
    for c in clusters:
        r = probe_cluster(c)
        if (c.outer_frame, c.inner_frame) == (
            "information_theoretic", "metaphorical",
        ):
            assert r.manipulation_absorption_risk == 0.0
