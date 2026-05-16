"""Aufgaben 3 + 4 + 7 — held-out runner, metrics, failure classes.

Runs every case through the real ``LogicalAuditor`` (no mocks)
and records the actual rule, state, gap, and bridges produced
by the production pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..logic.audit import LogicalAuditor, LogicalState
from ..logic.inference import InferenceRule
from .cases import ALL_HELDOUT_CASES, HeldoutCase, HeldoutCategory


class HeldoutFailureClass(str, Enum):
    """Aufgabe 7 — closed taxonomy of failure causes."""

    PARSER_SHAPE_MISS     = "parser_shape_miss"
    GUARD_TOO_STRICT      = "guard_too_strict"
    GUARD_TOO_WEAK        = "guard_too_weak"
    RULE_TOO_NARROW       = "rule_too_narrow"
    RULE_TOO_BROAD        = "rule_too_broad"
    BENCHMARK_LABEL_ERROR = "benchmark_label_error"
    UNKNOWN               = "unknown"


@dataclass(frozen=True)
class HeldoutOutcome:
    case_id: str
    category: str
    text: str
    expected_final_state: str
    expected_rule: str | None
    expected_blocked: bool
    trap_type: str
    actual_final_state: str
    actual_rule: str | None
    blocked_reason: str | None
    replay_hash: str | None
    matched_guard: str | None
    depth_reached: int
    correct: bool
    failure_class: HeldoutFailureClass | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "text": self.text,
            "expected_final_state": self.expected_final_state,
            "expected_rule": self.expected_rule,
            "expected_blocked": self.expected_blocked,
            "trap_type": self.trap_type,
            "actual_final_state": self.actual_final_state,
            "actual_rule": self.actual_rule,
            "blocked_reason": self.blocked_reason,
            "replay_hash": self.replay_hash,
            "matched_guard": self.matched_guard,
            "depth_reached": self.depth_reached,
            "correct": self.correct,
            "failure_class": (
                self.failure_class.value if self.failure_class else None
            ),
        }


def _matched_guard(case: HeldoutCase) -> str | None:
    if case.trap_type == "negation_pair":
        return "negation_guard"
    if case.trap_type == "cycle_connective":
        return "cycle_connective_guard"
    if case.trap_type == "token_cycle":
        return "token_cycle_guard"
    if case.trap_type == "quantifier_marker":
        return "quantifier_guard"
    if case.trap_type == "recycled_conclusion":
        return "recycled_conclusion_guard"
    return None


def _classify_failure(
    case: HeldoutCase,
    state: LogicalState,
    rule: InferenceRule | None,
) -> HeldoutFailureClass:
    # Valid chain expected to be supported but came back blocked.
    if case.expected_rule is InferenceRule.CAUSAL_CHAIN and (
        rule is not InferenceRule.CAUSAL_CHAIN
    ):
        if state is LogicalState.LOGICALLY_REJECTED:
            return HeldoutFailureClass.RULE_TOO_NARROW
        if state in (
            LogicalState.GAP_DETECTED, LogicalState.BRIDGE_REQUIRED,
        ):
            return HeldoutFailureClass.PARSER_SHAPE_MISS
        return HeldoutFailureClass.UNKNOWN

    # Trap expected to be blocked but came back supported.
    if case.expected_blocked and rule is InferenceRule.CAUSAL_CHAIN:
        return HeldoutFailureClass.GUARD_TOO_WEAK

    # Trap blocked but the wrong state value (e.g. expected
    # rejected, got bridge_required).
    if (
        case.expected_blocked
        and rule is not InferenceRule.CAUSAL_CHAIN
        and state != LogicalState(case.expected_final_state)
    ):
        return HeldoutFailureClass.BENCHMARK_LABEL_ERROR

    # Other mismatches (e.g. valid case supported but via a
    # different inference rule).
    if (
        not case.expected_blocked
        and rule is not None
        and rule is not InferenceRule.CAUSAL_CHAIN
    ):
        return HeldoutFailureClass.RULE_TOO_BROAD

    return HeldoutFailureClass.UNKNOWN


def _audit_once(
    case: HeldoutCase,
    auditor: LogicalAuditor,
) -> HeldoutOutcome:
    result = auditor.audit(case.text)
    actual_state = result.state
    actual_rule = result.rule

    expected_state = case.expected_final_state
    expected_rule = case.expected_rule

    correct = (actual_state == expected_state) and (
        (expected_rule is None and actual_rule is None)
        or (expected_rule is not None and actual_rule is expected_rule)
    )

    blocked_reason: str | None = None
    if actual_state == LogicalState.LOGICALLY_REJECTED:
        blocked_reason = (
            result.gap.kind.value if result.gap else "rejected"
        )
    elif actual_state == LogicalState.BRIDGE_REQUIRED:
        blocked_reason = "bridge_required"
    elif actual_state == LogicalState.GAP_DETECTED:
        blocked_reason = (
            result.gap.kind.value if result.gap else "gap"
        )

    replay_hash: str | None = None
    if result.proof_chain is not None:
        replay_hash = result.proof_chain.replay_hash

    depth_reached = len(result.propositions.premises)

    failure_class: HeldoutFailureClass | None = None
    if not correct:
        failure_class = _classify_failure(
            case, actual_state, actual_rule,
        )

    return HeldoutOutcome(
        case_id=case.case_id,
        category=case.category.value,
        text=case.text,
        expected_final_state=case.expected_final_state.value,
        expected_rule=(
            case.expected_rule.value if case.expected_rule else None
        ),
        expected_blocked=case.expected_blocked,
        trap_type=case.trap_type,
        actual_final_state=actual_state.value,
        actual_rule=actual_rule.value if actual_rule else None,
        blocked_reason=blocked_reason,
        replay_hash=replay_hash,
        matched_guard=_matched_guard(case),
        depth_reached=depth_reached,
        correct=correct,
        failure_class=failure_class,
    )


def run_heldout() -> tuple[HeldoutOutcome, ...]:
    """Walk every held-out case through the real LogicalAuditor.

    Two consecutive runs over the same auditor instance produce
    identical outcomes (no shared mutable state)."""
    auditor = LogicalAuditor()
    out: list[HeldoutOutcome] = []
    for case in ALL_HELDOUT_CASES:
        out.append(_audit_once(case, auditor))
    return tuple(out)


@dataclass(frozen=True)
class HeldoutMetrics:
    total: int
    valid_total: int
    trap_total: int
    correct_total: int
    accuracy: float
    heldout_precision: float
    heldout_recall: float
    false_positive_count: int
    false_negative_count: int
    guard_success_rate: float
    rule_generalization_rate: float
    trap_block_rate: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "valid_total": self.valid_total,
            "trap_total": self.trap_total,
            "correct_total": self.correct_total,
            "accuracy": self.accuracy,
            "heldout_precision": self.heldout_precision,
            "heldout_recall": self.heldout_recall,
            "false_positive_count": self.false_positive_count,
            "false_negative_count": self.false_negative_count,
            "guard_success_rate": self.guard_success_rate,
            "rule_generalization_rate": self.rule_generalization_rate,
            "trap_block_rate": self.trap_block_rate,
        }


def compute_metrics(
    outcomes: tuple[HeldoutOutcome, ...]
) -> HeldoutMetrics:
    total = len(outcomes)
    valid = [o for o in outcomes if not o.expected_blocked]
    traps = [o for o in outcomes if o.expected_blocked]
    correct = sum(1 for o in outcomes if o.correct)

    # Treat as a binary classifier where positive = "this is a
    # valid CAUSAL_CHAIN". Then:
    #   TP = valid case correctly labelled CAUSAL_CHAIN
    #   FP = trap labelled CAUSAL_CHAIN (manipulation succeeded)
    #   FN = valid case not labelled CAUSAL_CHAIN (under-coverage)
    tp = sum(
        1 for o in valid if o.actual_rule == "causal_chain"
    )
    fp = sum(
        1 for o in traps if o.actual_rule == "causal_chain"
    )
    fn = sum(
        1 for o in valid if o.actual_rule != "causal_chain"
    )
    precision = (
        round(tp / (tp + fp), 6) if (tp + fp) else 0.0
    )
    recall = (
        round(tp / (tp + fn), 6) if (tp + fn) else 0.0
    )

    # Guard success: trap cases blocked correctly / trap total.
    guard_success = sum(
        1 for o in traps if o.actual_rule != "causal_chain"
    )
    guard_rate = (
        round(guard_success / len(traps), 6) if traps else 0.0
    )

    # Rule generalisation: valid cases labelled CAUSAL_CHAIN /
    # valid total. Mirrors recall but kept separate for clarity.
    rule_gen = (
        round(tp / len(valid), 6) if valid else 0.0
    )

    # Trap block rate: every trap that was blocked (regardless of
    # which exact non-LOGICALLY_SUPPORTED state).
    blocked_traps = sum(
        1 for o in traps
        if o.actual_final_state != "logically_supported"
    )
    block_rate = (
        round(blocked_traps / len(traps), 6) if traps else 0.0
    )

    return HeldoutMetrics(
        total=total,
        valid_total=len(valid),
        trap_total=len(traps),
        correct_total=correct,
        accuracy=round(correct / total, 6) if total else 0.0,
        heldout_precision=precision,
        heldout_recall=recall,
        false_positive_count=fp,
        false_negative_count=fn,
        guard_success_rate=guard_rate,
        rule_generalization_rate=rule_gen,
        trap_block_rate=block_rate,
    )


__all__ = [
    "HeldoutFailureClass",
    "HeldoutMetrics",
    "HeldoutOutcome",
    "compute_metrics",
    "run_heldout",
]
