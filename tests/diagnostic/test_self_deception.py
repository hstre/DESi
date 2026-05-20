"""Tests for v2.1 self-deception guard (Aufgabe 8).

When a deficit is detected by the same mechanism it describes —
e.g. the benchmark uncovering its own coverage gaps — the deficit
is flagged ``self_reference=True`` and its confidence is halved.
"""
from __future__ import annotations

from desi.benchmark import Category
from desi.diagnostic import (
    CaseResolution,
    confidence_score,
    discover_dead_mutation_knob,
    discover_parser_coverage,
    discover_recursion_configuration,
)
from desi.recursive import BlockingReason, ResolutionState


def test_parser_coverage_is_self_referential() -> None:
    """Benchmark detects benchmark coverage gap → self_reference=True."""
    res = (CaseResolution(
        case_id="c1", category=Category.A_EVERYDAY_CAUSALITY,
        final_state=ResolutionState.RESOLUTION_BLOCKED,
        blocking_reason=BlockingReason.PARSER_UNSUPPORTED_FORM,
        depth_reached=0,
    ),)
    rec = discover_parser_coverage(res)
    assert rec is not None
    assert rec.self_reference is True


def test_recursion_configuration_is_self_referential() -> None:
    res = (CaseResolution(
        case_id="c1", category=Category.A_EVERYDAY_CAUSALITY,
        final_state=ResolutionState.RESOLUTION_COMPLETE,
        blocking_reason=None, depth_reached=0,
    ),)
    rec = discover_recursion_configuration(res)
    assert rec is not None
    assert rec.self_reference is True


def test_dead_mutation_knob_is_not_self_referential() -> None:
    """Sandbox + gate observables are independent of the deficit
    being described — no self-reference."""
    steps = [
        {"step_id": i, "parameter": "branch_open_evidence_min",
         "precision": 1.0, "recall": 1.0, "false_positives": 0,
         "authority_blocks": 10, "tool_precision": 1.0,
         "hash_mismatches": 0}
        for i in range(1, 4)
    ]
    rep = {"total_steps": 3, "accepted_steps": 3, "steps": steps}
    rec = discover_dead_mutation_knob(rep)
    assert rec is not None
    assert rec.self_reference is False


def test_self_reference_actually_halves_confidence() -> None:
    """Compare a self-referential vs non-self-referential deficit
    that are otherwise identical in their evidence axes."""
    c_no = confidence_score(
        frequency=5, reproducibility=1.0, cross_source_consistency=1.0,
        self_reference=False,
    )
    c_yes = confidence_score(
        frequency=5, reproducibility=1.0, cross_source_consistency=1.0,
        self_reference=True,
    )
    assert c_yes == round(c_no * 0.5, 6)
    assert c_yes < c_no


def test_self_referential_deficit_records_lower_confidence_than_non() -> None:
    """The detectors must apply the guard automatically."""
    # parser-coverage (self_ref=True) on one case
    parser_res = (CaseResolution(
        case_id="c1", category=Category.A_EVERYDAY_CAUSALITY,
        final_state=ResolutionState.RESOLUTION_BLOCKED,
        blocking_reason=BlockingReason.PARSER_UNSUPPORTED_FORM,
        depth_reached=0,
    ),)
    parser_rec = discover_parser_coverage(parser_res)
    # dead-knob (self_ref=False)
    steps = [
        {"step_id": i, "parameter": "branch_open_evidence_min",
         "precision": 1.0, "recall": 1.0, "false_positives": 0,
         "authority_blocks": 10, "tool_precision": 1.0,
         "hash_mismatches": 0}
        for i in range(1, 4)
    ]
    dead_rec = discover_dead_mutation_knob(
        {"total_steps": 3, "accepted_steps": 3, "steps": steps},
    )
    # Both have frequency >= 1 and reproducibility 1.0; the only
    # axis that differs is self_reference. dead_rec should have
    # strictly higher confidence.
    assert dead_rec.confidence_score > parser_rec.confidence_score
