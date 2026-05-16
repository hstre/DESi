"""v4.3 — effect measurement, before/after numbers, per-class
reduction, non-target invariants."""
from __future__ import annotations

from desi.external_audit_patch import (
    FALSE_SUPPORT_BEFORE, FALSE_SUPPORT_TARGET_AFTER,
    effect_measure,
)


def test_false_support_before_matches_v42() -> None:
    e = effect_measure()
    assert e.false_support_before == FALSE_SUPPORT_BEFORE == 143


def test_false_support_after_at_or_below_target() -> None:
    e = effect_measure()
    assert e.false_support_after <= FALSE_SUPPORT_TARGET_AFTER


def test_non_target_classes_not_silently_relabeled() -> None:
    e = effect_measure()
    assert e.non_target_relabel_count == 0


def test_per_class_reduction_only_in_targeted_classes() -> None:
    e = effect_measure()
    for p in e.per_class:
        if p.targeted:
            # Patched clusters should reduce to zero.
            assert p.after_count == 0, (p.cluster, p.after_count)
        else:
            # Non-target clusters must remain unchanged.
            assert p.before_count == p.after_count, (
                p.cluster, p.before_count, p.after_count,
            )


def test_external_recall_does_not_regress() -> None:
    e = effect_measure()
    # The patch must not reduce v4.1's external_recall on the
    # canonical F4 strategy.
    assert e.external_recall_after >= e.external_recall_before


def test_external_precision_improves() -> None:
    e = effect_measure()
    # Removing 119 false-supports must raise precision.
    assert e.external_precision_after > e.external_precision_before
