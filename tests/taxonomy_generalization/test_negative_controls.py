"""v5.2 — negative-control fixtures and classifier
accuracy."""
from __future__ import annotations

from collections import Counter

from desi.taxonomy_generalization.enums import NCKind
from desi.taxonomy_generalization.negative_controls import (
    all_generalization_ncs, classification_accuracy,
    classify_nc,
)


def test_at_least_one_hundred_ncs() -> None:
    assert len(all_generalization_ncs()) >= 100


def test_ncs_cover_all_five_kinds() -> None:
    kinds = {nc.kind for nc in all_generalization_ncs()}
    expected = {k.value for k in NCKind}
    assert kinds == expected


def test_each_kind_has_at_least_twenty_ncs() -> None:
    counts = Counter(
        nc.kind for nc in all_generalization_ncs()
    )
    for k in NCKind:
        assert counts[k.value] >= 20, k.value


def test_nc_ids_unique() -> None:
    ids = [nc.nc_id for nc in all_generalization_ncs()]
    assert len(set(ids)) == len(ids)


def test_classifier_accuracy_meets_threshold() -> None:
    assert classification_accuracy() >= 0.95


def test_classify_nc_returns_string() -> None:
    for nc in all_generalization_ncs()[:5]:
        result = classify_nc(nc)
        assert isinstance(result, str)
