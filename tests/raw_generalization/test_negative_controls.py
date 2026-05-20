"""v5.4 — raw-corpus NCs and accuracy."""
from __future__ import annotations

from collections import Counter

from desi.raw_generalization.enums import NCKind
from desi.raw_generalization.negative_controls import (
    all_raw_ncs, classification_accuracy, classify_nc,
)


def test_at_least_one_hundred_ncs() -> None:
    assert len(all_raw_ncs()) >= 100


def test_ncs_cover_all_five_kinds() -> None:
    kinds = {nc.kind for nc in all_raw_ncs()}
    expected = {k.value for k in NCKind}
    assert kinds == expected


def test_each_kind_has_at_least_twenty_ncs() -> None:
    counts = Counter(nc.kind for nc in all_raw_ncs())
    for k in NCKind:
        assert counts[k.value] >= 20, k.value


def test_nc_ids_unique() -> None:
    ids = [nc.nc_id for nc in all_raw_ncs()]
    assert len(set(ids)) == len(ids)


def test_nc_accuracy_meets_threshold() -> None:
    assert classification_accuracy() >= 0.95


def test_classify_nc_returns_pair() -> None:
    for nc in all_raw_ncs()[:5]:
        a, f = classify_nc(nc)
        assert isinstance(a, str)
        assert isinstance(f, bool)
