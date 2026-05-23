"""v5.1 — canonical baseline freeze."""
from __future__ import annotations

from desi.taxonomy_stability.baseline import (
    load_canonical_baseline,
)


def test_baseline_chain_count_is_565() -> None:
    assert load_canonical_baseline().chain_count == 565


def test_baseline_cluster_count_is_eight() -> None:
    assert load_canonical_baseline().cluster_count == 8


def test_baseline_failure_count_is_346() -> None:
    assert load_canonical_baseline().failure_count == 346


def test_baseline_largest_cluster_is_v50_value() -> None:
    """v5.0 reported 0.563584; v5.1 must read the same."""
    b = load_canonical_baseline()
    assert b.largest_cluster_fraction == 0.563584


def test_baseline_clusters_unique_names() -> None:
    b = load_canonical_baseline()
    names = [c.name for c in b.clusters]
    assert len(set(names)) == len(names)


def test_baseline_member_map_covers_all_clusters() -> None:
    b = load_canonical_baseline()
    member_count = sum(c.size for c in b.clusters)
    assert len(b.member_to_cluster) == member_count


def test_baseline_class_names_all_mt_prefix() -> None:
    """v5.0 contract — no v4 names; every canonical cluster
    name carries the MT_ prefix."""
    for c in load_canonical_baseline().clusters:
        assert c.name.startswith("MT_"), c.name
