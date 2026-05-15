"""Depth fitness + impact metrics — Aufgaben 4 + 5 + 6.

The fitness function and the six impact-metric counters are both
**purely data-derived**. Hard violations (FP > 0, hash mismatch,
authority < 10) immediately kill the step regardless of any
positive reward in the stress suite.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from ..recursive import ResolutionState
from .depth_stress import ALL_DEPTH_STRESS_CASES, DepthStressRun


# Cases that should resolve to ``RESOLUTION_COMPLETE``.
_DEPTH_CHAIN_IDS = {"D1", "D2", "D3", "D4", "D5"}
_CYCLE_IDS = {"D6"}
_BLOCKED_IDS = {"D7", "D8"}


# Sentinel for the kill condition. We don't use math.inf in the
# stored report payload (it's not JSON-clean); the orchestrator
# checks ``killed`` separately.
KILL_PENALTY: float = -math.inf


@dataclass(frozen=True)
class DepthImpactMetrics:
    """Per-step snapshot over the stress suite — Aufgabe 5."""

    mean_resolution_depth: float
    max_resolution_depth: int
    cycle_detection_rate: float
    blocked_propagation_rate: float
    depth_exceeded_rate: float
    resolution_complete_rate: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "mean_resolution_depth": self.mean_resolution_depth,
            "max_resolution_depth": self.max_resolution_depth,
            "cycle_detection_rate": self.cycle_detection_rate,
            "blocked_propagation_rate": self.blocked_propagation_rate,
            "depth_exceeded_rate": self.depth_exceeded_rate,
            "resolution_complete_rate": self.resolution_complete_rate,
        }


def compute_impact_metrics(stress_run: DepthStressRun) -> DepthImpactMetrics:
    results = stress_run.results
    if not results:
        return DepthImpactMetrics(0.0, 0, 0.0, 0.0, 0.0, 0.0)
    depths = [r.depth_reached for r in results]
    total = len(results)
    complete = sum(
        1 for r in results
        if r.final_state is ResolutionState.RESOLUTION_COMPLETE
    )
    exceeded = sum(
        1 for r in results
        if r.final_state is ResolutionState.RESOLUTION_DEPTH_EXCEEDED
    )
    cycles = sum(
        1 for r in results if r.case.case_id in _CYCLE_IDS and r.correct
    )
    blocked = sum(
        1 for r in results if r.case.case_id in _BLOCKED_IDS and r.correct
    )
    return DepthImpactMetrics(
        mean_resolution_depth=round(sum(depths) / total, 6),
        max_resolution_depth=max(depths),
        cycle_detection_rate=round(cycles / max(1, len(_CYCLE_IDS)), 6),
        blocked_propagation_rate=round(
            blocked / max(1, len(_BLOCKED_IDS)), 6,
        ),
        depth_exceeded_rate=round(exceeded / total, 6),
        resolution_complete_rate=round(complete / total, 6),
    )


# ---------------------------------------------------------------------------
# Fitness — Aufgabe 4
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FitnessBreakdown:
    """Components of one step's fitness score."""

    resolved_depth_cases: int
    cycle_detection_correct: int
    blocked_propagation_correct: int
    killed: bool
    kill_reason: str
    fitness: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "resolved_depth_cases": self.resolved_depth_cases,
            "cycle_detection_correct": self.cycle_detection_correct,
            "blocked_propagation_correct": self.blocked_propagation_correct,
            "killed": self.killed,
            "kill_reason": self.kill_reason,
            "fitness": (
                "-inf" if self.killed
                else round(self.fitness, 6)
            ),
        }


def compute_fitness(
    stress_run: DepthStressRun,
    *,
    main_false_positives: int,
    main_recall: float,
    main_precision: float,
    main_hash_mismatches: int,
    main_authority_blocks: int,
    tool_precision: float,
    required_authority_blocks: int = 10,
) -> FitnessBreakdown:
    """Compute fitness with hard kill on any FP / hash / authority
    violation. Otherwise: reward correct stress-suite outcomes."""
    reasons: list[str] = []
    if main_false_positives > 0:
        reasons.append(f"false_positives={main_false_positives}")
    if main_hash_mismatches > 0:
        reasons.append(f"hash_mismatches={main_hash_mismatches}")
    if main_authority_blocks != required_authority_blocks:
        reasons.append(
            f"authority_blocks={main_authority_blocks} "
            f"!= {required_authority_blocks}",
        )
    if main_precision != 1.0:
        reasons.append(f"precision={main_precision} != 1.0")
    if main_recall != 1.0:
        reasons.append(f"recall={main_recall} != 1.0")
    if tool_precision != 1.0:
        reasons.append(f"tool_precision={tool_precision} != 1.0")

    resolved = sum(
        1 for r in stress_run.results
        if r.case.case_id in _DEPTH_CHAIN_IDS
        and r.final_state is ResolutionState.RESOLUTION_COMPLETE
    )
    cycle_ok = sum(
        1 for r in stress_run.results
        if r.case.case_id in _CYCLE_IDS and r.correct
    )
    blocked_ok = sum(
        1 for r in stress_run.results
        if r.case.case_id in _BLOCKED_IDS and r.correct
    )

    if reasons:
        return FitnessBreakdown(
            resolved_depth_cases=resolved,
            cycle_detection_correct=cycle_ok,
            blocked_propagation_correct=blocked_ok,
            killed=True,
            kill_reason="; ".join(reasons),
            fitness=KILL_PENALTY,
        )
    return FitnessBreakdown(
        resolved_depth_cases=resolved,
        cycle_detection_correct=cycle_ok,
        blocked_propagation_correct=blocked_ok,
        killed=False,
        kill_reason="",
        fitness=float(resolved + cycle_ok + blocked_ok),
    )


# ---------------------------------------------------------------------------
# Overreasoning guard — Aufgabe 6
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OverreasoningVerdict:
    rejected: bool
    reason: str


def overreasoning_check(
    *,
    prev_metrics: DepthImpactMetrics | None,
    new_metrics: DepthImpactMetrics,
    prev_fitness: float | None,
    new_fitness: float,
    hash_mismatches: int,
) -> OverreasoningVerdict:
    """Reject when raising the depth bought a fitness gain at the
    cost of reliability."""
    if hash_mismatches > 0:
        return OverreasoningVerdict(True, "replay mismatch")
    if prev_metrics is None or prev_fitness is None:
        return OverreasoningVerdict(False, "")
    fitness_grew = new_fitness > prev_fitness
    if not fitness_grew:
        return OverreasoningVerdict(False, "")
    if new_metrics.cycle_detection_rate < prev_metrics.cycle_detection_rate:
        return OverreasoningVerdict(
            True,
            "cycle_detection_rate decreased while fitness grew",
        )
    if (new_metrics.blocked_propagation_rate
            < prev_metrics.blocked_propagation_rate):
        return OverreasoningVerdict(
            True,
            "blocked_propagation_rate decreased while fitness grew",
        )
    return OverreasoningVerdict(False, "")


# ---------------------------------------------------------------------------
# Plateau — Aufgabe 8
# ---------------------------------------------------------------------------


def detect_plateau(
    fitness_history: list[float],
    *,
    window: int = 5,
) -> bool:
    """5 consecutive zero-delta fitness values."""
    if len(fitness_history) < window:
        return False
    tail = fitness_history[-window:]
    return all(b == a for a, b in zip(tail, tail[1:]))


__all__ = [
    "DepthImpactMetrics",
    "FitnessBreakdown",
    "KILL_PENALTY",
    "OverreasoningVerdict",
    "compute_fitness",
    "compute_impact_metrics",
    "detect_plateau",
    "overreasoning_check",
]
