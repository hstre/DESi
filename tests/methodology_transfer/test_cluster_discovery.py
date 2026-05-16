"""v5.0 — cluster discovery is deterministic and in
corridor."""
from __future__ import annotations

from desi.methodology_transfer.cluster_discovery import (
    collapse_to_corridor, discover_clusters,
)
from desi.methodology_transfer.corpus import all_chains
from desi.methodology_transfer.feature_extraction import (
    extract_features, is_failure,
)


def _failures() -> tuple:
    samples = [extract_features(c) for c in all_chains()]
    return tuple(s for s in samples if is_failure(s))


def test_clustering_is_deterministic() -> None:
    fails = _failures()
    a = discover_clusters(fails)
    b = discover_clusters(fails)
    assert tuple((c.member_ids, c.size) for c in a) == \
        tuple((c.member_ids, c.size) for c in b)


def test_no_chain_assigned_to_more_than_one_cluster() -> None:
    fails = _failures()
    seen: set[str] = set()
    for c in discover_clusters(fails):
        for m in c.member_ids:
            assert m not in seen, m
            seen.add(m)
    assert seen == {s.chain_id for s in fails}


def test_collapse_caps_cluster_count() -> None:
    fails = _failures()
    raw = discover_clusters(fails)
    capped = collapse_to_corridor(raw, max_clusters=12)
    assert len(capped) <= 12


def test_clusters_sorted_descending_by_size() -> None:
    fails = _failures()
    clusters = discover_clusters(fails)
    sizes = [c.size for c in clusters]
    assert sizes == sorted(sizes, reverse=True)


def test_cluster_ids_are_contiguous_and_kxx() -> None:
    fails = _failures()
    clusters = discover_clusters(fails)
    for i, c in enumerate(clusters, start=1):
        assert c.cluster_id == f"K{i:02d}", c.cluster_id
