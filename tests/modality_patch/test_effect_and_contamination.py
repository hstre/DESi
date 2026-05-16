"""v4.7 — effect + contamination + non-target invariants."""
from __future__ import annotations

from desi.modality_patch import (
    EXPECTED_REDUCTION, TARGET_AFTER_COUNT,
    TARGET_BEFORE_COUNT, TARGET_CLUSTERS,
    contamination_check, effect_measure,
)


def test_contamination_is_zero() -> None:
    rep = contamination_check()
    assert rep.contamination_count == 0, [
        t[:80] for t in rep.contaminating_texts
    ]
    assert rep.protected_pool_size > 0


def test_effect_meets_target() -> None:
    e = effect_measure()
    assert e.false_support_before == TARGET_BEFORE_COUNT == 19
    assert e.false_support_after == TARGET_AFTER_COUNT == 9
    assert e.reduction == EXPECTED_REDUCTION == 10


def test_only_target_clusters_reduce() -> None:
    e = effect_measure()
    for p in e.per_class:
        if p.targeted:
            assert p.cluster in TARGET_CLUSTERS
            assert p.after_count == 0
            assert p.reduction == p.before_count
        else:
            assert p.before_count == p.after_count, (
                p.cluster, p.before_count, p.after_count,
            )
            assert p.reduction == 0


def test_non_target_relabel_count_is_zero() -> None:
    e = effect_measure()
    assert e.non_target_relabel_count == 0
