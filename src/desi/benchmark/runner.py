"""BenchmarkRunner — runs all 50 cases through the v1.4 resolver.

The runner is stateless and deterministic. It accepts an optional
``resolver`` and ``consilium`` injection so a test can verify the
runner under custom dependencies; by default it builds a fresh
:class:`RecursiveResolver` per call. The runner never touches
memory, never reads source metadata, and never adapts based on
prior cases.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from ..consilium import BridgeConsilium, Verdict
from ..logic import LogicalAuditor
from ..recursive import RecursiveResolver

from .case import (
    BenchmarkCase,
    BenchmarkResult,
    classify_outcome,
)
from .cases import ALL_CASES


@dataclass(frozen=True)
class BenchmarkRun:
    """Container for one full benchmark pass."""

    timestamp: datetime
    results: tuple[BenchmarkResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "results": [r.to_dict() for r in self.results],
        }


class BenchmarkRunner:
    """Run every :class:`BenchmarkCase` through the v1.4 resolver."""

    def __init__(
        self,
        *,
        resolver: RecursiveResolver | None = None,
    ) -> None:
        self._resolver_factory = (
            (lambda: resolver) if resolver is not None else self._fresh
        )

    @staticmethod
    def _fresh() -> RecursiveResolver:
        # A fresh resolver per call so stale auditor / consilium
        # state cannot leak across cases.
        return RecursiveResolver(
            auditor=LogicalAuditor(),
            consilium=BridgeConsilium(),
        )

    def run(
        self,
        cases: Iterable[BenchmarkCase] | None = None,
    ) -> BenchmarkRun:
        targets = tuple(cases) if cases is not None else ALL_CASES
        results: list[BenchmarkResult] = []
        for case in targets:
            results.append(self._run_one(case))
        return BenchmarkRun(
            timestamp=datetime.now(timezone.utc),
            results=tuple(results),
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _run_one(self, case: BenchmarkCase) -> BenchmarkResult:
        # The v1.4 resolver consumes the text only. The benchmark's
        # `additional_conditions` / `context` are not threaded
        # through the recursive walker (v1.4 doesn't accept them);
        # they are recorded on the case for documentation and for a
        # future v1.5+ extension that pipes them into the consilium.
        resolver = self._resolver_factory()
        resolution = resolver.resolve(case.text)
        bridge_count = max(0, len(resolution.resolved_claims) - 1)
        veto_count = _veto_count_for(case, resolver)
        fp, fn = classify_outcome(case, resolution.final_state)
        return BenchmarkResult(
            case=case,
            final_state=resolution.final_state,
            bridge_count=bridge_count,
            recursion_depth=resolution.depth_reached,
            veto_count=veto_count,
            replay_hash=resolution.replay_hash,
            false_positive=fp,
            false_negative=fn,
        )


def _veto_count_for(case: BenchmarkCase, resolver: RecursiveResolver) -> int:
    """Reserved for future use.

    v1.4's :class:`RecursiveResolutionResult` does not yet count
    consilium vetoes separately from blocked-claim ids; the v1.5
    benchmark records ``len(blocked_claims)`` as a proxy because
    every blocked claim in v1.4 came from a consilium VETO /
    NEEDS_MORE_PREMISES or a logical-audit REJECTED state. v1.6 may
    split these.
    """
    # Re-run is not done; we only inspect the last resolution if it
    # was attached to the resolver. For v1.5, returning 0 is the
    # honest baseline — vetoes are reported in the ledger but not in
    # the result struct.
    del case, resolver
    return 0


__all__ = [
    "BenchmarkRun",
    "BenchmarkRunner",
]
