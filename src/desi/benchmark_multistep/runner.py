"""MultiStepBenchmarkRunner — v2.3.

Runs the 30 hand-crafted cases through the **real** v1.9 evaluation
stack:

* :class:`LogicalAuditor`
* :class:`BridgeConsilium`
* :class:`RecursiveResolver`

No mocks. No patches. The runner only *observes*.

Captures per case:

* ``final_state``        — the resolver's verdict
* ``depth_reached``      — actual depth used
* ``replay_hash``        — deterministic encoding of the walk
* ``cycle_detected``     — whether the resolver flagged a cycle
* ``blocked``            — whether resolution ended in a BLOCKED state
* ``blocking_reason``    — concrete reason if blocked
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from ..consilium import BridgeConsilium
from ..logic import LogicalAuditor
from ..recursive import (
    BlockingReason,
    RecursiveResolver,
    ResolutionState,
)
from .case import MultiStepCase
from .cases import ALL_MULTISTEP_CASES


@dataclass(frozen=True)
class MultiStepResult:
    """One per-case observation of the real evaluation stack."""

    case: MultiStepCase
    final_state: ResolutionState
    depth_reached: int
    replay_hash: str
    cycle_detected: bool
    blocked: bool
    blocking_reason: BlockingReason | None
    expected_depth_met: bool
    expected_state_met: bool
    expected_cycle_met: bool
    expected_blocked_met: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "case": self.case.to_dict(),
            "final_state": self.final_state.value,
            "depth_reached": self.depth_reached,
            "replay_hash": self.replay_hash,
            "cycle_detected": self.cycle_detected,
            "blocked": self.blocked,
            "blocking_reason": (
                self.blocking_reason.value if self.blocking_reason
                else None
            ),
            "expected_depth_met": self.expected_depth_met,
            "expected_state_met": self.expected_state_met,
            "expected_cycle_met": self.expected_cycle_met,
            "expected_blocked_met": self.expected_blocked_met,
        }


@dataclass(frozen=True)
class MultiStepRun:
    timestamp: datetime
    results: tuple[MultiStepResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "results": [r.to_dict() for r in self.results],
        }


class MultiStepBenchmarkRunner:
    """Stateless runner over the 30 closed cases.

    The auditor + consilium injections exist for tests; the default
    factories build fresh real instances so no benchmark state can
    leak between cases.
    """

    def __init__(
        self,
        *,
        auditor: LogicalAuditor | None = None,
        consilium: BridgeConsilium | None = None,
        resolver: RecursiveResolver | None = None,
    ) -> None:
        self._auditor = auditor
        self._consilium = consilium
        self._resolver_override = resolver

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        cases: Iterable[MultiStepCase] | None = None,
    ) -> MultiStepRun:
        targets = tuple(cases) if cases is not None else ALL_MULTISTEP_CASES
        results: list[MultiStepResult] = []
        for case in targets:
            results.append(self._run_one(case))
        return MultiStepRun(
            timestamp=datetime.now(timezone.utc),
            results=tuple(results),
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_resolver(self) -> RecursiveResolver:
        if self._resolver_override is not None:
            return self._resolver_override
        # Fresh real components per case — same discipline as v1.5.
        return RecursiveResolver(
            auditor=self._auditor or LogicalAuditor(),
            consilium=self._consilium or BridgeConsilium(),
        )

    def _run_one(self, case: MultiStepCase) -> MultiStepResult:
        resolver = self._build_resolver()
        res = resolver.resolve(case.text)
        cycle_detected = (
            res.final_state is ResolutionState.RESOLUTION_CYCLE_DETECTED
        )
        blocked = (res.final_state is ResolutionState.RESOLUTION_BLOCKED
                   or cycle_detected)
        expected_depth_met = (res.depth_reached >= case.expected_min_depth)
        expected_state_met = (res.final_state is case.expected_final_state)
        # cycle expectation: case marks cycle → resolver must produce
        # either a CYCLE_DETECTED state or a BLOCKED-with-cycle path.
        expected_cycle_met = (case.expected_cycle == cycle_detected)
        expected_blocked_met = (case.expected_blocked == blocked)
        return MultiStepResult(
            case=case,
            final_state=res.final_state,
            depth_reached=res.depth_reached,
            replay_hash=res.replay_hash,
            cycle_detected=cycle_detected,
            blocked=blocked,
            blocking_reason=res.blocking_reason,
            expected_depth_met=expected_depth_met,
            expected_state_met=expected_state_met,
            expected_cycle_met=expected_cycle_met,
            expected_blocked_met=expected_blocked_met,
        )


__all__ = ["MultiStepBenchmarkRunner", "MultiStepResult", "MultiStepRun"]
