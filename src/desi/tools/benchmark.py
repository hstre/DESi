"""20-case mini-benchmark for the v1.9 tool layer.

Five categories × four cases. Ground truth labels mirror the
v1.5 main benchmark's discipline: each case carries a typed
expected outcome that grades the system honestly.

Categories (per directive):

* A — arithmetic
* B — symbolic math (sympy; v1.9 ships without sympy → fail-closed)
* C — counting
* D — date/time
* E — false tool temptation (tool MUST NOT fire)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from ..memory.claim import ClaimState
from .detector import ToolDetector
from .gate import ToolGate, ToolResult
from .impact import ToolUsageRegistry
from .proposal import ToolUseProposal


class ToolCategory(str, Enum):
    A_ARITHMETIC = "A_arithmetic"
    B_SYMBOLIC_MATH = "B_symbolic_math"
    C_COUNTING = "C_counting"
    D_DATE_TIME = "D_date_time"
    E_FALSE_TEMPTATION = "E_false_temptation"


class ToolGroundTruth(str, Enum):
    """How the case *should* end."""

    SHOULD_TOOL_SUPPORT = "should_tool_support"
    SHOULD_TOOL_FAIL = "should_tool_fail"
    SHOULD_NOT_DISPATCH = "should_not_dispatch"


@dataclass(frozen=True)
class ToolBenchmarkCase:
    case_id: str
    category: ToolCategory
    text: str
    ground_truth: ToolGroundTruth
    expected_value: str = ""        # for SHOULD_TOOL_SUPPORT cases
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id, "category": self.category.value,
            "text": self.text,
            "ground_truth": self.ground_truth.value,
            "expected_value": self.expected_value,
            "note": self.note,
        }


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------


_CAT_A: tuple[ToolBenchmarkCase, ...] = (
    ToolBenchmarkCase("TA1", ToolCategory.A_ARITHMETIC,
                       "What is 2 + 2?",
                       ToolGroundTruth.SHOULD_TOOL_SUPPORT,
                       expected_value="4",
                       note="Trivial sum; PYTHON_DECIMAL."),
    ToolBenchmarkCase("TA2", ToolCategory.A_ARITHMETIC,
                       "Compute 17 * 23",
                       ToolGroundTruth.SHOULD_TOOL_SUPPORT,
                       expected_value="391",
                       note="Multiplication; PYTHON_DECIMAL."),
    ToolBenchmarkCase("TA3", ToolCategory.A_ARITHMETIC,
                       "Calculate 100 / 4",
                       ToolGroundTruth.SHOULD_TOOL_SUPPORT,
                       expected_value="25",
                       note="Integer division as decimal."),
    ToolBenchmarkCase("TA4", ToolCategory.A_ARITHMETIC,
                       "Is 144 = 12 * 12?",
                       ToolGroundTruth.SHOULD_TOOL_SUPPORT,
                       expected_value="0",
                       note="Equality probe via subtraction; expect 0."),
)

_CAT_B: tuple[ToolBenchmarkCase, ...] = (
    ToolBenchmarkCase("TB1", ToolCategory.B_SYMBOLIC_MATH,
                       "Solve x^2 - 4 = 0 for x",
                       ToolGroundTruth.SHOULD_TOOL_FAIL,
                       note="sympy not installed → DEPENDENCY_MISSING."),
    ToolBenchmarkCase("TB2", ToolCategory.B_SYMBOLIC_MATH,
                       "Solve x + 1 = 5 for x",
                       ToolGroundTruth.SHOULD_TOOL_FAIL,
                       note="sympy not installed → DEPENDENCY_MISSING."),
    ToolBenchmarkCase("TB3", ToolCategory.B_SYMBOLIC_MATH,
                       "Solve 2*x = 8 for x",
                       ToolGroundTruth.SHOULD_TOOL_FAIL,
                       note="sympy not installed → DEPENDENCY_MISSING."),
    ToolBenchmarkCase("TB4", ToolCategory.B_SYMBOLIC_MATH,
                       "Solve x*x - 9 = 0 for x",
                       ToolGroundTruth.SHOULD_TOOL_FAIL,
                       note="sympy not installed → DEPENDENCY_MISSING."),
)

_CAT_C: tuple[ToolBenchmarkCase, ...] = (
    ToolBenchmarkCase("TC1", ToolCategory.C_COUNTING,
                       "How many vowels in 'mississippi'?",
                       ToolGroundTruth.SHOULD_TOOL_SUPPORT,
                       expected_value="4",
                       note="i-i-i-i = 4."),
    ToolBenchmarkCase("TC2", ToolCategory.C_COUNTING,
                       "How many s's in 'mississippi'?",
                       ToolGroundTruth.SHOULD_TOOL_SUPPORT,
                       expected_value="4",
                       note="s-s-s-s = 4."),
    ToolBenchmarkCase("TC3", ToolCategory.C_COUNTING,
                       "How many distinct letters in 'banana'?",
                       ToolGroundTruth.SHOULD_TOOL_SUPPORT,
                       expected_value="3",
                       note="b, a, n = 3."),
    ToolBenchmarkCase("TC4", ToolCategory.C_COUNTING,
                       "How many vowels in 'rhythm'?",
                       ToolGroundTruth.SHOULD_TOOL_SUPPORT,
                       expected_value="0",
                       note="No standard-set vowels."),
)

_CAT_D: tuple[ToolBenchmarkCase, ...] = (
    ToolBenchmarkCase("TD1", ToolCategory.D_DATE_TIME,
                       "How many days between 2020-01-01 and 2020-12-31?",
                       ToolGroundTruth.SHOULD_TOOL_SUPPORT,
                       expected_value="365",
                       note="2020 is a leap year."),
    ToolBenchmarkCase("TD2", ToolCategory.D_DATE_TIME,
                       "What weekday was 2024-07-04?",
                       ToolGroundTruth.SHOULD_TOOL_SUPPORT,
                       expected_value="Thursday",
                       note="US Independence Day 2024."),
    ToolBenchmarkCase("TD3", ToolCategory.D_DATE_TIME,
                       "Add 30 days to 2025-01-15",
                       ToolGroundTruth.SHOULD_TOOL_SUPPORT,
                       expected_value="2025-02-14",
                       note="Day-precision arithmetic."),
    ToolBenchmarkCase("TD4", ToolCategory.D_DATE_TIME,
                       "How many days between 2024-01-01 and 2024-01-31?",
                       ToolGroundTruth.SHOULD_TOOL_SUPPORT,
                       expected_value="30",
                       note="January 1 to January 31 = 30 day delta."),
)

_CAT_E: tuple[ToolBenchmarkCase, ...] = (
    ToolBenchmarkCase("TE1", ToolCategory.E_FALSE_TEMPTATION,
                       "Compute the consciousness of a rock.",
                       ToolGroundTruth.SHOULD_NOT_DISPATCH,
                       note="No numeric / structured input."),
    ToolBenchmarkCase("TE2", ToolCategory.E_FALSE_TEMPTATION,
                       "What is love + happiness?",
                       ToolGroundTruth.SHOULD_NOT_DISPATCH,
                       note="Has '+' but operands are not numeric."),
    ToolBenchmarkCase("TE3", ToolCategory.E_FALSE_TEMPTATION,
                       "Solve God for x",
                       ToolGroundTruth.SHOULD_NOT_DISPATCH,
                       note="No equation form; sympy detector requires '='."),
    ToolBenchmarkCase("TE4", ToolCategory.E_FALSE_TEMPTATION,
                       "How many truths in the universe?",
                       ToolGroundTruth.SHOULD_NOT_DISPATCH,
                       note="Counting form, but no quoted target."),
)


ALL_TOOL_CASES: tuple[ToolBenchmarkCase, ...] = (
    _CAT_A + _CAT_B + _CAT_C + _CAT_D + _CAT_E
)


def cases_by_category(cat: ToolCategory) -> tuple[ToolBenchmarkCase, ...]:
    return tuple(c for c in ALL_TOOL_CASES if c.category is cat)


# ---------------------------------------------------------------------------
# Result + runner
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ToolBenchmarkResult:
    case: ToolBenchmarkCase
    proposal: ToolUseProposal | None
    tool_result: ToolResult | None
    correct: bool
    rationale: str

    @property
    def dispatched(self) -> bool:
        return self.proposal is not None

    @property
    def succeeded(self) -> bool:
        return self.tool_result is not None and self.tool_result.succeeded

    def to_dict(self) -> dict[str, Any]:
        return {
            "case": self.case.to_dict(),
            "dispatched": self.dispatched,
            "succeeded": self.succeeded,
            "correct": self.correct,
            "proposal": (
                self.proposal.to_dict() if self.proposal else None
            ),
            "tool_result": (
                self.tool_result.to_dict() if self.tool_result else None
            ),
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class ToolBenchmarkRun:
    timestamp: datetime
    results: tuple[ToolBenchmarkResult, ...]
    registry: ToolUsageRegistry

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "results": [r.to_dict() for r in self.results],
            "registry_size": len(self.registry),
        }


def _grade(case: ToolBenchmarkCase,
            proposal: ToolUseProposal | None,
            tool_result: ToolResult | None) -> tuple[bool, str]:
    """Compare a measured outcome against the case's ground truth."""
    gt = case.ground_truth
    if gt is ToolGroundTruth.SHOULD_NOT_DISPATCH:
        ok = (proposal is None)
        return ok, ("no dispatch (expected)" if ok
                    else "tool dispatched on a non-computable input")
    if gt is ToolGroundTruth.SHOULD_TOOL_FAIL:
        ok = (tool_result is not None
              and tool_result.state is ClaimState.TOOL_FAILED)
        return ok, ("fail-closed (expected)" if ok
                    else "expected TOOL_FAILED")
    if gt is ToolGroundTruth.SHOULD_TOOL_SUPPORT:
        if tool_result is None or not tool_result.succeeded:
            return False, "expected TOOL_SUPPORTED"
        actual = str(tool_result.output.get("value", "")).strip()
        if case.expected_value and actual != case.expected_value:
            return False, (
                f"value mismatch: expected {case.expected_value!r}, "
                f"got {actual!r}"
            )
        return True, "tool result matches expected_value"
    return False, f"unknown ground_truth: {gt}"


class ToolBenchmarkRunner:
    """Run all 20 mini-benchmark cases through detector + gate."""

    def __init__(
        self,
        *,
        detector: ToolDetector | None = None,
        gate: ToolGate | None = None,
    ) -> None:
        self._detector = detector or ToolDetector()
        self._gate = gate or ToolGate()

    def run(self) -> ToolBenchmarkRun:
        registry = ToolUsageRegistry()
        results: list[ToolBenchmarkResult] = []
        for case in ALL_TOOL_CASES:
            proposal = self._detector.detect(case.text)
            tool_result: ToolResult | None = None
            if proposal is not None:
                tool_result = self._gate.execute(proposal)
                if tool_result.provenance is not None:
                    # Bind every successful execution to the case_id so
                    # ImpactScan / ContaminationPropagation can query.
                    registry.record(case.case_id, tool_result.provenance)
            ok, why = _grade(case, proposal, tool_result)
            results.append(ToolBenchmarkResult(
                case=case, proposal=proposal,
                tool_result=tool_result,
                correct=ok, rationale=why,
            ))
        return ToolBenchmarkRun(
            timestamp=datetime.now(timezone.utc),
            results=tuple(results),
            registry=registry,
        )


__all__ = [
    "ALL_TOOL_CASES",
    "ToolBenchmarkCase",
    "ToolBenchmarkResult",
    "ToolBenchmarkRun",
    "ToolBenchmarkRunner",
    "ToolCategory",
    "ToolGroundTruth",
    "cases_by_category",
]
