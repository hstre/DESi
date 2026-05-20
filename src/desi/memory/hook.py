"""MemoryHook — outermost write-only observer of a DESi run.

v0.3 directive (in short):

  *Memory beobachtet den Run. Operatoren bleiben rein.*

The hook sits *outside* the run loop. It receives lifecycle callbacks
from :func:`desi.runner.run_desi`. It writes — only writes — to a
:class:`desi.memory.MemoryRecorder`. It never reads from the recorder
during the run, never returns memory state into the run, never alters
the run's verdicts. A failing write does not break the run unless the
hook is constructed with ``strict=True``.

Three guarantees:

1. Identical trajectory input produces identical DESi output regardless
   of whether a hook is attached. (Tested in ``tests/test_runner.py``.)
2. A failing recorder under the default ``strict=False`` is collected
   on ``hook.errors`` and the run continues. (Tested in
   ``tests/memory/test_hook.py``.)
3. A failing recorder under ``strict=True`` raises and the run aborts.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

from .claim import ClaimState
from .recorder import MemoryRecorder
from .relations import RelationType

if TYPE_CHECKING:
    from ..models import Trajectory, TrajectoryStep


@dataclass
class HookError:
    """One captured failure during a non-strict run.

    The error is stored verbatim; the hook makes no attempt to translate
    or re-classify it. Downstream callers may inspect ``stage`` and
    ``exception`` to decide what to do.
    """

    stage: str
    exception: BaseException
    payload: dict[str, Any] = field(default_factory=dict)


class MemoryHook:
    """Write-only adapter from a DESi run to a :class:`MemoryRecorder`.

    Construct with a recorder and pass to :func:`desi.runner.run_desi`:

    >>> hook = MemoryHook(recorder=MemoryRecorder(InMemoryStore()),
    ...                   model="claude-opus-4-7")
    >>> report = run_desi(trajectory, memory_hook=hook)

    All hook methods are no-ops on failure when ``strict=False`` (the
    default). On ``strict=True`` they re-raise after recording the
    error so that the run can abort.
    """

    def __init__(
        self,
        recorder: MemoryRecorder,
        *,
        model: str = "unknown",
        strict: bool = False,
        config: dict[str, Any] | None = None,
        prompt_hash: str | None = None,
    ) -> None:
        self._recorder = recorder
        self.model = model
        self.strict = strict
        self._config = config or {}
        self._prompt_hash = prompt_hash
        self.errors: list[HookError] = []
        self._seen_claim_ids: set[str] = set()
        self._previous_focus: str | None = None
        self._run_started: bool = False
        # v0.7: optional behaviour-effective configuration passed from
        # run_desi(config=...). The base MemoryHook stores it and lets
        # subclasses (notably _SessionHook) consult it to gate
        # branch-opening decisions on a knob value.
        self._active_config: dict[str, Any] = {}

    def set_active_config(self, config: dict[str, Any]) -> None:
        """Receive the v0.7 run_desi config. Stored verbatim."""
        self._active_config = dict(config)

    @property
    def active_config(self) -> dict[str, Any]:
        """Read-only view of the currently active config (or {})."""
        return dict(self._active_config)

    # ------------------------------------------------------------------
    # Safety wrapper
    # ------------------------------------------------------------------

    def _safe(
        self,
        stage: str,
        fn: Callable[..., Any],
        *args: Any,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Run ``fn(*args, **kwargs)``; never propagate unless strict."""
        try:
            return fn(*args, **kwargs)
        except BaseException as exc:  # noqa: BLE001 — intentional broad catch
            err = HookError(stage=stage, exception=exc,
                            payload=payload or {})
            self.errors.append(err)
            if self.strict:
                raise

    # ------------------------------------------------------------------
    # Lifecycle entry points (called by the runner)
    # ------------------------------------------------------------------

    def on_run_start(self, trajectory: "Trajectory") -> None:
        run_id = _derive_run_id(trajectory)
        self._safe(
            "on_run_start",
            self._recorder.start_run,
            run_id=run_id,
            model=self.model,
            config=self._config,
            prompt_hash=self._prompt_hash,
            label=str(getattr(trajectory, "trajectory_id", "")),
            payload={"trajectory_id": getattr(trajectory, "trajectory_id", None)},
        )
        # If the recorder rejected the run (non-strict), mark the flag
        # so the per-step calls fail quickly rather than retrying.
        self._run_started = (
            self._recorder.active_run is not None
            and self._recorder.active_run.run_id == run_id
        )
        self._previous_focus = None
        self._seen_claim_ids = set()

    def on_step(self, step: "TrajectoryStep") -> None:
        if not self._run_started:
            return
        # 1. OperatorEvent for the step itself.
        self._safe(
            "on_step.operator_event",
            self._recorder.record_operator_event,
            operator_name=str(step.operator),
            loop_index=int(step.loop_index),
            input_claims=(self._previous_focus,) if self._previous_focus else (),
            output_claims=(step.focus_claim_id,) if step.focus_claim_id else (),
            sub_role=str(getattr(step, "operator_sub_role", "") or ""),
            payload={"loop_index": step.loop_index, "operator": step.operator},
        )
        # 2. If this step introduces a not-yet-seen focus claim, record it.
        focus = step.focus_claim_id
        if focus and focus not in self._seen_claim_ids:
            self._seen_claim_ids.add(focus)
            self._safe(
                "on_step.record_claim",
                self._recorder.record_claim,
                content=focus,
                method=str(step.operator),
                state=ClaimState.PROPOSED,
                operator_path=(str(step.operator),),
                claim_id=focus,
                payload={"focus_claim_id": focus},
            )
        # 3. DERIVES_FROM relation when focus changes between consecutive
        #    steps.
        if (
            focus
            and self._previous_focus
            and focus != self._previous_focus
        ):
            self._safe(
                "on_step.derives_from",
                self._recorder.record_relation,
                source=focus,
                target=self._previous_focus,
                rel_type=RelationType.DERIVES_FROM,
                payload={"from": self._previous_focus, "to": focus},
            )
        if focus:
            self._previous_focus = focus

    def on_run_end(self, report: Any) -> None:
        if not self._run_started:
            return
        self._safe(
            "on_run_end",
            self._recorder.end_run,
            payload={"report_type": type(report).__name__},
        )
        self._run_started = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _derive_run_id(trajectory: "Trajectory") -> str:
    """Stable run id derived from the trajectory id + step count.

    Deterministic per (trajectory_id, n_steps) so that re-running the
    same trajectory under a fresh recorder produces the same run_id.
    Idempotent: a second start_run with the same id is rejected by the
    recorder; the hook captures the error in non-strict mode and the
    run continues.
    """
    tid = str(getattr(trajectory, "trajectory_id", "no_id"))
    n = len(getattr(trajectory, "steps", []) or [])
    raw = f"{tid}\x00{n}".encode("utf-8")
    return "run_" + hashlib.sha256(raw).hexdigest()[:12]
