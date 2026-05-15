"""Tests for v2.1 actionability filter (Aufgabe 6).

A deficit is actionable iff:
  1. reproducible (deterministic detection)
  2. has at least one live knob
  3. benchmarkable
  4. not pure infrastructure

The detectors encode this discipline directly: e.g. TOOL_DEPENDENCY
is marked non-actionable because no live epistemic knob fixes a
missing OS package; DEAD_MUTATION_KNOB is marked actionable because
the dead knob itself is the lever.
"""
from __future__ import annotations

from desi.benchmark import Category
from desi.diagnostic import (
    CaseResolution,
    DeficitCategory,
    discover_dead_mutation_knob,
    discover_parser_coverage,
    discover_recursion_configuration,
    discover_tool_dependency,
)
from desi.recursive import BlockingReason, ResolutionState


def _stub_tool_run(*, failure_reasons):
    class _R:
        def __init__(self, fr):
            self.failure_reason = fr
            self.succeeded = (fr == "")
            self.state = None
            self.provenance = None
    class _Result:
        def __init__(self, case_id, fr):
            self.case = type("C", (), {"case_id": case_id})()
            self.tool_result = _R(fr)
            self.proposal = None
            self.correct = False
    class _Run:
        pass
    run = _Run()
    run.results = tuple(
        _Result(f"T{i}", fr) for i, fr in enumerate(failure_reasons, 1)
    )
    return run


def test_sympy_dependency_is_not_actionable() -> None:
    """The directive's example: sympy missing → NOT actionable for
    epistemic evolution."""
    run = _stub_tool_run(failure_reasons=[
        "dependency_missing", "dependency_missing",
    ])
    rec = discover_tool_dependency(run)
    assert rec is not None
    assert rec.is_actionable is False
    assert rec.candidate_knobs == ()


def test_dead_mutation_knob_is_actionable() -> None:
    """The directive's example: dead mutation knob → actionable."""
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
    assert rec.is_actionable is True
    assert len(rec.candidate_knobs) >= 1


def test_recursion_configuration_is_actionable() -> None:
    """A live knob (max_depth) exists for this deficit."""
    resolutions = tuple(
        CaseResolution(
            case_id=f"c{i}", category=Category.A_EVERYDAY_CAUSALITY,
            final_state=ResolutionState.RESOLUTION_COMPLETE,
            blocking_reason=None, depth_reached=0,
        ) for i in range(3)
    )
    rec = discover_recursion_configuration(resolutions)
    assert rec is not None
    assert rec.is_actionable is True
    assert rec.candidate_knobs == ("RecursiveResolver.max_depth",)


def test_parser_coverage_is_not_actionable() -> None:
    """Parser changes are out of scope for the v2.1 knob universe."""
    resolutions = (
        CaseResolution(
            case_id="c1", category=Category.A_EVERYDAY_CAUSALITY,
            final_state=ResolutionState.RESOLUTION_BLOCKED,
            blocking_reason=BlockingReason.PARSER_UNSUPPORTED_FORM,
            depth_reached=0,
        ),
    )
    rec = discover_parser_coverage(resolutions)
    assert rec is not None
    assert rec.is_actionable is False
    assert rec.candidate_knobs == ()


def test_actionable_implies_at_least_one_candidate_knob() -> None:
    """Hard rule: actionable AND empty candidate_knobs is forbidden."""
    steps = [
        {"step_id": i, "parameter": "branch_open_evidence_min",
         "precision": 1.0, "recall": 1.0, "false_positives": 0,
         "authority_blocks": 10, "tool_precision": 1.0,
         "hash_mismatches": 0}
        for i in range(1, 4)
    ]
    rep = {"total_steps": 3, "accepted_steps": 3, "steps": steps}
    rec = discover_dead_mutation_knob(rep)
    assert rec.is_actionable is True
    assert len(rec.candidate_knobs) >= 1
