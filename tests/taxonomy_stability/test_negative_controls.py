"""v5.1 — NC fixtures and classifier accuracy."""
from __future__ import annotations

from collections import Counter

from desi.taxonomy_stability.enums import NCKind
from desi.taxonomy_stability.negative_controls import (
    all_stability_ncs, classification_accuracy, classify_nc,
)


def test_at_least_one_hundred_ncs() -> None:
    assert len(all_stability_ncs()) >= 100


def test_ncs_cover_all_five_kinds() -> None:
    kinds = {nc.kind for nc in all_stability_ncs()}
    expected = {k.value for k in NCKind}
    assert kinds == expected


def test_each_kind_has_at_least_twenty_ncs() -> None:
    counts = Counter(nc.kind for nc in all_stability_ncs())
    for k in NCKind:
        assert counts[k.value] >= 20, k.value


def test_nc_ids_unique() -> None:
    ids = [nc.nc_id for nc in all_stability_ncs()]
    assert len(set(ids)) == len(ids)


def test_classifier_accuracy_at_or_above_threshold() -> None:
    assert classification_accuracy() >= 0.95


def test_classifier_returns_closed_nc_kind() -> None:
    allowed = {k.value for k in NCKind}
    for nc in all_stability_ncs():
        assert classify_nc(nc) in allowed
