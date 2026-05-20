"""Aufgaben 3 + 4 + 5 + 7 — real-pipeline runner, metrics, gates."""
from __future__ import annotations

from desi.heldout_causal import (
    ALL_HELDOUT_CASES,
    HeldoutFailureClass,
    MIN_PRECISION,
    MIN_RECALL,
    compute_metrics,
    run_heldout,
)
from desi.heldout_causal.cases import HeldoutCategory


def test_runner_returns_one_outcome_per_case() -> None:
    outs = run_heldout()
    assert len(outs) == len(ALL_HELDOUT_CASES)


def test_runner_is_deterministic() -> None:
    a = [o.to_dict() for o in run_heldout()]
    b = [o.to_dict() for o in run_heldout()]
    assert a == b


def test_metrics_meet_hard_gates() -> None:
    m = compute_metrics(run_heldout())
    assert m.heldout_precision >= MIN_PRECISION
    assert m.heldout_recall >= MIN_RECALL
    assert m.false_positive_count == 0
    assert m.trap_block_rate == 1.0


def test_all_valid_chains_labeled_causal_chain() -> None:
    for o in run_heldout():
        if not o.expected_blocked:
            assert o.actual_rule == "causal_chain", (
                f"{o.case_id}: expected CAUSAL_CHAIN, got "
                f"{o.actual_rule}"
            )


def test_all_traps_blocked() -> None:
    for o in run_heldout():
        if o.expected_blocked:
            assert o.actual_final_state != "logically_supported", (
                f"{o.case_id}: trap was NOT blocked"
            )
            assert o.actual_rule != "causal_chain", o.case_id


def test_all_cycles_blocked() -> None:
    for o in run_heldout():
        if o.category == HeldoutCategory.D_CYCLE_TRAP.value:
            assert o.actual_rule != "causal_chain", o.case_id


def test_all_contradictions_blocked() -> None:
    for o in run_heldout():
        if o.category == HeldoutCategory.C_CONTRADICTION_TRAP.value:
            assert o.actual_rule != "causal_chain", o.case_id


def test_failure_class_enum_is_closed_seven_values() -> None:
    assert len(list(HeldoutFailureClass)) == 7
    assert {f.value for f in HeldoutFailureClass} == {
        "parser_shape_miss",
        "guard_too_strict",
        "guard_too_weak",
        "rule_too_narrow",
        "rule_too_broad",
        "benchmark_label_error",
        "unknown",
    }


def test_every_failed_case_carries_exactly_one_class() -> None:
    for o in run_heldout():
        if not o.correct:
            assert o.failure_class is not None, o.case_id
        else:
            assert o.failure_class is None, o.case_id
