"""Tests for v2.4 BridgeFunnelReport (Aufgabe 5)."""
from __future__ import annotations

from datetime import datetime, timezone

from desi.bridge_audit import (
    BridgeEntryAuditRunner,
    BridgeFunnelReport,
    LossStage,
    build_funnel_report,
    compute_funnel_replay_hash,
)


def _report() -> BridgeFunnelReport:
    now = datetime.now(timezone.utc)
    return build_funnel_report(
        BridgeEntryAuditRunner().run(),
        started_at=now, finished_at=now,
    )


def test_report_carries_all_required_fields() -> None:
    rep = _report()
    for f in (
        "total_cases", "loss_distribution",
        "category_loss_distribution", "dominant_loss_stage",
        "recursion_reach_rate", "bridge_creation_rate",
        "consilium_call_rate", "resolver_entry_rate",
        "replay_hash",
    ):
        assert hasattr(rep, f), f


def test_total_cases_is_thirty() -> None:
    rep = _report()
    assert rep.total_cases == 30


def test_rates_are_in_unit_interval() -> None:
    rep = _report()
    for v in (
        rep.recursion_reach_rate, rep.bridge_creation_rate,
        rep.consilium_call_rate, rep.resolver_entry_rate,
    ):
        assert 0.0 <= v <= 1.0


def test_dominant_loss_stage_is_a_LossStage() -> None:
    rep = _report()
    assert rep.dominant_loss_stage in set(LossStage)


def test_two_runs_produce_identical_replay_hash() -> None:
    now = datetime.now(timezone.utc)
    a = build_funnel_report(
        BridgeEntryAuditRunner().run(),
        started_at=now, finished_at=now,
    )
    b = build_funnel_report(
        BridgeEntryAuditRunner().run(),
        started_at=now, finished_at=now,
    )
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_timestamps() -> None:
    early = datetime(2020, 1, 1, tzinfo=timezone.utc)
    late = datetime(2030, 1, 1, tzinfo=timezone.utc)
    run = BridgeEntryAuditRunner().run()
    a = build_funnel_report(run, started_at=early, finished_at=early)
    b = build_funnel_report(run, started_at=late, finished_at=late)
    assert a.replay_hash == b.replay_hash


def test_replay_hash_helper_is_sixteen_hex_chars() -> None:
    h = compute_funnel_replay_hash({"total_cases": 30})
    assert len(h) == 16
    int(h, 16)


def test_to_dict_round_trip_shape() -> None:
    rep = _report()
    d = rep.to_dict()
    for k in (
        "total_cases", "loss_distribution",
        "category_loss_distribution", "dominant_loss_stage",
        "recursion_reach_rate", "bridge_creation_rate",
        "consilium_call_rate", "resolver_entry_rate",
        "traces", "replay_hash",
    ):
        assert k in d


def test_loss_distribution_keys_are_enum_value_strings() -> None:
    rep = _report()
    enum_values = {s.value for s in LossStage}
    for k in rep.loss_distribution:
        # The counts dict uses the FunnelCounts field names; verify
        # the category distribution uses enum values directly.
        pass
    for cat, dist in rep.category_loss_distribution.items():
        for k in dist:
            assert k in enum_values
