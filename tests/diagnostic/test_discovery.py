"""Tests for v2.1 deficit discovery (Aufgabe 5)."""
from __future__ import annotations

from desi.benchmark import Category
from desi.diagnostic import (
    CaseResolution,
    DeficitCategory,
    discover_authority_coverage,
    discover_counterexample_coverage,
    discover_dead_mutation_knob,
    discover_false_block_reason,
    discover_parser_coverage,
    discover_recursion_configuration,
)
from desi.recursive import BlockingReason, ResolutionState


def _res(case_id, category, state, reason=None, depth=0):
    return CaseResolution(
        case_id=case_id, category=category, final_state=state,
        blocking_reason=reason, depth_reached=depth,
    )


# ---------------------------------------------------------------------------
# Parser coverage
# ---------------------------------------------------------------------------


def test_parser_coverage_fires_when_blocked() -> None:
    resolutions = (
        _res("c1", Category.A_EVERYDAY_CAUSALITY,
             ResolutionState.RESOLUTION_BLOCKED,
             BlockingReason.PARSER_UNSUPPORTED_FORM),
        _res("c2", Category.A_EVERYDAY_CAUSALITY,
             ResolutionState.RESOLUTION_COMPLETE),
    )
    rec = discover_parser_coverage(resolutions)
    assert rec is not None
    assert rec.category is DeficitCategory.PARSER_COVERAGE
    assert rec.frequency == 1
    assert rec.is_actionable is False


def test_parser_coverage_silent_when_clean() -> None:
    resolutions = (
        _res("c1", Category.A_EVERYDAY_CAUSALITY,
             ResolutionState.RESOLUTION_COMPLETE),
    )
    assert discover_parser_coverage(resolutions) is None


# ---------------------------------------------------------------------------
# Counterexample coverage
# ---------------------------------------------------------------------------


def test_counterexample_coverage_fires_when_blocked() -> None:
    resolutions = (
        _res("c1", Category.A_EVERYDAY_CAUSALITY,
             ResolutionState.RESOLUTION_BLOCKED,
             BlockingReason.COUNTEREXAMPLE_FOUND),
    )
    rec = discover_counterexample_coverage(resolutions)
    assert rec is not None
    assert rec.category is DeficitCategory.COUNTEREXAMPLE_COVERAGE


# ---------------------------------------------------------------------------
# Authority coverage (uses LOGICAL_RULE_COVERAGE category)
# ---------------------------------------------------------------------------


def test_authority_coverage_silent_when_all_cat_c_correct() -> None:
    resolutions = tuple(
        _res(f"C{i}", Category.C_AUTHORITY_TRAPS,
             ResolutionState.RESOLUTION_BLOCKED,
             BlockingReason.AUTHORITY_CLAIM)
        for i in range(1, 11)
    )
    assert discover_authority_coverage(resolutions) is None


def test_authority_coverage_fires_when_missing() -> None:
    """If even one Cat-C case is not AUTHORITY_CLAIM-blocked, fire."""
    resolutions = (
        _res("C1", Category.C_AUTHORITY_TRAPS,
             ResolutionState.RESOLUTION_BLOCKED,
             BlockingReason.AUTHORITY_CLAIM),
        _res("C2", Category.C_AUTHORITY_TRAPS,
             ResolutionState.RESOLUTION_COMPLETE),
    )
    rec = discover_authority_coverage(resolutions)
    assert rec is not None
    assert rec.frequency == 1


# ---------------------------------------------------------------------------
# False block reason
# ---------------------------------------------------------------------------


def test_false_block_reason_fires_on_silent_block() -> None:
    """BLOCKED state with no blocking_reason = silent block."""
    resolutions = (
        _res("c1", Category.A_EVERYDAY_CAUSALITY,
             ResolutionState.RESOLUTION_BLOCKED, None),
    )
    rec = discover_false_block_reason(resolutions)
    assert rec is not None
    assert rec.category is DeficitCategory.FALSE_BLOCK_REASON


def test_false_block_reason_silent_when_reason_attached() -> None:
    resolutions = (
        _res("c1", Category.A_EVERYDAY_CAUSALITY,
             ResolutionState.RESOLUTION_BLOCKED,
             BlockingReason.PARSER_UNSUPPORTED_FORM),
    )
    assert discover_false_block_reason(resolutions) is None


# ---------------------------------------------------------------------------
# Recursion configuration
# ---------------------------------------------------------------------------


def test_recursion_configuration_fires_when_depth_never_binds() -> None:
    resolutions = tuple(
        _res(f"c{i}", Category.A_EVERYDAY_CAUSALITY,
             ResolutionState.RESOLUTION_COMPLETE, depth=0)
        for i in range(5)
    )
    rec = discover_recursion_configuration(resolutions)
    assert rec is not None
    assert rec.is_actionable is True
    assert "RecursiveResolver.max_depth" in rec.candidate_knobs


def test_recursion_configuration_silent_when_depth_binds() -> None:
    resolutions = (
        _res("c1", Category.A_EVERYDAY_CAUSALITY,
             ResolutionState.RESOLUTION_COMPLETE, depth=2),
    )
    assert discover_recursion_configuration(resolutions) is None


# ---------------------------------------------------------------------------
# Dead mutation knob — from sandbox report
# ---------------------------------------------------------------------------


_STABLE_STEPS = [
    {"step_id": i, "parameter": "branch_open_evidence_min",
     "precision": 1.0, "recall": 1.0, "false_positives": 0,
     "authority_blocks": 10, "tool_precision": 1.0,
     "hash_mismatches": 0}
    for i in range(1, 6)
]


def test_dead_mutation_knob_fires_when_all_accepted_zero_variance() -> None:
    rep = {
        "total_steps": 5, "accepted_steps": 5,
        "steps": _STABLE_STEPS,
    }
    rec = discover_dead_mutation_knob(rep)
    assert rec is not None
    assert rec.category is DeficitCategory.DEAD_MUTATION_KNOB
    assert rec.candidate_knobs == ("branch_open_evidence_min",)
    assert rec.is_actionable is True
    assert rec.severity_score == 1.0


def test_dead_mutation_knob_silent_when_some_rejected() -> None:
    rep = {"total_steps": 5, "accepted_steps": 4, "steps": _STABLE_STEPS}
    assert discover_dead_mutation_knob(rep) is None


def test_dead_mutation_knob_silent_when_metrics_move() -> None:
    moving_steps = [
        {**step, "precision": 0.99 if i == 2 else 1.0}
        for i, step in enumerate(_STABLE_STEPS, start=1)
    ]
    rep = {"total_steps": 5, "accepted_steps": 5, "steps": moving_steps}
    assert discover_dead_mutation_knob(rep) is None


def test_dead_mutation_knob_silent_when_no_sandbox_report() -> None:
    assert discover_dead_mutation_knob(None) is None
