"""v4.11 — reproducibility-class fixtures."""
from __future__ import annotations

from desi.repro_audit import (
    MIN_CLASSIFICATION_ACCURACY, MIN_NC_COUNT,
    all_repro_ncs, classification_accuracy, classify_nc,
)


def test_at_least_20_ncs() -> None:
    assert len(all_repro_ncs()) >= MIN_NC_COUNT


def test_classification_accuracy_meets_threshold() -> None:
    assert classification_accuracy() >= (
        MIN_CLASSIFICATION_ACCURACY
    )


def test_every_nc_classifies_to_expected_class() -> None:
    for nc in all_repro_ncs():
        assert classify_nc(nc) == nc.expected_class, nc
