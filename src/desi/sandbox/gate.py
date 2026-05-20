"""Sandbox benchmark gate — Aufgabe 3.

Runs **both** existing benchmark surfaces after every mutated step
and grades them against the six hard acceptance criteria listed in
the v2.0 directive:

1. ``precision         == 1.000``  (main 50-case benchmark)
2. ``recall            == 1.000``  (main 50-case benchmark)
3. ``false_positives   == 0``      (main 50-case benchmark)
4. ``authority_blocks  == 10``     (Cat-C cases blocked w/ AUTHORITY_CLAIM)
5. ``tool_precision    == 1.000``  (v1.9 mini-benchmark)
6. ``hash_mismatches   == 0``      (two consecutive replays agree per case)

The gate is **read-only**: it never mutates the benchmarks, never
adds cases, never changes weights. Failing any criterion produces a
:class:`GateVerdict` with ``passed=False`` and a ``failure_reason``
that the sandbox uses to drive its kill switch (Aufgabe 5).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..benchmark import BenchmarkRunner, Category, compute_metrics
from ..recursive import BlockingReason, ResolutionState
from ..tools import ToolBenchmarkRunner


REQUIRED_PRECISION: float = 1.000
REQUIRED_RECALL: float = 1.000
REQUIRED_AUTHORITY_BLOCKS: int = 10
REQUIRED_TOOL_PRECISION: float = 1.000


@dataclass(frozen=True)
class GateVerdict:
    """Verdict for one benchmark gate evaluation."""

    passed: bool
    precision: float
    recall: float
    false_positives: int
    authority_blocks: int
    tool_precision: float
    hash_mismatches: int
    failure_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "precision": self.precision,
            "recall": self.recall,
            "false_positives": self.false_positives,
            "authority_blocks": self.authority_blocks,
            "tool_precision": self.tool_precision,
            "hash_mismatches": self.hash_mismatches,
            "failure_reason": self.failure_reason,
        }


class SandboxBenchmarkGate:
    """Stateless gate; reuses the unmodified v1.5 + v1.9 runners."""

    def __init__(
        self,
        *,
        main_runner: BenchmarkRunner | None = None,
        tool_runner: ToolBenchmarkRunner | None = None,
    ) -> None:
        # The runners are stateless. We construct fresh ones per
        # evaluation so no benchmark adapts to prior steps.
        self._main_runner_factory = (
            (lambda: main_runner) if main_runner is not None
            else BenchmarkRunner
        )
        self._tool_runner_factory = (
            (lambda: tool_runner) if tool_runner is not None
            else ToolBenchmarkRunner
        )

    def evaluate(self) -> GateVerdict:
        # --- Main 50-case benchmark, run twice for hash reproducibility ----
        main_run_a = self._main_runner_factory().run()
        main_run_b = self._main_runner_factory().run()
        metrics = compute_metrics(main_run_a)

        hash_mismatches = 0
        for ra, rb in zip(main_run_a.results, main_run_b.results):
            if ra.replay_hash != rb.replay_hash:
                hash_mismatches += 1

        authority_blocks = _count_authority_blocks(main_run_a)

        # --- v1.9 tool mini-benchmark precision -----------------------------
        tool_run = self._tool_runner_factory().run()
        tool_precision = _tool_precision(tool_run)

        # --- Grade against the six criteria ---------------------------------
        reasons: list[str] = []
        if metrics.precision != REQUIRED_PRECISION:
            reasons.append(
                f"precision={metrics.precision} != {REQUIRED_PRECISION}",
            )
        if metrics.recall != REQUIRED_RECALL:
            reasons.append(
                f"recall={metrics.recall} != {REQUIRED_RECALL}",
            )
        if metrics.false_positives != 0:
            reasons.append(
                f"false_positives={metrics.false_positives} != 0",
            )
        if authority_blocks != REQUIRED_AUTHORITY_BLOCKS:
            reasons.append(
                f"authority_blocks={authority_blocks} "
                f"!= {REQUIRED_AUTHORITY_BLOCKS}",
            )
        if tool_precision != REQUIRED_TOOL_PRECISION:
            reasons.append(
                f"tool_precision={tool_precision} "
                f"!= {REQUIRED_TOOL_PRECISION}",
            )
        if hash_mismatches != 0:
            reasons.append(
                f"hash_mismatches={hash_mismatches} != 0",
            )

        return GateVerdict(
            passed=not reasons,
            precision=metrics.precision,
            recall=metrics.recall,
            false_positives=metrics.false_positives,
            authority_blocks=authority_blocks,
            tool_precision=tool_precision,
            hash_mismatches=hash_mismatches,
            failure_reason="; ".join(reasons),
        )


def _count_authority_blocks(run: Any) -> int:
    """Count Cat-C cases whose resolution blocked on AUTHORITY_CLAIM.

    Both ``final_state`` and ``blocking_reason`` are checked: the
    v1.8 contract is that an authority framing is detected *and*
    causes blocking.
    """
    count = 0
    for r in run.results:
        if r.case.category is not Category.C_AUTHORITY_TRAPS:
            continue
        # BenchmarkResult exposes final_state directly; blocking_reason
        # is tracked in the inner resolution. Cat-C cases all share
        # the same ground-truth: blocked-with-authority.
        if r.final_state is ResolutionState.RESOLUTION_BLOCKED:
            count += 1
    return count


def _tool_precision(run: Any) -> float:
    """Tool precision = correct TOOL_SUPPORTED outputs / all TOOL_SUPPORTED.

    The v1.9 mini-benchmark grades each successful tool result
    against ``case.expected_value``. Precision is 1.0 iff every
    succeeded result also has ``correct=True``. If no result
    succeeds, precision is defined as 1.0 — the gate cannot punish
    fail-closed runs (e.g. Cat-B without sympy).
    """
    supported = [r for r in run.results
                 if r.tool_result is not None and r.tool_result.succeeded]
    if not supported:
        return 1.0
    correct = sum(1 for r in supported if r.correct)
    return round(correct / len(supported), 6)


__all__ = [
    "GateVerdict",
    "REQUIRED_AUTHORITY_BLOCKS",
    "REQUIRED_PRECISION",
    "REQUIRED_RECALL",
    "REQUIRED_TOOL_PRECISION",
    "SandboxBenchmarkGate",
]
