"""v4.8 — classifier coverage + NC accuracy."""
from __future__ import annotations

from collections import Counter

from desi.content_audit_probe import (
    ContentFailure, MIN_CLASSIFICATION_ACCURACY,
    MIN_NC_COUNT, ResidueCase, all_content_ncs,
    classify, classify_all, collect_residue_cases,
    replay_all, replay_case,
)


def test_classifier_assigns_one_closed_class_per_case() -> None:
    cases = collect_residue_cases()
    records = replay_all(cases)
    ti = {c.chain_id: c.text for c in cases}
    cls = classify_all(records, ti)
    allowed = {f.value for f in ContentFailure}
    assert len(cls) == len(cases)
    for c in cls:
        assert c.failure_class in allowed


def test_v48_residue_distribution_pinned_in_frozen_artifact() -> None:
    """At v4.8 time the residue split exactly between
    PROPERTY_REVERSAL (5) and DIRECT_CONTRADICTION (4).
    After v4.9 the live residue is empty. We pin the v4.8-era
    distribution via the frozen artifact."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_8" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    counts = data["distribution"]["failure_count"]
    assert counts.get(
        ContentFailure.PROPERTY_REVERSAL.value, 0,
    ) == 5
    assert counts.get(
        ContentFailure.DIRECT_CONTRADICTION.value, 0,
    ) == 4
    assert counts.get(
        ContentFailure.UNKNOWN.value, 0,
    ) == 0


def test_nc_count_meets_directive_minima() -> None:
    ncs = all_content_ncs()
    assert len(ncs) >= MIN_NC_COUNT
    counts = Counter(n.cohort for n in ncs)
    assert counts["contradiction_pair"] >= 20
    assert counts["inversion_case"] >= 20
    assert counts["valid_content_preserving"] >= 20


def test_nc_classification_accuracy_meets_threshold() -> None:
    ncs = all_content_ncs()
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
