"""v4.6 — classifier closed-class coverage + NC accuracy."""
from __future__ import annotations

from collections import Counter

from desi.warrant_probe import (
    MIN_CLASSIFICATION_ACCURACY, MIN_NC_COUNT,
    ResidueCase, WarrantFailure, all_warrant_ncs,
    classify, classify_all, collect_residue_cases,
    replay_all, replay_case,
)


def test_classifier_assigns_one_closed_class_per_residue_case() -> None:
    cases = collect_residue_cases()
    records = replay_all(cases)
    ti = {c.chain_id: c.text for c in cases}
    cls = classify_all(records, ti)
    allowed = {f.value for f in WarrantFailure}
    assert len(cls) == len(cases)
    for c in cls:
        assert c.failure_class in allowed


def test_nc_count_meets_directive_minima() -> None:
    ncs = all_warrant_ncs()
    assert len(ncs) >= MIN_NC_COUNT
    counts = Counter(n.directive_family for n in ncs)
    assert counts["missing_bridge"] >= 20
    assert counts["scope_extension"] >= 20
    assert counts["generalization_leap"] >= 20


def test_nc_classification_accuracy_meets_threshold() -> None:
    ncs = all_warrant_ncs()
    correct = 0
    for nc in ncs:
        case = ResidueCase(
            chain_id=nc.nc_id, domain="nc",
            text=nc.text, ground_truth="INVALID",
        )
        rec = replay_case(case)
        c = classify(rec, nc.text)
        if c.failure_class == nc.expected_class:
            correct += 1
    rate = correct / len(ncs)
    assert rate >= MIN_CLASSIFICATION_ACCURACY, rate


def test_nc_bank_covers_required_warrant_classes() -> None:
    expected = {n.expected_class for n in all_warrant_ncs()}
    assert WarrantFailure.MISSING_BRIDGE_RULE.value in expected
    assert WarrantFailure.SCOPE_EXTENSION.value in expected
    assert WarrantFailure.SAMPLE_TO_UNIVERSAL.value in expected
    assert (
        WarrantFailure.CORRELATION_TO_CAUSATION.value
        in expected
    )
