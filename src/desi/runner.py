"""Top-level DESi run entrypoint.

v0.3 introduces :func:`run_desi` as a thin wrapper around
:func:`desi.diagnostics.compute_all`. The wrapper is the place where an
optional :class:`desi.memory.MemoryHook` is invoked. The hook receives
only lifecycle callbacks and is *outside* the diagnostic logic:

* ``run_desi(trajectory)`` is bit-for-bit equivalent to
  ``compute_all(trajectory)``.
* ``run_desi(trajectory, memory_hook=hook)`` produces the **same**
  :class:`DeterministicMetrics`, plus side-effect writes to the hook's
  recorder.

No operator, guard, detector, classifier, or report builder reads from
the hook. Identical input → identical output, with or without the hook.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .diagnostics import DeterministicMetrics, compute_all
from .models import Trajectory

if TYPE_CHECKING:
    from .memory.hook import MemoryHook


def run_desi(
    trajectory: Trajectory,
    *,
    config: dict | None = None,
    memory_hook: "MemoryHook | None" = None,
) -> DeterministicMetrics:
    """Run DESi diagnostics on ``trajectory``.

    If ``memory_hook`` is provided, the hook is notified at three
    lifecycle points — run start, per-step, run end — and may write to
    its recorder. The hook **must not** affect the result; this
    invariant is tested explicitly in ``tests/test_runner.py``.

    v0.7: ``config`` is an optional flat dict of named knobs. When
    provided, the memory hook receives it via :meth:`set_active_config`
    before ``on_run_start``. Exactly one knob is read by v0.7's
    branch-opening guard:
    ``guard_thresholds.branch_open_evidence_min`` (default 0.30, range
    [0.0, 1.0]). Passing ``config=None`` preserves v0.6 behaviour
    bit-for-bit.

    Default (``memory_hook=None``) preserves pre-v0.3 behaviour
    exactly. DESi continues to run without a memory backend and
    without a database.
    """
    if memory_hook is None:
        return compute_all(trajectory)

    # v0.7: hand the config to the hook so its config-aware guards
    # can read knob values. Hooks that don't implement set_active_config
    # silently ignore the config — v0.7 stays additive.
    if config is not None:
        setter = getattr(memory_hook, "set_active_config", None)
        if callable(setter):
            setter(config)

    # Hook is opt-in. From here on every memory-side call is wrapped in
    # the hook's _safe shim so that a misbehaving recorder cannot
    # contaminate the diagnostic result.
    memory_hook.on_run_start(trajectory)
    for step in trajectory.steps:
        memory_hook.on_step(step)
    report = compute_all(trajectory)
    memory_hook.on_run_end(report)
    return report
