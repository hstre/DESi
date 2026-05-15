"""DepthEvolutionSandbox — Aufgabe 1 (+ 5, 6, 8).

A 30-step single-knob sandbox over ``RecursiveResolver.max_depth``.
The orchestrator reuses v2.0's stable-source fingerprint discipline
and v2.0's :class:`SandboxBenchmarkGate` for the main + tool +
hash criteria, then adds:

* a :class:`DepthStressSuite` pass per step,
* a fitness function (Aufgabe 4) that kills the step on any FP /
  hash / authority violation,
* an overreasoning guard (Aufgabe 6) that rejects steps where
  fitness grew at the expense of cycle/blocked reliability,
* plateau detection over the last 5 fitness deltas (Aufgabe 8) —
  the run continues regardless.

Read-only over stable-v1.9.0. The ``stable_hash_before ==
stable_hash_after`` invariant is enforced at run completion.
"""
from __future__ import annotations

import hashlib
import pathlib
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .depth_events import DepthLedgerEventType, DepthShadowLedger
from .depth_metrics import (
    DepthImpactMetrics,
    FitnessBreakdown,
    compute_fitness,
    compute_impact_metrics,
    detect_plateau,
    overreasoning_check,
)
from .depth_mutation import (
    DEFAULT_START_DEPTH,
    DEPTH_MAX,
    DEPTH_MIN,
    DepthMutationProposal,
)
from .depth_report import (
    DepthEvolutionReport,
    DepthStepOutcome,
    DepthStepRecord,
    compute_depth_replay_hash,
    detect_convergence,
    detect_oscillation,
)
from .depth_stress import DepthStressSuite
from .gate import SandboxBenchmarkGate


_STABLE_PKG_ROOT = pathlib.Path(__file__).resolve().parent.parent


def _stable_fingerprint(root: pathlib.Path) -> str:
    """sha256[:16] over stable v1.9 .py files; v2.0/v2.1/v2.2 modules
    are excluded."""
    h = hashlib.sha256()
    excluded_top = {"sandbox", "diagnostic"}
    for p in sorted(root.rglob("*.py")):
        try:
            rel = p.relative_to(root)
        except ValueError:
            continue
        if rel.parts and rel.parts[0] in excluded_top:
            continue
        rel_str = rel.as_posix()
        file_hash = hashlib.sha256(p.read_bytes()).hexdigest()
        h.update(f"{rel_str}|{file_hash}\n".encode("utf-8"))
    return h.hexdigest()[:16]


def _genesis_hash(stable_hash: str, start_depth: int) -> str:
    return "clone_" + hashlib.sha256(
        f"depth_genesis|{stable_hash}|{start_depth}".encode("utf-8"),
    ).hexdigest()[:12]


def _clone_hash(step_id: int, parent_hash: str, proposed: int) -> str:
    raw = f"{step_id}|{parent_hash}|{proposed}"
    return "clone_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


@dataclass(frozen=True)
class _StepEval:
    record: DepthStepRecord
    advance: bool
    new_parent_hash: str
    new_parent_depth: int
    fitness: float
    metrics: DepthImpactMetrics


class DepthEvolutionSandbox:
    """Read-only single-knob evolution over ``max_depth``."""

    def __init__(
        self,
        *,
        stable_version: str = "stable-v1.9.0",
        start_depth: int = DEFAULT_START_DEPTH,
        n_steps: int = 30,
        ledger_path: pathlib.Path | str | None = None,
        gate: SandboxBenchmarkGate | None = None,
        stress: DepthStressSuite | None = None,
        stable_root: pathlib.Path | None = None,
    ) -> None:
        if n_steps < 1:
            raise ValueError("n_steps must be >= 1")
        if not (DEPTH_MIN <= start_depth <= DEPTH_MAX):
            raise ValueError(
                f"start_depth {start_depth} outside "
                f"[{DEPTH_MIN}, {DEPTH_MAX}]",
            )
        self._stable_version = stable_version
        self._n_steps = n_steps
        self._start_depth = start_depth
        self._gate = gate or SandboxBenchmarkGate()
        self._stress = stress or DepthStressSuite()
        self._ledger = DepthShadowLedger(path=ledger_path)
        self._stable_root = stable_root or _STABLE_PKG_ROOT

    @property
    def ledger(self) -> DepthShadowLedger:
        return self._ledger

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> DepthEvolutionReport:
        started_at = datetime.now(timezone.utc)
        stable_hash_before = _stable_fingerprint(self._stable_root)

        parent_hash = _genesis_hash(stable_hash_before, self._start_depth)
        parent_depth = self._start_depth
        records: list[DepthStepRecord] = []
        depth_history: list[int] = [parent_depth]
        fitness_history: list[float] = []
        prev_metrics: DepthImpactMetrics | None = None
        prev_fitness: float | None = None

        for step_id in range(1, self._n_steps + 1):
            try:
                ev = self._run_one(
                    step_id=step_id,
                    parent_hash=parent_hash,
                    parent_depth=parent_depth,
                    prev_metrics=prev_metrics,
                    prev_fitness=prev_fitness,
                )
            except Exception as exc:   # noqa: BLE001
                ev = self._kill_step(
                    step_id=step_id,
                    parent_hash=parent_hash,
                    parent_depth=parent_depth,
                    exc=exc,
                )

            records.append(ev.record)
            if ev.advance:
                parent_hash = ev.new_parent_hash
                parent_depth = ev.new_parent_depth
                prev_metrics = ev.metrics
                prev_fitness = ev.fitness
            depth_history.append(parent_depth)
            fitness_history.append(ev.fitness)

        stable_hash_after = _stable_fingerprint(self._stable_root)
        finished_at = datetime.now(timezone.utc)

        if stable_hash_before != stable_hash_after:
            raise RuntimeError(
                "stable-v1.9.0 fingerprint changed during run: "
                f"{stable_hash_before} -> {stable_hash_after}",
            )

        accepted = [r for r in records
                    if r.outcome is DepthStepOutcome.ACCEPTED]
        rejected = sum(1 for r in records
                       if r.outcome is DepthStepOutcome.REJECTED)
        killed = sum(1 for r in records
                     if r.outcome is DepthStepOutcome.KILLED)

        live_fitness = [f for f in fitness_history if f > float("-inf")]
        best_fitness = max(live_fitness) if live_fitness else 0.0
        best_depth = _best_depth(records, parent_depth)
        plateau = detect_plateau(live_fitness)
        oscillation = detect_oscillation(depth_history)
        convergence = detect_convergence(depth_history)
        # Occam: when fitness has plateaued, prefer the smallest depth
        # that achieved the peak — DESi must not recommend "deeper
        # chains" when shorter chains reach the same outcome.
        recommended_depth = best_depth

        report_payload = {
            "stable_version": self._stable_version,
            "stable_hash_before": stable_hash_before,
            "stable_hash_after": stable_hash_after,
            "total_steps": len(records),
            "accepted_steps": len(accepted),
            "rejected_steps": rejected,
            "killed_steps": killed,
            "best_depth": best_depth,
            "starting_depth": self._start_depth,
            "depth_history": depth_history,
            "plateau_detected": plateau,
            "oscillation_detected": oscillation,
            "convergence_detected": convergence,
            "best_fitness": best_fitness,
            "recommended_depth": recommended_depth,
            "steps": [r.to_dict() for r in records],
        }
        replay_hash = compute_depth_replay_hash(report_payload)

        return DepthEvolutionReport(
            started_at=started_at,
            finished_at=finished_at,
            stable_version=self._stable_version,
            stable_hash_before=stable_hash_before,
            stable_hash_after=stable_hash_after,
            total_steps=len(records),
            accepted_steps=len(accepted),
            rejected_steps=rejected,
            killed_steps=killed,
            best_depth=best_depth,
            starting_depth=self._start_depth,
            depth_history=tuple(depth_history),
            plateau_detected=plateau,
            oscillation_detected=oscillation,
            convergence_detected=convergence,
            best_fitness=best_fitness,
            recommended_depth=recommended_depth,
            steps=tuple(records),
            replay_hash=replay_hash,
        )

    # ------------------------------------------------------------------
    # Per-step
    # ------------------------------------------------------------------

    def _run_one(
        self,
        *,
        step_id: int,
        parent_hash: str,
        parent_depth: int,
        prev_metrics: DepthImpactMetrics | None,
        prev_fitness: float | None,
    ) -> _StepEval:
        proposal = DepthMutationProposal.build(
            step_id=step_id, parent_hash=parent_hash,
            parent_depth=parent_depth,
        )
        if abs(proposal.proposed_depth - proposal.parent_depth) > 1:
            raise RuntimeError(
                f"jump > 1: {proposal.parent_depth} -> "
                f"{proposal.proposed_depth}",
            )

        self._ledger.append(
            DepthLedgerEventType.DEPTH_MUTATION_PROPOSED,
            proposal.to_dict(),
        )
        clone = _clone_hash(step_id, parent_hash, proposal.proposed_depth)
        self._ledger.append(
            DepthLedgerEventType.DEPTH_MUTATION_APPLIED,
            {"step_id": step_id, "clone_hash": clone,
             "proposed_depth": proposal.proposed_depth},
        )

        # Main + tool + hash gate (read-only).
        verdict = self._gate.evaluate()

        # Stress suite at the proposed depth.
        self._ledger.append(
            DepthLedgerEventType.DEPTH_STRESS_STARTED,
            {"step_id": step_id, "clone_hash": clone,
             "max_depth": proposal.proposed_depth},
        )
        stress_run = self._stress.run(max_depth=proposal.proposed_depth)
        metrics = compute_impact_metrics(stress_run)
        self._ledger.append(
            DepthLedgerEventType.DEPTH_STRESS_COMPLETED,
            {"step_id": step_id, "clone_hash": clone,
             "max_depth": proposal.proposed_depth,
             **metrics.to_dict()},
        )

        breakdown: FitnessBreakdown = compute_fitness(
            stress_run,
            main_false_positives=verdict.false_positives,
            main_recall=verdict.recall,
            main_precision=verdict.precision,
            main_hash_mismatches=verdict.hash_mismatches,
            main_authority_blocks=verdict.authority_blocks,
            tool_precision=verdict.tool_precision,
        )

        if breakdown.killed:
            outcome = DepthStepOutcome.REJECTED
            failure_reason = breakdown.kill_reason
        else:
            verdict_o = overreasoning_check(
                prev_metrics=prev_metrics,
                new_metrics=metrics,
                prev_fitness=prev_fitness,
                new_fitness=breakdown.fitness,
                hash_mismatches=verdict.hash_mismatches,
            )
            if verdict_o.rejected:
                outcome = DepthStepOutcome.REJECTED
                failure_reason = verdict_o.reason
            else:
                outcome = DepthStepOutcome.ACCEPTED
                failure_reason = ""

        event = (
            DepthLedgerEventType.DEPTH_MUTATION_ACCEPTED
            if outcome is DepthStepOutcome.ACCEPTED
            else DepthLedgerEventType.DEPTH_MUTATION_REJECTED
        )
        self._ledger.append(
            event,
            {
                "step_id": step_id,
                "clone_hash": clone,
                "proposed_depth": proposal.proposed_depth,
                "fitness_killed": breakdown.killed,
                "failure_reason": failure_reason,
            },
        )

        accepted = (outcome is DepthStepOutcome.ACCEPTED)
        record = DepthStepRecord(
            step_id=step_id,
            parent_depth=proposal.parent_depth,
            proposed_depth=proposal.proposed_depth,
            accepted_depth=(
                proposal.proposed_depth if accepted else proposal.parent_depth
            ),
            direction=proposal.direction,
            clamped=proposal.clamped,
            outcome=outcome,
            fitness=breakdown.fitness,
            fitness_killed=breakdown.killed,
            resolved_depth_cases=breakdown.resolved_depth_cases,
            cycle_detection_correct=breakdown.cycle_detection_correct,
            blocked_propagation_correct=breakdown.blocked_propagation_correct,
            mean_resolution_depth=metrics.mean_resolution_depth,
            max_resolution_depth=metrics.max_resolution_depth,
            cycle_detection_rate=metrics.cycle_detection_rate,
            blocked_propagation_rate=metrics.blocked_propagation_rate,
            depth_exceeded_rate=metrics.depth_exceeded_rate,
            resolution_complete_rate=metrics.resolution_complete_rate,
            main_false_positives=verdict.false_positives,
            main_hash_mismatches=verdict.hash_mismatches,
            main_authority_blocks=verdict.authority_blocks,
            failure_reason=failure_reason,
        )
        return _StepEval(
            record=record,
            advance=accepted,
            new_parent_hash=clone if accepted else parent_hash,
            new_parent_depth=(
                proposal.proposed_depth if accepted else parent_depth
            ),
            fitness=breakdown.fitness,
            metrics=metrics,
        )

    def _kill_step(
        self,
        *,
        step_id: int,
        parent_hash: str,
        parent_depth: int,
        exc: BaseException,
    ) -> _StepEval:
        tb = "".join(traceback.format_exception_only(
            type(exc), exc,
        )).strip()
        self._ledger.append(
            DepthLedgerEventType.DEPTH_MUTATION_REJECTED,
            {"step_id": step_id, "killed": True,
             "failure_reason": f"{type(exc).__name__}: {exc}",
             "traceback": tb},
        )
        empty_metrics = DepthImpactMetrics(0.0, 0, 0.0, 0.0, 0.0, 0.0)
        record = DepthStepRecord(
            step_id=step_id,
            parent_depth=parent_depth,
            proposed_depth=parent_depth,
            accepted_depth=parent_depth,
            direction=0,
            clamped=False,
            outcome=DepthStepOutcome.KILLED,
            fitness=float("-inf"),
            fitness_killed=True,
            resolved_depth_cases=0,
            cycle_detection_correct=0,
            blocked_propagation_correct=0,
            mean_resolution_depth=0.0,
            max_resolution_depth=0,
            cycle_detection_rate=0.0,
            blocked_propagation_rate=0.0,
            depth_exceeded_rate=0.0,
            resolution_complete_rate=0.0,
            main_false_positives=-1,
            main_hash_mismatches=-1,
            main_authority_blocks=-1,
            failure_reason=f"{type(exc).__name__}: {exc}",
        )
        return _StepEval(
            record=record, advance=False,
            new_parent_hash=parent_hash,
            new_parent_depth=parent_depth,
            fitness=float("-inf"),
            metrics=empty_metrics,
        )


def _best_depth(
    records: list[DepthStepRecord],
    final_depth: int,
) -> int:
    accepted = [r for r in records
                if r.outcome is DepthStepOutcome.ACCEPTED]
    if not accepted:
        return final_depth
    # Tie-break: highest fitness first, then smaller depth (Occam:
    # prefer the lower depth at equal fitness — "merely longer
    # chains" should lose to "shorter chains, same outcome").
    best = max(accepted, key=lambda r: (r.fitness, -r.accepted_depth))
    return best.accepted_depth


__all__ = ["DepthEvolutionSandbox"]
