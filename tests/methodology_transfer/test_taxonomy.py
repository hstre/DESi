"""v5.0 — closed taxonomy, no v4 reuse."""
from __future__ import annotations

from desi.methodology_transfer.report import build_report
from desi.methodology_transfer.taxonomy import (
    TaxonomyClass, assign_names,
)


_V4_FORBIDDEN_NAMES: frozenset[str] = frozenset({
    # external_probe failure classes (Domain B)
    "MARKER_LEAKAGE_VALID_AS_INVALID",
    "MARKER_LEAKAGE_INVALID_AS_VALID",
    "POLARITY_INVERSION",
    "CYCLE_DISGUISE",
    "OVER_BLOCK",
    "AMBIGUITY_OVER_DECISION",
    "AMBIGUITY_OVER_BLOCK",
    "NO_FAILURE",
    # marker IDs from v4.x lines that might leak
    "MARKER_OVERRIDE_BUG",
})


def test_taxonomy_classes_are_closed_and_unique() -> None:
    values = [c.value for c in TaxonomyClass]
    assert len(set(values)) == len(values)
    # Every class name carries the new MT_ prefix.
    for v in values:
        assert v.startswith("MT_"), v


def test_no_v4_class_name_appears_in_v5_taxonomy() -> None:
    v5_values = {c.value for c in TaxonomyClass}
    assert v5_values & _V4_FORBIDDEN_NAMES == set()


def test_taxonomy_has_between_five_and_twelve_entries() -> None:
    r = build_report()
    assert 5 <= r.cluster_count <= 12


def test_largest_cluster_at_least_fifteen_percent() -> None:
    r = build_report()
    assert r.largest_cluster_fraction >= 0.15


def test_unknown_fraction_at_most_ten_percent() -> None:
    r = build_report()
    assert r.metrics.unknown_fraction <= 0.10


def test_every_taxonomy_entry_uses_closed_name() -> None:
    r = build_report()
    allowed = {c.value for c in TaxonomyClass}
    for t in r.taxonomy:
        assert t.taxonomy_name in allowed, t.taxonomy_name


def test_taxonomy_member_ids_unique() -> None:
    r = build_report()
    seen: set[str] = set()
    for t in r.taxonomy:
        for m in t.member_ids:
            assert m not in seen, m
            seen.add(m)
