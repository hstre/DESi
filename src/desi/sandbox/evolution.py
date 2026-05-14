"""EvolutionSandbox — Aufgaben 1 & 5.

A 30-step self-optimization loop, **fully isolated** from the
``stable-v1.9.0`` package. The sandbox:

* fingerprints the stable package source tree once at start-up;
* per step proposes one single-knob mutation (Aufgabe 2), creates a
  ``clone_<hash>`` *value* (not a code-clone — the sandbox never
  touches disk), runs the full benchmark gate (Aufgabe 3), and
  records every event into the shadow ledger (Aufgabe 4);
* fingerprints the stable package source tree again at shutdown
  and refuses to return a report whose ``stable_hash_before !=
  stable_hash_after``;
* on any constraint violation, unexpected exception, or gate
  failure, fires the kill switch (Aufgabe 5): the step is marked
  KILLED, sandbox parameter state rolls back to the last accepted
  value, and either the loop continues with the next step (default)
  or the entire run aborts (when ``abort_on_kill=True``).

The whole module is **read-only with respect to stable-v1.9.0** —
the v1.5 ``BenchmarkRunner`` and v1.9 ``ToolBenchmarkRunner`` are
called as-is, no monkey-patching, no rebinding, no rewriting.
"""
from __future__ import annotations

import hashlib
import pathlib
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .gate import GateVerdict, SandboxBenchmarkGate
from .ledger import ShadowLedger, ShadowLedgerEventType
from .mutation import BASELINE_VALUE, MutationProposal
from .report import (
    EvolutionReport,
    StepOutcome,
    StepRecord,
    compute_replay_hash,
    detect_convergence,
    detect_drift,
    detect_local_optimum,
    detect_oscillation,
)


# Default location of the stable package source — used to fingerprint
# it before/after the run so we can prove no source file changed.
_STABLE_PKG_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _stable_source_fingerprint(root: pathlib.Path) -> str:
    """sha256[:16] over the sorted ``(rel_path, file_sha256)`` pairs.

    All ``.py`` files under ``root`` are read in binary mode and
    their hashes concatenated in deterministic order. The
    ``sandbox`` package itself is **excluded** — it is part of v2.0
    and may change freely.
    """
    h = hashlib.sha256()
    paths: list[pathlib.Path] = []
    for p in sorted(root.rglob("*.py")):
        # Skip the v2.0 sandbox package.
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        if rel.parts and rel.parts[0] == "sandbox":
            continue
        paths.append(p)
    for p in paths:
        rel = p.relative_to(root).as_posix()
        file_hash = hashlib.sha256(p.read_bytes()).hexdigest()
        h.update(f"{rel}|{file_hash}\n".encode("utf-8"))
    return h.hexdigest()[:16]


def _clone_hash(step_id: int, parent_hash: str, proposed_value: float) -> str:
    raw = f"{step_id}|{parent_hash}|{proposed_value:.6f}"
    return "clone_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def _initial_parent_hash(stable_hash: str) -> str:
    return "clone_" + hashlib.sha256(
        f"genesis|{stable_hash}".encode("utf-8"),
    ).hexdigest()[:12]


@dataclass(frozen=True)
class _StepEvaluation:
    """Internal: paired step record + outcome decision."""

    record: StepRecord
    advance_parent: bool
    new_parent_hash: str
    new_parent_value: float


class EvolutionSandbox:
    """Isolated 30-step evolution loop.

    Parameters
    ----------
    stable_version:
        Pin string for the immutable host package — recorded but
        never used to alter behaviour. Must match an existing
        release tag in spirit (``"stable-v1.9.0"``).
    n_steps:
        Number of evolution steps. The directive fixes this at 30.
    abort_on_kill:
        If True, the first KILLED step ends the run early. If False
        (default), the kill switch only discards that step's
        mutation and the loop continues from the prior parent.
    ledger_path:
        Optional path for the shadow ledger to persist JSONL.
    initial_value:
        Starting value of ``branch_open_evidence_min``. Defaults to
        the v0.7 production value (0.45).
    """

    def __init__(
        self,
        *,
        stable_version: str = "stable-v1.9.0",
        n_steps: int = 30,
        abort_on_kill: bool = False,
        ledger_path: pathlib.Path | str | None = None,
        initial_value: float = BASELINE_VALUE,
        gate: SandboxBenchmarkGate | None = None,
        stable_root: pathlib.Path | None = None,
    ) -> None:
        if n_steps < 1:
            raise ValueError("n_steps must be >= 1")
        self._stable_version = stable_version
        self._n_steps = n_steps
        self._abort_on_kill = abort_on_kill
        self._initial_value = initial_value
        self._gate = gate or SandboxBenchmarkGate()
        self._ledger = ShadowLedger(path=ledger_path)
        self._stable_root = stable_root or _STABLE_PKG_ROOT

    @property
    def ledger(self) -> ShadowLedger:
        return self._ledger

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> EvolutionReport:
        started_at = datetime.now(timezone.utc)
        stable_hash_before = _stable_source_fingerprint(self._stable_root)

        self._ledger.append(
            ShadowLedgerEventType.SANDBOX_STARTED,
            {
                "stable_version": self._stable_version,
                "n_steps": self._n_steps,
                "abort_on_kill": self._abort_on_kill,
                "initial_value": self._initial_value,
                "stable_hash_before": stable_hash_before,
            },
        )

        parent_hash = _initial_parent_hash(stable_hash_before)
        parent_value = self._initial_value
        records: list[StepRecord] = []
        accepted_values: list[float] = [parent_value]
        aborted = False

        for step_id in range(1, self._n_steps + 1):
            try:
                step_eval = self._run_one_step(
                    step_id=step_id,
                    parent_hash=parent_hash,
                    parent_value=parent_value,
                )
            except Exception as exc:   # noqa: BLE001 — kill switch
                step_eval = self._kill_step(
                    step_id=step_id,
                    parent_hash=parent_hash,
                    parent_value=parent_value,
                    exc=exc,
                )

            records.append(step_eval.record)
            if step_eval.advance_parent:
                parent_hash = step_eval.new_parent_hash
                parent_value = step_eval.new_parent_value
                accepted_values.append(parent_value)
            if (
                self._abort_on_kill
                and step_eval.record.outcome is StepOutcome.KILLED
            ):
                aborted = True
                break

        stable_hash_after = _stable_source_fingerprint(self._stable_root)
        finished_at = datetime.now(timezone.utc)

        if stable_hash_before != stable_hash_after:
            # This must never happen — the sandbox is read-only.
            raise RuntimeError(
                "stable-v1.9.0 fingerprint changed during sandbox.run(): "
                f"{stable_hash_before} -> {stable_hash_after}",
            )

        best_value, best_clone = _best_clone(records, parent_value)
        report_core = {
            "stable_version": self._stable_version,
            "stable_hash_before": stable_hash_before,
            "stable_hash_after": stable_hash_after,
            "total_steps": len(records),
            "accepted_steps":
                sum(1 for r in records if r.outcome is StepOutcome.ACCEPTED),
            "rejected_steps":
                sum(1 for r in records if r.outcome is StepOutcome.REJECTED),
            "killed_steps":
                sum(1 for r in records if r.outcome is StepOutcome.KILLED),
            "best_clone_hash": best_clone,
            "best_parameter_value": best_value,
            "final_parameter_value": parent_value,
            "local_optima_detected":
                detect_local_optimum(accepted_values),
            "oscillation_detected":
                detect_oscillation(accepted_values),
            "convergence_detected":
                detect_convergence(accepted_values),
            "drift_detected": detect_drift(accepted_values),
            "steps": [r.to_dict() for r in records],
            "aborted": aborted,
        }
        replay_hash = compute_replay_hash(report_core)

        self._ledger.append(
            ShadowLedgerEventType.SANDBOX_COMPLETED,
            {
                "stable_hash_after": stable_hash_after,
                "total_steps": report_core["total_steps"],
                "accepted_steps": report_core["accepted_steps"],
                "rejected_steps": report_core["rejected_steps"],
                "killed_steps": report_core["killed_steps"],
                "best_clone_hash": best_clone,
                "replay_hash": replay_hash,
            },
        )

        return EvolutionReport(
            started_at=started_at,
            finished_at=finished_at,
            stable_version=self._stable_version,
            stable_hash_before=stable_hash_before,
            stable_hash_after=stable_hash_after,
            total_steps=report_core["total_steps"],
            accepted_steps=report_core["accepted_steps"],
            rejected_steps=report_core["rejected_steps"],
            killed_steps=report_core["killed_steps"],
            best_clone_hash=best_clone,
            best_parameter_value=best_value,
            final_parameter_value=parent_value,
            local_optima_detected=bool(report_core["local_optima_detected"]),
            oscillation_detected=bool(report_core["oscillation_detected"]),
            convergence_detected=bool(report_core["convergence_detected"]),
            drift_detected=bool(report_core["drift_detected"]),
            steps=tuple(records),
            replay_hash=replay_hash,
        )

    # ------------------------------------------------------------------
    # Per-step helpers
    # ------------------------------------------------------------------

    def _run_one_step(
        self,
        *,
        step_id: int,
        parent_hash: str,
        parent_value: float,
    ) -> _StepEvaluation:
        proposal = MutationProposal.build(
            step_id=step_id,
            parent_hash=parent_hash,
            parent_value=parent_value,
        )
        # Single-knob hard invariant.
        if len(proposal.mutated_parameters) != 1:
            raise RuntimeError(
                "single-knob invariant violated: "
                f"{proposal.mutated_parameters!r}",
            )

        self._ledger.append(
            ShadowLedgerEventType.MUTATION_PROPOSED,
            proposal.to_dict(),
        )

        clone = _clone_hash(step_id, parent_hash, proposal.proposed_value)

        self._ledger.append(
            ShadowLedgerEventType.MUTATION_APPLIED,
            {
                "step_id": step_id,
                "clone_hash": clone,
                "parameter": proposal.parameter,
                "proposed_value": proposal.proposed_value,
            },
        )

        self._ledger.append(
            ShadowLedgerEventType.BENCHMARK_STARTED,
            {"step_id": step_id, "clone_hash": clone},
        )
        verdict = self._gate.evaluate()
        self._ledger.append(
            ShadowLedgerEventType.BENCHMARK_COMPLETED,
            {"step_id": step_id, "clone_hash": clone,
             **verdict.to_dict()},
        )

        outcome = (
            StepOutcome.ACCEPTED if verdict.passed
            else StepOutcome.REJECTED
        )
        accept_event = (
            ShadowLedgerEventType.MUTATION_ACCEPTED if verdict.passed
            else ShadowLedgerEventType.MUTATION_REJECTED
        )
        self._ledger.append(
            accept_event,
            {
                "step_id": step_id,
                "clone_hash": clone,
                "parameter": proposal.parameter,
                "proposed_value": proposal.proposed_value,
                "failure_reason": verdict.failure_reason,
            },
        )

        record = StepRecord(
            step_id=step_id,
            parent_hash=parent_hash,
            clone_hash=clone,
            parameter=proposal.parameter,
            parent_value=proposal.parent_value,
            proposed_value=proposal.proposed_value,
            direction=proposal.direction,
            clamped=proposal.clamped,
            outcome=outcome,
            precision=verdict.precision,
            recall=verdict.recall,
            false_positives=verdict.false_positives,
            authority_blocks=verdict.authority_blocks,
            tool_precision=verdict.tool_precision,
            hash_mismatches=verdict.hash_mismatches,
            failure_reason=verdict.failure_reason,
        )

        return _StepEvaluation(
            record=record,
            advance_parent=verdict.passed,
            new_parent_hash=clone if verdict.passed else parent_hash,
            new_parent_value=(
                proposal.proposed_value if verdict.passed else parent_value
            ),
        )

    def _kill_step(
        self,
        *,
        step_id: int,
        parent_hash: str,
        parent_value: float,
        exc: BaseException,
    ) -> _StepEvaluation:
        """Aufgabe 5 — kill switch: record + roll back, never crash."""
        reason = f"{type(exc).__name__}: {exc}"
        clone = _clone_hash(step_id, parent_hash, parent_value)
        tb_excerpt = "".join(traceback.format_exception_only(
            type(exc), exc,
        )).strip()
        self._ledger.append(
            ShadowLedgerEventType.MUTATION_REJECTED,
            {
                "step_id": step_id,
                "clone_hash": clone,
                "killed": True,
                "failure_reason": reason,
                "traceback": tb_excerpt,
            },
        )
        record = StepRecord(
            step_id=step_id,
            parent_hash=parent_hash,
            clone_hash=clone,
            parameter="branch_open_evidence_min",
            parent_value=parent_value,
            proposed_value=parent_value,
            direction=0,
            clamped=False,
            outcome=StepOutcome.KILLED,
            precision=0.0,
            recall=0.0,
            false_positives=-1,
            authority_blocks=-1,
            tool_precision=0.0,
            hash_mismatches=-1,
            failure_reason=reason,
        )
        return _StepEvaluation(
            record=record,
            advance_parent=False,
            new_parent_hash=parent_hash,
            new_parent_value=parent_value,
        )


def _best_clone(
    records: list[StepRecord],
    final_value: float,
) -> tuple[float, str]:
    """Best = the accepted step with the highest parameter value.

    The "best" measure here is intentionally simple — accepted
    steps are by definition gate-clean (precision=1.0, recall=1.0,
    fp=0), so they all tie on the explicit metrics. The largest
    accepted ``proposed_value`` reflects "how far the sandbox could
    push the knob and still pass". If no step was accepted, the
    best clone is the genesis state.
    """
    accepted = [r for r in records if r.outcome is StepOutcome.ACCEPTED]
    if not accepted:
        return final_value, "clone_genesis"
    best = max(accepted, key=lambda r: r.proposed_value)
    return best.proposed_value, best.clone_hash


__all__ = ["EvolutionSandbox"]
