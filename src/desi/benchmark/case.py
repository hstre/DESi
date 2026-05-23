"""BenchmarkCase + enums — v1.5 real-world test scaffolding.

The benchmark deliberately does **not** add new operators,
heuristics, or rules to DESi. Each :class:`BenchmarkCase` records a
piece of natural-language input plus a *ground-truth* label that
states what an ideal epistemic engine should do with it. The
runner compares the v1.4 :class:`RecursiveResolver`'s actual
verdict against the ground truth and computes
``false_positive`` / ``false_negative`` flags.

The mission is honest measurement. Failures the benchmark exposes
are documented as findings, not silently patched.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..recursive import ResolutionState


class Category(str, Enum):
    """Five closed benchmark categories."""

    A_EVERYDAY_CAUSALITY = "A_everyday_causality"
    B_CLASSICAL_LOGIC = "B_classical_logic"
    C_AUTHORITY_TRAPS = "C_authority_traps"
    D_METAPHOR_AMBIGUITY = "D_metaphor_ambiguity"
    E_PHILOSOPHICAL_STRESS = "E_philosophical_stress"


class GroundTruth(str, Enum):
    """The ideal-epistemic-engine verdict for each case.

    * ``SHOULD_RESOLVE``   — a valid logical chain (gap-free under
      the v1.2 rule set). Expected final state:
      ``RESOLUTION_COMPLETE`` at depth 0 (rule directly matched).
    * ``SHOULD_BRIDGE``    — there is a hidden assumption between
      premise and conclusion that needs an explicit bridge. The
      v1.4 resolver may *propose* a bridge and recurse, but it
      should never silently accept it without surfacing the gap.
      We mark ``SHOULD_BRIDGE`` cases as ``false_positive`` when
      the system completes with depth>0 and zero adversarial
      pushback, because the bridge was synthesised by the system
      itself and accepted by its own consilium.
    * ``SHOULD_BLOCK``    — authority claim, metaphor without
      context, or a question. Expected: NOT ``RESOLUTION_COMPLETE``.
    * ``SHOULD_REJECT``   — explicitly invalid inference
      (e.g. invalid transitivity). Expected:
      ``RESOLUTION_BLOCKED``.
    """

    SHOULD_RESOLVE = "should_resolve"
    SHOULD_BRIDGE = "should_bridge"
    SHOULD_BLOCK = "should_block"
    SHOULD_REJECT = "should_reject"


@dataclass(frozen=True)
class BenchmarkCase:
    """One natural-language reasoning case + its ground truth."""

    case_id: str
    category: Category
    text: str
    ground_truth: GroundTruth
    # Optional adversarial conditions / discourse context the v1.3
    # consilium consumes — left empty for the v1.5 honest baseline.
    additional_conditions: tuple[str, ...] = field(default_factory=tuple)
    context: str = ""
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "category": self.category.value,
            "text": self.text,
            "ground_truth": self.ground_truth.value,
            "additional_conditions": list(self.additional_conditions),
            "context": self.context,
            "note": self.note,
        }


@dataclass(frozen=True)
class BenchmarkResult:
    """One case's measured outcome plus the comparison flags."""

    case: BenchmarkCase
    final_state: ResolutionState
    bridge_count: int
    recursion_depth: int
    veto_count: int
    replay_hash: str
    false_positive: bool
    false_negative: bool

    def to_dict(self) -> dict:
        return {
            "case": self.case.to_dict(),
            "final_state": self.final_state.value,
            "bridge_count": self.bridge_count,
            "recursion_depth": self.recursion_depth,
            "veto_count": self.veto_count,
            "replay_hash": self.replay_hash,
            "false_positive": self.false_positive,
            "false_negative": self.false_negative,
        }


def classify_outcome(
    case: BenchmarkCase,
    final_state: ResolutionState,
) -> tuple[bool, bool]:
    """Return (false_positive, false_negative) for a measured outcome.

    The classifier is deterministic and metadata-free.

    * SHOULD_RESOLVE → ``RESOLUTION_COMPLETE`` is correct;
                      anything else is a false_negative.
    * SHOULD_BRIDGE  → bridge proposed AND not silently completed is
                      ideal. ``RESOLUTION_COMPLETE`` here is a
                      false_positive (the system invented certainty
                      via its own bridge generator).
    * SHOULD_BLOCK   → ``RESOLUTION_COMPLETE`` is a false_positive;
                      anything else (BLOCKED / CYCLE / DEPTH) is
                      correct.
    * SHOULD_REJECT  → ``RESOLUTION_BLOCKED`` is correct;
                      ``RESOLUTION_COMPLETE`` is a false_positive;
                      ``RESOLUTION_CYCLE_DETECTED`` /
                      ``RESOLUTION_DEPTH_EXCEEDED`` are reported as
                      false_negatives because the system did not
                      issue the deliberate "this is invalid" call.
    """
    if case.ground_truth is GroundTruth.SHOULD_RESOLVE:
        return (False, final_state is not ResolutionState.RESOLUTION_COMPLETE)
    if case.ground_truth is GroundTruth.SHOULD_BRIDGE:
        # Completing silently is a false positive (invented certainty);
        # blocking is fine (the gap was visible).
        return (final_state is ResolutionState.RESOLUTION_COMPLETE, False)
    if case.ground_truth is GroundTruth.SHOULD_BLOCK:
        return (final_state is ResolutionState.RESOLUTION_COMPLETE, False)
    if case.ground_truth is GroundTruth.SHOULD_REJECT:
        if final_state is ResolutionState.RESOLUTION_BLOCKED:
            return (False, False)
        if final_state is ResolutionState.RESOLUTION_COMPLETE:
            return (True, False)
        return (False, True)
    raise ValueError(f"unknown ground truth: {case.ground_truth}")


__all__ = [
    "BenchmarkCase",
    "BenchmarkResult",
    "Category",
    "GroundTruth",
    "classify_outcome",
]
