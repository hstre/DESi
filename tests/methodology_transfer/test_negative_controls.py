"""v5.0 — negative-control fixtures and accuracy."""
from __future__ import annotations

from desi.methodology_transfer.negative_controls import (
    all_transfer_ncs, classification_accuracy, classify_nc,
)
from desi.methodology_transfer.taxonomy import TaxonomyClass


def test_at_least_one_hundred_ncs() -> None:
    assert len(all_transfer_ncs()) >= 100


def test_nc_ids_unique() -> None:
    ids = [nc.nc_id for nc in all_transfer_ncs()]
    assert len(set(ids)) == len(ids)


def test_nc_expected_classes_are_closed() -> None:
    allowed = {c.value for c in TaxonomyClass}
    for nc in all_transfer_ncs():
        assert nc.expected_class in allowed


def test_nc_classification_accuracy_threshold() -> None:
    assert classification_accuracy() >= 0.95


def test_classify_nc_returns_closed_name() -> None:
    allowed = {c.value for c in TaxonomyClass}
    for nc in all_transfer_ncs():
        assert classify_nc(nc) in allowed


def test_nc_families_cover_at_least_six_classes() -> None:
    families = {nc.family for nc in all_transfer_ncs()}
    assert len(families) >= 6
