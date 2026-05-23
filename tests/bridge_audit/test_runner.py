"""Tests for the v2.4 BridgeEntryAuditRunner (Aufgaben 3, 6)."""
from __future__ import annotations

from desi.benchmark_multistep import ALL_MULTISTEP_CASES
from desi.bridge_audit import (
    BridgeEntryAuditRunner,
    BridgeEntryTrace,
    LossStage,
)


def test_runner_traces_thirty_cases() -> None:
    run = BridgeEntryAuditRunner().run()
    assert len(run.traces) == 30


def test_runner_uses_v23_case_ids() -> None:
    run = BridgeEntryAuditRunner().run()
    case_ids = {t.case_id for t in run.traces}
    expected = {c.case_id for c in ALL_MULTISTEP_CASES}
    assert case_ids == expected


def test_each_trace_is_a_BridgeEntryTrace() -> None:
    run = BridgeEntryAuditRunner().run()
    for t in run.traces:
        assert isinstance(t, BridgeEntryTrace)


def test_two_runs_produce_identical_replay_hashes() -> None:
    a = BridgeEntryAuditRunner().run()
    b = BridgeEntryAuditRunner().run()
    for ta, tb in zip(a.traces, b.traces):
        assert ta.replay_hash == tb.replay_hash, ta.case_id


def test_two_runs_produce_identical_loss_stages() -> None:
    a = BridgeEntryAuditRunner().run()
    b = BridgeEntryAuditRunner().run()
    for ta, tb in zip(a.traces, b.traces):
        assert ta.loss_stage is tb.loss_stage, ta.case_id


def test_every_loss_stage_is_in_closed_enum() -> None:
    run = BridgeEntryAuditRunner().run()
    for t in run.traces:
        assert t.loss_stage in set(LossStage), (
            f"trace produced out-of-enum loss_stage: {t.loss_stage}"
        )


def test_premise_count_is_nonnegative() -> None:
    run = BridgeEntryAuditRunner().run()
    for t in run.traces:
        assert t.premise_count >= 0


def test_depth_reached_is_nonnegative() -> None:
    run = BridgeEntryAuditRunner().run()
    for t in run.traces:
        assert t.depth_reached >= 0


def test_trace_to_dict_round_trip_shape() -> None:
    run = BridgeEntryAuditRunner().run()
    t = run.traces[0]
    d = t.to_dict()
    for k in (
        "case_id", "parser_recognized", "premise_count",
        "premise_kinds", "audit_state", "bridge_created",
        "bridge_count", "bridge_kinds", "consilium_called",
        "consilium_verdicts", "veto_roles", "resolver_entered",
        "depth_reached", "final_state", "loss_stage", "replay_hash",
    ):
        assert k in d, k


def test_run_carries_timestamp() -> None:
    run = BridgeEntryAuditRunner().run()
    assert run.timestamp is not None
