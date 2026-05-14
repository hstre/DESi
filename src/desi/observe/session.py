"""ObservationSession — wraps a MemoryHook and emits a deterministic timeline.

Construct with a recorder; pass ``session.hook`` to
:func:`desi.runner.run_desi`. Each lifecycle callback the hook
receives also produces one or more :class:`TimelineEvent` records on
the session.

Determinism contract: identical input + identical seed produce
identical timelines (same number of events, same order, same payloads
modulo the ``ts`` metadata field which is excluded from equality).
"""
from __future__ import annotations

from typing import Any

from ..memory.claim import ClaimState
from ..memory.hook import MemoryHook
from ..memory.recorder import MemoryRecorder
from ..memory.relations import RelationType
from ..memory.store import MemoryStore
from .snapshot import GraphSnapshot, snapshot_store
from .timeline import EventType, TimelineEvent


class ObservationSession:
    """Live observation tap that wraps a :class:`MemoryHook`.

    Operators never see the session; only the runner does, via the
    ``session.hook`` attribute. The session collects events into an
    in-memory list ordered by a monotonic ``tick`` counter.
    """

    def __init__(
        self,
        recorder: MemoryRecorder,
        *,
        model: str = "unknown",
        seed: int = 0,
        config: dict[str, Any] | None = None,
        prompt_hash: str | None = None,
        strict: bool = False,
    ) -> None:
        self._recorder = recorder
        self.seed = int(seed)
        self.events: list[TimelineEvent] = []
        self.snapshots: list[GraphSnapshot] = []
        self._tick = 0
        self._open_branches: dict[str, int] = {}  # focus_claim_id -> open tick
        self._known_claims: set[str] = set()
        self._previous_focus: str | None = None
        self._hook = _SessionHook(
            recorder=recorder,
            session=self,
            model=model,
            strict=strict,
            config=config,
            prompt_hash=prompt_hash,
        )

    # ------------------------------------------------------------------
    # Public surface
    # ------------------------------------------------------------------

    @property
    def hook(self) -> MemoryHook:
        """Pass this to :func:`desi.runner.run_desi`."""
        return self._hook

    @property
    def store(self) -> MemoryStore:
        """The underlying store (read-only intent; useful for snapshotting)."""
        return self._recorder._store  # noqa: SLF001 — intentional access

    def timeline(self) -> list[TimelineEvent]:
        return list(self.events)

    def take_snapshot(self, label: str) -> GraphSnapshot:
        snap = snapshot_store(self.store, label=label, tick=self._tick)
        self.snapshots.append(snap)
        return snap

    # ------------------------------------------------------------------
    # Internals — used by the wrapped hook
    # ------------------------------------------------------------------

    def _next_tick(self) -> int:
        t = self._tick
        self._tick += 1
        return t

    def _emit(self, event_type: EventType, payload: dict[str, Any]) -> TimelineEvent:
        ev = TimelineEvent(tick=self._next_tick(),
                           event_type=event_type,
                           payload=dict(payload))
        self.events.append(ev)
        return ev


class _SessionHook(MemoryHook):
    """MemoryHook subclass that emits a TimelineEvent per recorder call.

    Inherits the v0.3 contract (write-only, error-isolated, optional
    strict mode). The session-emission step itself is wrapped so that
    a failing emit cannot break the run.
    """

    def __init__(self, *, session: ObservationSession, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._session = session

    # ------------------------------------------------------------------
    # Override every public hook method
    # ------------------------------------------------------------------

    def on_run_start(self, trajectory) -> None:  # type: ignore[override]
        super().on_run_start(trajectory)
        self._session._emit(EventType.RUN_STARTED, {
            "trajectory_id": getattr(trajectory, "trajectory_id", None),
            "n_steps": len(getattr(trajectory, "steps", []) or []),
            "seed": self._session.seed,
        })
        # Snapshot at start.
        self._session.take_snapshot("start")
        # Surface any captured hook errors as timeline events.
        self._drain_recent_errors()

    def on_step(self, step) -> None:  # type: ignore[override]
        op = str(step.operator)
        loop = int(step.loop_index)
        focus = step.focus_claim_id
        # Operator started.
        self._session._emit(EventType.OPERATOR_STARTED, {
            "operator": op,
            "loop_index": loop,
            "focus_claim_id": focus,
        })
        # Underlying recorder writes.
        super().on_step(step)
        self._drain_recent_errors()
        # Claim creation event (the hook only records new ones).
        if focus and focus not in self._session._known_claims:
            self._session._known_claims.add(focus)
            self._session._emit(EventType.CLAIM_CREATED, {
                "claim_id": focus,
                "method": op,
                "loop_index": loop,
                "state": ClaimState.PROPOSED.value,
            })
            # v0.7: the first behaviour-effective config knob. The
            # branch-opening decision now consults
            # guard_thresholds.branch_open_evidence_min. When config
            # carries no such knob (v0.6 and earlier callers), the
            # threshold defaults to 0.0 — every focus opens a branch,
            # bit-identical to v0.6.
            threshold = self._read_branch_threshold()
            evidence = self._compute_branch_evidence(loop)
            if evidence >= threshold:
                self._session._open_branches[focus] = self._session._tick
                self._session._emit(EventType.BRANCH_OPENED, {
                    "branch_id": f"branch_{focus}",
                    "focus_claim_id": focus,
                    "loop_index": loop,
                    "evidence": evidence,
                    "threshold": threshold,
                })
                self._session.take_snapshot(f"after_branch_open_{focus}")
            else:
                self._session._emit(EventType.GUARD_BLOCKED, {
                    "operator": "branch_open_guard",
                    "loop_index": loop,
                    "focus_claim_id": focus,
                    "evidence": evidence,
                    "threshold": threshold,
                    "reason": (
                        f"branch suppressed: evidence={evidence:.2f} "
                        f"< threshold={threshold:.2f}"
                    ),
                })
        # Focus-shift → DERIVES_FROM relation event.
        if (focus and self._session._previous_focus
                and focus != self._session._previous_focus):
            self._session._emit(EventType.RELATION_CREATED, {
                "source": focus,
                "target": self._session._previous_focus,
                "rel_type": RelationType.DERIVES_FROM.value,
                "loop_index": loop,
            })
            # Close the prior branch — it lost focus.
            prev = self._session._previous_focus
            if prev in self._session._open_branches:
                del self._session._open_branches[prev]
                self._session._emit(EventType.BRANCH_CLOSED, {
                    "branch_id": f"branch_{prev}",
                    "focus_claim_id": prev,
                    "loop_index": loop,
                })
        # Operator ended (always after the inner work).
        self._session._emit(EventType.OPERATOR_ENDED, {
            "operator": op,
            "loop_index": loop,
            "focus_claim_id": focus,
        })
        if focus:
            self._session._previous_focus = focus

    def on_run_end(self, report) -> None:  # type: ignore[override]
        # Close any still-open branches before sealing the run.
        for focus in list(self._session._open_branches.keys()):
            self._session._emit(EventType.BRANCH_CLOSED, {
                "branch_id": f"branch_{focus}",
                "focus_claim_id": focus,
                "reason": "run_end",
            })
        self._session._open_branches.clear()
        super().on_run_end(report)
        self._drain_recent_errors()
        self._session._emit(EventType.RUN_ENDED, {
            "report_type": type(report).__name__,
            "trajectory_id": getattr(report, "trajectory_id", None),
        })
        self._session.take_snapshot("end")

    # ------------------------------------------------------------------
    # Custom emitters that operators / scenarios may invoke explicitly
    # ------------------------------------------------------------------

    def emit_guard_passed(self, *, operator: str, loop_index: int,
                          guard_result: str = "passed") -> None:
        self._session._emit(EventType.GUARD_PASSED, {
            "operator": operator,
            "loop_index": loop_index,
            "guard_result": guard_result,
        })

    def emit_guard_blocked(self, *, operator: str, loop_index: int,
                           guard_result: str = "blocked",
                           reason: str = "") -> None:
        self._session._emit(EventType.GUARD_BLOCKED, {
            "operator": operator,
            "loop_index": loop_index,
            "guard_result": guard_result,
            "reason": reason,
        })

    def emit_claim_revised(self, *, claim_id: str, version: int) -> None:
        self._session._emit(EventType.CLAIM_REVISED, {
            "claim_id": claim_id,
            "version": version,
        })

    def emit_claim_rejected(self, *, claim_id: str, reason: str = "") -> None:
        self._session._emit(EventType.CLAIM_REJECTED, {
            "claim_id": claim_id,
            "reason": reason,
        })

    def emit_relation(
        self,
        *,
        source: str,
        target: str,
        rel_type: RelationType,
        loop_index: int | None = None,
    ) -> None:
        self._session._emit(EventType.RELATION_CREATED, {
            "source": source,
            "target": target,
            "rel_type": rel_type.value,
            "loop_index": loop_index,
        })

    def emit_branch_merged(
        self,
        *,
        source_branches: list[str],
        target_branch: str,
    ) -> None:
        self._session._emit(EventType.BRANCH_MERGED, {
            "source_branches": list(source_branches),
            "target_branch": target_branch,
        })

    # ------------------------------------------------------------------
    # v0.7: branch-evidence gate
    # ------------------------------------------------------------------

    def _read_branch_threshold(self) -> float:
        """Read the configured branch-open evidence threshold.

        When no config is active (v0.6 callers), returns 0.0 so that
        every branch opens — bit-identical to v0.6 behaviour.
        """
        return float(self._active_config.get(
            "guard_thresholds.branch_open_evidence_min", 0.0,
        ))

    def _compute_branch_evidence(self, loop_index: int) -> float:
        """Per-step branch-opening evidence in [0.0, 0.7].

        Deterministic function of how many branches have been opened
        in the recent past. Specifically: each open branch already
        recorded for this session reduces the next branch's evidence
        by 0.10, floored at 0.0 and capped at 0.7. The first branch
        of a run scores 0.7; the seventh scores 0.0.

        Rationale: this gives ``branch_open_evidence_min = 0.30`` the
        same effect as v0.6 on the shipped scenarios (S2 / S5 / S6),
        and a measurable suppression effect on
        ADV_BRANCH_EXPLOSION (which opens >= 5 branches in quick
        succession). The function is intentionally heuristic in v0.7;
        the contract is reproducibility, not optimality.
        """
        opens_so_far = len(self._session._known_claims) - 1
        evidence = 0.7 - 0.10 * max(0, opens_so_far)
        if evidence < 0.0:
            return 0.0
        if evidence > 1.0:
            return 1.0
        return evidence

    # ------------------------------------------------------------------
    # Internal: surface non-strict hook errors as timeline events
    # ------------------------------------------------------------------

    def _drain_recent_errors(self) -> None:
        # Walk only the new errors since the last drain.
        already = getattr(self, "_errors_emitted", 0)
        for err in self.errors[already:]:
            self._session._emit(EventType.HOOK_ERROR, {
                "stage": err.stage,
                "error_class": type(err.exception).__name__,
                "message": str(err.exception),
            })
        self._errors_emitted = len(self.errors)
