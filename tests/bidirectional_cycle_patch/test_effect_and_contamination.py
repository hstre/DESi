"""v4.5 — effect + contamination + non-target invariants."""
from __future__ import annotations

from desi.bidirectional_cycle_patch import (
    EXPECTED_REDUCTION, TARGET_AFTER_COUNT,
    TARGET_BEFORE_COUNT, TARGET_CLUSTER,
    contamination_check, effect_measure,
)


def test_contamination_is_zero() -> None:
    rep = contamination_check()
    assert rep.contamination_count == 0, [
        t[:80] for t in rep.contaminating_texts
    ]
    assert rep.protected_pool_size > 0


def test_effect_meets_target() -> None:
    e = effect_measure(TARGET_CLUSTER)
    assert e.false_support_before == TARGET_BEFORE_COUNT
    assert e.false_support_after == TARGET_AFTER_COUNT
    assert e.reduction == EXPECTED_REDUCTION


def test_only_target_cluster_reduces() -> None:
    e = effect_measure(TARGET_CLUSTER)
    for p in e.per_class:
        if p.targeted:
            assert p.cluster == TARGET_CLUSTER
            assert p.after_count == 0
            assert p.reduction == p.before_count
        else:
            assert p.before_count == p.after_count, (
                p.cluster, p.before_count, p.after_count,
            )
            assert p.reduction == 0


def test_non_target_relabel_count_is_zero() -> None:
    e = effect_measure(TARGET_CLUSTER)
    assert e.non_target_relabel_count == 0
