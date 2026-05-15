"""Tests for v2.4 BridgeEntryTrace (Aufgabe 1)."""
from __future__ import annotations

from desi.bridge_audit import (
    BridgeEntryTrace,
    LossStage,
    classify_loss_stage,
    trace_replay_hash,
)
from desi.recursive import BlockingReason, ResolutionState


def test_trace_carries_sixteen_required_fields() -> None:
    """Aufgabe 1 lists every required field by name."""
    fields = (
        "case_id", "parser_recognized", "premise_count", "premise_kinds",
        "audit_state", "bridge_created", "bridge_count", "bridge_kinds",
        "consilium_called", "consilium_verdicts", "veto_roles",
        "resolver_entered", "depth_reached", "final_state",
        "loss_stage", "replay_hash",
    )
    t = BridgeEntryTrace(
        case_id="X", parser_recognized=True, premise_count=2,
        premise_kinds=("conditional", "atomic"),
        audit_state="logically_supported",
        bridge_created=False, bridge_count=0, bridge_kinds=(),
        consilium_called=False, consilium_verdicts=(),
        veto_roles=(), resolver_entered=False, depth_reached=0,
        final_state=ResolutionState.RESOLUTION_COMPLETE,
        loss_stage=LossStage.NO_LOSS, replay_hash="0" * 16,
    )
    for f in fields:
        assert hasattr(t, f), f


def test_classifier_no_loss_when_state_matches_and_depth_met() -> None:
    s = classify_loss_stage(
        parser_recognized=True, premise_count=2,
        audit_state="logically_supported",
        bridge_created=False, consilium_called=False,
        consilium_verdicts=(), veto_roles=(),
        resolver_entered=False, depth_reached=2,
        final_state=ResolutionState.RESOLUTION_COMPLETE,
        blocking_reason=None, expected_cycle=False,
        expected_min_depth=2,
        expected_final_state=ResolutionState.RESOLUTION_COMPLETE,
        expected_blocked=False,
    )
    assert s is LossStage.NO_LOSS


def test_classifier_parser_loss_when_no_premises() -> None:
    s = classify_loss_stage(
        parser_recognized=False, premise_count=0,
        audit_state="", bridge_created=False, consilium_called=False,
        consilium_verdicts=(), veto_roles=(),
        resolver_entered=False, depth_reached=0,
        final_state=ResolutionState.RESOLUTION_BLOCKED,
        blocking_reason=BlockingReason.PARSER_UNSUPPORTED_FORM,
        expected_cycle=False, expected_min_depth=1,
        expected_final_state=ResolutionState.RESOLUTION_COMPLETE,
        expected_blocked=False,
    )
    assert s is LossStage.PARSER_LOSS


def test_classifier_audit_reject_loss() -> None:
    s = classify_loss_stage(
        parser_recognized=True, premise_count=2,
        audit_state="logically_rejected",
        bridge_created=False, consilium_called=False,
        consilium_verdicts=(), veto_roles=(),
        resolver_entered=False, depth_reached=0,
        final_state=ResolutionState.RESOLUTION_BLOCKED,
        blocking_reason=None,
        expected_cycle=False, expected_min_depth=0,
        expected_final_state=ResolutionState.RESOLUTION_BLOCKED,
        expected_blocked=True,
    )
    assert s is LossStage.AUDIT_REJECT_LOSS


def test_classifier_cycle_not_recognized() -> None:
    s = classify_loss_stage(
        parser_recognized=True, premise_count=3,
        audit_state="gap_detected",
        bridge_created=True, consilium_called=True,
        consilium_verdicts=("accept_as_bridge",), veto_roles=(),
        resolver_entered=True, depth_reached=1,
        final_state=ResolutionState.RESOLUTION_BLOCKED,
        blocking_reason=None,
        expected_cycle=True, expected_min_depth=0,
        expected_final_state=ResolutionState.RESOLUTION_BLOCKED,
        expected_blocked=True,
    )
    assert s is LossStage.CYCLE_NOT_RECOGNIZED


def test_classifier_consilium_veto_loss() -> None:
    s = classify_loss_stage(
        parser_recognized=True, premise_count=3,
        audit_state="gap_detected",
        bridge_created=True, consilium_called=True,
        consilium_verdicts=("veto",), veto_roles=("skeptic",),
        resolver_entered=True, depth_reached=0,
        final_state=ResolutionState.RESOLUTION_BLOCKED,
        blocking_reason=None,
        expected_cycle=False, expected_min_depth=1,
        expected_final_state=ResolutionState.RESOLUTION_COMPLETE,
        expected_blocked=False,
    )
    assert s is LossStage.CONSILIUM_VETO_LOSS


def test_classifier_resolver_zero_depth() -> None:
    s = classify_loss_stage(
        parser_recognized=True, premise_count=2,
        audit_state="gap_detected",
        bridge_created=True, consilium_called=True,
        consilium_verdicts=("accept_as_bridge",), veto_roles=(),
        resolver_entered=True, depth_reached=0,
        final_state=ResolutionState.RESOLUTION_BLOCKED,
        blocking_reason=None,
        expected_cycle=False, expected_min_depth=2,
        expected_final_state=ResolutionState.RESOLUTION_COMPLETE,
        expected_blocked=False,
    )
    assert s is LossStage.RESOLVER_ZERO_DEPTH


def test_classifier_returns_only_enum_values() -> None:
    """Hard constraint: classifier never returns anything outside
    the closed enum."""
    s = classify_loss_stage(
        parser_recognized=True, premise_count=1,
        audit_state="logically_supported",
        bridge_created=False, consilium_called=False,
        consilium_verdicts=(), veto_roles=(),
        resolver_entered=False, depth_reached=0,
        final_state=ResolutionState.RESOLUTION_COMPLETE,
        blocking_reason=None,
        expected_cycle=False, expected_min_depth=0,
        expected_final_state=ResolutionState.RESOLUTION_COMPLETE,
        expected_blocked=False,
    )
    assert s in set(LossStage)


def test_replay_hash_is_deterministic() -> None:
    payload = {"a": 1, "b": [2, 3], "case_id": "X"}
    a = trace_replay_hash(payload)
    b = trace_replay_hash(payload)
    assert a == b
    assert len(a) == 16


def test_replay_hash_ignores_its_own_field() -> None:
    p1 = {"a": 1, "replay_hash": "x"}
    p2 = {"a": 1, "replay_hash": "y"}
    assert trace_replay_hash(p1) == trace_replay_hash(p2)
