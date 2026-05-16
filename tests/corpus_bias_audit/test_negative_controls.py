"""v5.3 — adversarial rewrite NCs."""
from __future__ import annotations

from collections import Counter

from desi.corpus_bias_audit.enums import NCKind
from desi.corpus_bias_audit.negative_controls import (
    all_rewrite_ncs, classification_accuracy, classify_nc,
)


def test_at_least_one_hundred_ncs() -> None:
    assert len(all_rewrite_ncs()) >= 100


def test_ncs_cover_all_five_kinds() -> None:
    kinds = {nc.kind for nc in all_rewrite_ncs()}
    expected = {k.value for k in NCKind}
    assert kinds == expected


def test_each_kind_has_at_least_twenty_ncs() -> None:
    counts = Counter(nc.kind for nc in all_rewrite_ncs())
    for k in NCKind:
        assert counts[k.value] >= 20, k.value


def test_nc_ids_unique() -> None:
    ids = [nc.nc_id for nc in all_rewrite_ncs()]
    assert len(set(ids)) == len(ids)


def test_classification_accuracy_meets_threshold() -> None:
    assert classification_accuracy() >= 0.95
