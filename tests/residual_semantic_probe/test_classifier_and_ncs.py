"""v4.4 — classifier closed-class coverage + NC accuracy."""
from __future__ import annotations

from collections import Counter

from desi.residual_semantic_probe import (
    MIN_CLASSIFICATION_ACCURACY, MIN_NC_COUNT,
    ResidualSemanticFailure, ResidueCase, all_semantic_ncs,
    classify, classify_all, collect_residue_cases, replay_all,
    replay_case,
)


def test_classifier_assigns_one_closed_class_per_residue_case() -> None:
    cases = collect_residue_cases()
    records = replay_all(cases)
    ti = {c.chain_id: c.text for c in cases}
    cls = classify_all(records, ti)
    allowed = {f.value for f in ResidualSemanticFailure}
    assert len(cls) == len(cases)
    for c in cls:
        assert c.failure_class in allowed


def test_nc_count_meets_directive_minima() -> None:
    ncs = all_semantic_ncs()
    assert len(ncs) >= MIN_NC_COUNT
    family_counts = Counter(n.directive_family for n in ncs)
    assert family_counts["cycle_disguise"] >= 20
    assert family_counts["frame_switch"] >= 20
    assert family_counts["non_sequitur"] >= 20


def test_nc_classification_accuracy_meets_threshold() -> None:
    ncs = all_semantic_ncs()
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


def test_nc_bank_covers_every_directive_family_class_target() -> None:
    """Each NC carries one of the v4.4 closed classes as its
    expected label. The bank must cover at least the four
    classes the residue actually exercises plus
    CROSS_DOMAIN_ANALOGY (zero-overlap fixtures)."""
    expected_classes = {n.expected_class for n in all_semantic_ncs()}
    assert ResidualSemanticFailure.BIDIRECTIONAL_CYCLE.value in (
        expected_classes
    )
    assert ResidualSemanticFailure.CONCLUSION_LEAP.value in (
        expected_classes
    )
    assert ResidualSemanticFailure.UNJUSTIFIED_GENERALIZATION.value in (
        expected_classes
    )
    assert ResidualSemanticFailure.SEMANTIC_SCOPE_COLLAPSE.value in (
        expected_classes
    )
    assert ResidualSemanticFailure.CAUSAL_BRIDGE_MISSING.value in (
        expected_classes
    )
    assert ResidualSemanticFailure.CROSS_DOMAIN_ANALOGY.value in (
        expected_classes
    )
