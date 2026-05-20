"""Deterministic DESi 5-phase model.

Phases:
    I_EXPOSITION
    II_FIRST_SATURATION_MODULATION
    III_DEVELOPMENT
    IV_DEEPENING_ATTRACTOR
    V_TERMINAL_CONVERGENCE

The rules below follow the project charter. They are intentionally
conservative: a phase is only emitted when its trigger condition is met by the
observed metrics — no LLM is consulted here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .diagnostics import (
    ENI_LOW_THRESHOLD,
    classify_en_event,
)
from .models import ENEvent, Trajectory, TrajectoryStep


# Phase tags (use the canonical strings from the project charter)
PHASE_I = "I_EXPOSITION"
PHASE_II = "II_FIRST_SATURATION_MODULATION"
PHASE_III = "III_DEVELOPMENT"
PHASE_IV = "IV_DEEPENING_ATTRACTOR"
PHASE_V = "V_TERMINAL_CONVERGENCE"

PHASES_ORDERED = (PHASE_I, PHASE_II, PHASE_III, PHASE_IV, PHASE_V)


@dataclass(frozen=True)
class PhaseSpan:
    name: str
    start_loop: int
    end_loop: int
    trigger_evidence: list[str]
    confidence: str  # "high" | "medium" | "low"


# --- rule helpers -----------------------------------------------------------


def _en_events_by_loop(events: Iterable[ENEvent]) -> dict[int, ENEvent]:
    return {e.loop_index: e for e in events}


def _step_by_loop(steps: Iterable[TrajectoryStep]) -> dict[int, TrajectoryStep]:
    return {s.loop_index: s for s in steps}


def _consecutive_low_eni_run(
    events: list[ENEvent],
) -> tuple[int, int] | None:
    """Return (start_loop, end_loop) of the first run of >= 2 consecutive
    EN events with eni_novelty < 0.10, ordered by loop_index. Else None.
    """
    sorted_events = sorted(events, key=lambda e: e.loop_index)
    run_start: int | None = None
    run_end: int | None = None
    run_len = 0
    for ev in sorted_events:
        if ev.eni_novelty < ENI_LOW_THRESHOLD:
            run_len += 1
            if run_start is None:
                run_start = ev.loop_index
            run_end = ev.loop_index
            if run_len >= 2:
                # commit at the moment we first hit length 2
                assert run_start is not None and run_end is not None
                return run_start, run_end
        else:
            run_start = None
            run_end = None
            run_len = 0
    return None


# --- per-phase detectors ----------------------------------------------------


def detect_phase_i(trajectory: Trajectory) -> PhaseSpan | None:
    """Phase I: loop 0, novel >= 10, dup < 0.30, no EN."""
    if not trajectory.steps:
        return None
    step0 = next((s for s in trajectory.steps if s.loop_index == 0), None)
    if step0 is None:
        return None
    en_at_zero = any(e.loop_index == 0 for e in trajectory.en_events)
    evidence: list[str] = []
    if step0.novel_claims >= 10:
        evidence.append(f"novel_claims={step0.novel_claims} >= 10")
    if step0.dup_rate < 0.30:
        evidence.append(f"dup_rate={step0.dup_rate:.2f} < 0.30")
    if not en_at_zero:
        evidence.append("no EN event at loop 0")

    if len(evidence) == 3:
        return PhaseSpan(
            name=PHASE_I,
            start_loop=0,
            end_loop=0,
            trigger_evidence=evidence,
            confidence="high",
        )
    if len(evidence) == 2:
        return PhaseSpan(
            name=PHASE_I,
            start_loop=0,
            end_loop=0,
            trigger_evidence=evidence + ["partial match"],
            confidence="medium",
        )
    return None


def detect_phase_ii(trajectory: Trajectory) -> PhaseSpan | None:
    """Phase II: novelty collapse to <= 2 OR early saturation AND EN fires."""
    if not trajectory.steps or not trajectory.en_events:
        return None

    sorted_steps = sorted(trajectory.steps, key=lambda s: s.loop_index)
    sorted_en = sorted(trajectory.en_events, key=lambda e: e.loop_index)
    first_en = sorted_en[0]

    # find the first step where novel_claims collapsed to <= 2
    collapse_loop: int | None = None
    for s in sorted_steps:
        if s.loop_index > 0 and s.novel_claims <= 2:
            collapse_loop = s.loop_index
            break
    if collapse_loop is None:
        return None
    # EN must fire at or after the collapse, early in the trajectory
    if first_en.loop_index < collapse_loop:
        # an EN fired even before the collapse -> still counts as Phase II trigger
        trigger_loop = first_en.loop_index
    else:
        trigger_loop = first_en.loop_index

    evidence = [
        f"novelty collapse: novel_claims<=2 at loop {collapse_loop}",
        f"first EN at loop {first_en.loop_index} (eni_novelty={first_en.eni_novelty:.2f})",
    ]
    return PhaseSpan(
        name=PHASE_II,
        start_loop=collapse_loop,
        end_loop=trigger_loop,
        trigger_evidence=evidence,
        confidence="medium",
    )


def detect_phase_iii(trajectory: Trajectory) -> PhaseSpan | None:
    """Phase III: novelty recovery after a genuine EN, dup oscillating ~0.10-0.40."""
    sorted_en = sorted(trajectory.en_events, key=lambda e: e.loop_index)
    genuine = next(
        (
            e
            for e in sorted_en
            if classify_en_event(e).label == "genuine_transformation"
        ),
        None,
    )
    if genuine is None:
        return None

    sorted_steps = sorted(trajectory.steps, key=lambda s: s.loop_index)
    post_steps = [s for s in sorted_steps if s.loop_index > genuine.loop_index]
    if not post_steps:
        return None

    # take the window up to the next genuine EN (exclusive), or end of trajectory
    next_genuine_loop: int | None = None
    for e in sorted_en:
        if (
            e.loop_index > genuine.loop_index
            and classify_en_event(e).label == "genuine_transformation"
        ):
            next_genuine_loop = e.loop_index
            break
    if next_genuine_loop is not None:
        window = [s for s in post_steps if s.loop_index < next_genuine_loop]
    else:
        window = post_steps

    if not window:
        return None

    dup_rates = [s.dup_rate for s in window]
    in_band = sum(1 for d in dup_rates if 0.10 <= d <= 0.40)
    recovered = any(s.novel_claims >= 3 for s in window)

    if not recovered:
        return None

    evidence = [
        f"genuine EN at loop {genuine.loop_index} "
        f"(eni_novelty={genuine.eni_novelty:.2f})",
        f"post-EN novelty recovery (max novel_claims="
        f"{max(s.novel_claims for s in window)})",
        f"dup_rate in [0.10, 0.40] for {in_band}/{len(window)} step(s)",
    ]
    confidence = "high" if in_band >= max(1, len(window) // 2) else "medium"
    return PhaseSpan(
        name=PHASE_III,
        start_loop=window[0].loop_index,
        end_loop=window[-1].loop_index,
        trigger_evidence=evidence,
        confidence=confidence,
    )


def detect_phase_iv(trajectory: Trajectory) -> PhaseSpan | None:
    """Phase IV: eni_novelty < 0.10 for two or more consecutive EN events."""
    run = _consecutive_low_eni_run(trajectory.en_events)
    if run is None:
        return None
    start, end = run
    evidence = [
        f"two or more consecutive EN events with eni_novelty < {ENI_LOW_THRESHOLD:.2f} "
        f"(loops {start}..{end})",
    ]
    return PhaseSpan(
        name=PHASE_IV,
        start_loop=start,
        end_loop=end,
        trigger_evidence=evidence,
        confidence="high",
    )


def detect_phase_v(trajectory: Trajectory) -> PhaseSpan | None:
    """Phase V: dup > 0.50 AND novel <= 1, OR terminal failure imminent."""
    sorted_steps = sorted(trajectory.steps, key=lambda s: s.loop_index)
    trigger_step: TrajectoryStep | None = None
    for step in sorted_steps:
        if step.dup_rate > 0.50 and step.novel_claims <= 1:
            trigger_step = step
            break

    terminal = trajectory.terminal_failure_mode
    has_terminal_failure = terminal is not None and str(terminal) not in ("NONE", "None")

    if trigger_step is None and not has_terminal_failure:
        return None

    if trigger_step is not None:
        start = trigger_step.loop_index
        end = sorted_steps[-1].loop_index if sorted_steps else start
        evidence = [
            f"dup_rate={trigger_step.dup_rate:.2f} > 0.50 AND "
            f"novel_claims={trigger_step.novel_claims} <= 1 at loop {start}"
        ]
        if has_terminal_failure:
            evidence.append(f"terminal_failure_mode={terminal}")
        return PhaseSpan(
            name=PHASE_V,
            start_loop=start,
            end_loop=end,
            trigger_evidence=evidence,
            confidence="high",
        )

    # only terminal failure flagged -> medium confidence
    assert sorted_steps  # since has_terminal_failure implies something happened
    start = sorted_steps[-1].loop_index
    return PhaseSpan(
        name=PHASE_V,
        start_loop=start,
        end_loop=start,
        trigger_evidence=[f"terminal_failure_mode={terminal} (metrics not at threshold)"],
        confidence="medium",
    )


# --- aggregator -------------------------------------------------------------


@dataclass(frozen=True)
class PhaseDetectionResult:
    phases: list[PhaseSpan] = field(default_factory=list)

    def names(self) -> list[str]:
        return [p.name for p in self.phases]


def detect_phases(trajectory: Trajectory) -> PhaseDetectionResult:
    """Run every phase detector and return the spans in canonical order."""
    detectors = (
        detect_phase_i,
        detect_phase_ii,
        detect_phase_iii,
        detect_phase_iv,
        detect_phase_v,
    )
    found: list[PhaseSpan] = []
    for fn in detectors:
        span = fn(trajectory)
        if span is not None:
            found.append(span)
    return PhaseDetectionResult(phases=found)
