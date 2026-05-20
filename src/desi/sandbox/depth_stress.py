"""DepthStressSuite — Aufgabe 3.

Eight deterministic depth-stress cases.

* D1–D5: chains of nominal "depth" 1..5 that the v1.4 recursive
  resolver attempts to walk under the current ``max_depth``.
* D6:    a cycle graph — resolver should detect the cycle.
* D7:    a sibling graph — branching at the root.
* D8:    blocked-grandchild — authority block on the parent should
         propagate to its child.

Each case carries an ``expected_state`` that the suite grades
against. Grading is **purely deterministic** — same text + same
``max_depth`` → same ``final_state`` → same grade.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..recursive import RecursiveResolver, ResolutionState


@dataclass(frozen=True)
class DepthStressCase:
    """One stress case for the depth suite."""

    case_id: str
    label: str
    text: str
    expected_state: ResolutionState

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "label": self.label,
            "text": self.text,
            "expected_state": self.expected_state.value,
        }


# ---------------------------------------------------------------------------
# Eight closed cases (the directive lists D1..D8 exactly).
# ---------------------------------------------------------------------------


ALL_DEPTH_STRESS_CASES: tuple[DepthStressCase, ...] = (
    DepthStressCase(
        case_id="D1", label="depth_1_chain",
        text=(
            "All men are mortal. Socrates is a man. "
            "Therefore Socrates is mortal."
        ),
        expected_state=ResolutionState.RESOLUTION_COMPLETE,
    ),
    DepthStressCase(
        case_id="D2", label="depth_2_chain",
        text=(
            "All A are B. All B are C. "
            "Therefore all A are C."
        ),
        expected_state=ResolutionState.RESOLUTION_COMPLETE,
    ),
    DepthStressCase(
        case_id="D3", label="depth_3_chain",
        text=(
            "All A are B. All B are C. All C are D. "
            "Therefore all A are D."
        ),
        expected_state=ResolutionState.RESOLUTION_COMPLETE,
    ),
    DepthStressCase(
        case_id="D4", label="depth_4_chain",
        text=(
            "All A are B. All B are C. All C are D. All D are E. "
            "Therefore all A are E."
        ),
        expected_state=ResolutionState.RESOLUTION_COMPLETE,
    ),
    DepthStressCase(
        case_id="D5", label="depth_5_chain",
        text=(
            "All A are B. All B are C. All C are D. "
            "All D are E. All E are F. Therefore all A are F."
        ),
        expected_state=ResolutionState.RESOLUTION_COMPLETE,
    ),
    DepthStressCase(
        case_id="D6", label="cycle_graph",
        text=(
            "If P then Q. If Q then P. "
            "Therefore P."
        ),
        expected_state=ResolutionState.RESOLUTION_BLOCKED,
    ),
    DepthStressCase(
        case_id="D7", label="sibling_graph",
        text=(
            "All birds fly. All birds have feathers. "
            "Penguins are birds. Therefore penguins fly."
        ),
        expected_state=ResolutionState.RESOLUTION_BLOCKED,
    ),
    DepthStressCase(
        case_id="D8", label="blocked_grandchild",
        text=(
            "Professor X says all crows are black. "
            "All crows have feathers. "
            "Therefore something with feathers is black."
        ),
        expected_state=ResolutionState.RESOLUTION_BLOCKED,
    ),
)


@dataclass(frozen=True)
class DepthStressResult:
    case: DepthStressCase
    final_state: ResolutionState
    depth_reached: int
    correct: bool
    replay_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case.case_id,
            "label": self.case.label,
            "expected_state": self.case.expected_state.value,
            "final_state": self.final_state.value,
            "depth_reached": self.depth_reached,
            "correct": self.correct,
            "replay_hash": self.replay_hash,
        }


@dataclass(frozen=True)
class DepthStressRun:
    max_depth: int
    results: tuple[DepthStressResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_depth": self.max_depth,
            "results": [r.to_dict() for r in self.results],
        }


class DepthStressSuite:
    """Runs the eight closed cases against ``RecursiveResolver``."""

    def __init__(
        self,
        *,
        resolver_factory: Any = None,
    ) -> None:
        self._factory = resolver_factory or RecursiveResolver

    def run(self, *, max_depth: int) -> DepthStressRun:
        if max_depth < 1:
            raise ValueError("max_depth must be >= 1")
        resolver = self._factory()
        out: list[DepthStressResult] = []
        for case in ALL_DEPTH_STRESS_CASES:
            res = resolver.resolve(case.text, max_depth=max_depth)
            correct = (res.final_state is case.expected_state)
            out.append(DepthStressResult(
                case=case,
                final_state=res.final_state,
                depth_reached=res.depth_reached,
                correct=correct,
                replay_hash=res.replay_hash,
            ))
        return DepthStressRun(max_depth=max_depth, results=tuple(out))


__all__ = [
    "ALL_DEPTH_STRESS_CASES",
    "DepthStressCase",
    "DepthStressResult",
    "DepthStressRun",
    "DepthStressSuite",
]
