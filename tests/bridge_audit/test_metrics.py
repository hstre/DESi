"""Tests for v2.4 funnel metrics (Aufgabe 4)."""
from __future__ import annotations

from desi.bridge_audit import (
    BridgeEntryAuditRunner,
    LossStage,
    compute_category_loss_distribution,
    compute_funnel_counts,
    dominant_loss_stage,
)


def test_funnel_counts_sum_to_thirty() -> None:
    run = BridgeEntryAuditRunner().run()
    counts = compute_funnel_counts(run)
    assert counts.total == 30


def test_funnel_counts_carry_nine_named_counters() -> None:
    run = BridgeEntryAuditRunner().run()
    counts = compute_funnel_counts(run)
    for f in (
        "parser_loss_count", "audit_reject_loss_count",
        "bridge_missing_loss_count", "consilium_veto_loss_count",
        "resolver_not_reached_count", "resolver_zero_depth_count",
        "cycle_not_recognized_count", "no_loss_count",
        "unknown_loss_count",
    ):
        assert hasattr(counts, f)


def test_funnel_counts_are_deterministic() -> None:
    a = compute_funnel_counts(BridgeEntryAuditRunner().run())
    b = compute_funnel_counts(BridgeEntryAuditRunner().run())
    assert a.to_dict() == b.to_dict()


def test_category_loss_distribution_covers_five_categories() -> None:
    run = BridgeEntryAuditRunner().run()
    dist = compute_category_loss_distribution(run)
    assert len(dist) == 5
    expected_cats = {
        "R1_two_step_bridge", "R2_three_step_bridge",
        "R3_four_step_closure", "R4_hidden_contradiction",
        "R5_cyclic_dependency",
    }
    assert set(dist.keys()) == expected_cats


def test_each_category_sums_to_six() -> None:
    """Aufgabe 6: kategorie-anzahl bleibt 5×6."""
    run = BridgeEntryAuditRunner().run()
    dist = compute_category_loss_distribution(run)
    for cat, per_stage in dist.items():
        total = sum(per_stage.values())
        assert total == 6, f"{cat}: total={total}"


def test_each_category_uses_only_enum_keys() -> None:
    run = BridgeEntryAuditRunner().run()
    dist = compute_category_loss_distribution(run)
    enum_values = {s.value for s in LossStage}
    for cat, per_stage in dist.items():
        for k in per_stage.keys():
            assert k in enum_values, f"{cat}: unknown stage {k}"


def test_dominant_loss_stage_returns_enum_member() -> None:
    run = BridgeEntryAuditRunner().run()
    counts = compute_funnel_counts(run)
    d = dominant_loss_stage(counts)
    assert d in set(LossStage)


def test_dominant_loss_stage_is_no_loss_when_all_zero() -> None:
    from desi.bridge_audit.metrics import FunnelCounts
    counts = FunnelCounts(0, 0, 0, 0, 0, 0, 0, 0, 0)
    assert dominant_loss_stage(counts) is LossStage.NO_LOSS
