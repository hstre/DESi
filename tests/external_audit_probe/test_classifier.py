"""v4.2 — classifier closed-class coverage + NC accuracy."""
from __future__ import annotations

from desi.external_audit_probe import (
    ExternalAuditFailure, MIN_CLASSIFICATION_ACCURACY,
    all_failure_fixtures, classify_all,
    collect_false_support_cases, replay_all, replay_case,
    FalseSupportCase,
)


def test_classifier_assigns_one_closed_class_per_case() -> None:
    cases = collect_false_support_cases()
    records = replay_all(cases)
    ti = {c.chain_id: c.text for c in cases}
    classes = classify_all(records, ti)
    allowed = {f.value for f in ExternalAuditFailure}
    assert len(classes) == len(cases)
    for c in classes:
        assert c.failure_class in allowed


def test_nc_classification_accuracy_meets_threshold() -> None:
    fixtures = all_failure_fixtures()
    cases = tuple(
        FalseSupportCase(
            chain_id=f.nc_id, domain="negative_control_synthetic",
            text=f.text, ground_truth="INVALID",
        )
        for f in fixtures
    )
    records = tuple(replay_case(c) for c in cases)
    classes = classify_all(
        records, {c.chain_id: c.text for c in cases},
    )
    correct = sum(
        1 for f, c in zip(fixtures, classes)
        if c.failure_class == f.expected_class
    )
    rate = correct / len(fixtures)
    assert rate >= MIN_CLASSIFICATION_ACCURACY, (
        f"NC classification accuracy {rate} < "
        f"{MIN_CLASSIFICATION_ACCURACY}"
    )


def test_nc_bank_covers_every_closed_class() -> None:
    """Aufgabe 9 minimum: at least one fixture per closed
    class."""
    fixtures = all_failure_fixtures()
    expected_classes = {f.expected_class for f in fixtures}
    assert expected_classes == {
        f.value for f in ExternalAuditFailure
    }


def test_nc_bank_meets_size_floor() -> None:
    assert len(all_failure_fixtures()) >= 50
