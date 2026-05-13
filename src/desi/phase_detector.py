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
    classify_en_event_composite,
)
from .models import ENEvent, Trajectory, TrajectoryStep


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
    confidence: str


def _en_events_by_loop(events: Iterable[ENEvent]) -> dict[int, ENEvent]:
    return {e.loop_index: e for e in events}


def _step_by_loop(steps: Iterable[TrajectoryStep]) -> dict[int, TrajectoryStep]:
    return {s.loop_index: s for s in steps}


def _consecutive_low_eni_run(events: list[ENEvent]) -> tuple[int, int] | None:
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
                assert run_start is not None and run_end is not None
                return run_start, run_end
        else:
            run_start = None
            run_end = None
            run_len = 0
    return None


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
        return PhaseSpan(name=PHASE_I, start_loop=0, end_loop=0,
                         trigger_evidence=evidence, confidence="high")
    if len(evidence) == 2:
        return PhaseSpan(name=PHASE_I, start_loop=0, end_loop=0,
                         trigger_evidence=evidence + ["partial match"],
                         confidence="medium")
    return None


def detect_phase_ii(trajectory: Trajectory) -> PhaseSpan | None:
    """Phase II: cycle-3 dropped EN gate; cycle-9 added persistence; cycle-1 normalised span."""
    if not trajectory.steps:
        return None
    sorted_steps = sorted(trajectory.steps, key=lambda s: s.loop_index)
    sorted_en = sorted(trajectory.en_events, key=lambda e: e.loop_index)
    first_en = sorted_en[0] if sorted_en else None
    collapse_loop: int | None = None
    for a, b in zip(sorted_steps, sorted_steps[1:]):
        if a.loop_index > 0 and a.novel_claims <= 2 and b.novel_claims <= 2:
            collapse_loop = a.loop_index
            break
    if collapse_loop is None:
        return None
    if first_en is None:
        evidence = [
            f"novelty collapse: novel_claims<=2 at loop {collapse_loop}",
            f"persistence: novel<=2 at loops {collapse_loop} and {collapse_loop+1}",
            "no EN events in trajectory (saturation observed without EN probe)",
        ]
        return PhaseSpan(name=PHASE_II, start_loop=collapse_loop, end_loop=collapse_loop,
                         trigger_evidence=evidence, confidence="low")
    trigger_loop = first_en.loop_index
    evidence = [
        f"novelty collapse: novel_claims<=2 at loop {collapse_loop}",
        f"persistence: novel<=2 at loops {collapse_loop} and {collapse_loop+1}",
        f"first EN at loop {first_en.loop_index} (eni_novelty={first_en.eni_novelty:.2f})",
    ]
    span_start, span_end = sorted((collapse_loop, trigger_loop))
    return PhaseSpan(name=PHASE_II, start_loop=span_start, end_loop=span_end,
                     trigger_evidence=evidence, confidence="medium")


def detect_phase_iii(trajectory: Trajectory) -> PhaseSpan | None:
    """Phase III: cycle-10 first-trigger on composite; boundary stays legacy.

    First-genuine trigger uses classify_en_event_composite (must be
    `genuine_transformation_confirmed`). The window-boundary lookup
    intentionally stays on the legacy classifier so unconfirmed but
    high-ENI events still bound the window (preventing the failed-
    cycle-10 regression where Phase III extended over adv06 Phase V).
    """
    sorted_en = sorted(trajectory.en_events, key=lambda e: e.loop_index)
    genuine = next(
        (e for e in sorted_en
         if classify_en_event_composite(e).label == "genuine_transformation_confirmed"),
        None,
    )
    if genuine is None:
        return None
    sorted_steps = sorted(trajectory.steps, key=lambda s: s.loop_index)
    post_steps = [s for s in sorted_steps if s.loop_index > genuine.loop_index]
    if not post_steps:
        return None
    next_genuine_loop: int | None = None
    for e in sorted_en:
        if (e.loop_index > genuine.loop_index
                and classify_en_event(e).label == "genuine_transformation"):
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
        f"genuine EN at loop {genuine.loop_index} (eni_novelty={genuine.eni_novelty:.2f})",
        f"post-EN novelty recovery (max novel_claims={max(s.novel_claims for s in window)})",
        f"dup_rate in [0.10, 0.40] for {in_band}/{len(window)} step(s)",
    ]
    confidence = "high" if in_band >= max(1, len(window) // 2) else "medium"
    return PhaseSpan(name=PHASE_III,
                     start_loop=window[0].loop_index, end_loop=window[-1].loop_index,
                     trigger_evidence=evidence, confidence=confidence)


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
    return PhaseSpan(name=PHASE_IV, start_loop=start, end_loop=end,
                     trigger_evidence=evidence, confidence="high")


def detect_phase_v(trajectory: Trajectory) -> PhaseSpan | None:
    """Phase V: dup > 0.50 AND novel <= 1, OR terminal failure (cycle-2: close on reversal)."""
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
        evidence = [
            f"dup_rate={trigger_step.dup_rate:.2f} > 0.50 AND "
            f"novel_claims={trigger_step.novel_claims} <= 1 at loop {start}"
        ]
        if has_terminal_failure:
            evidence.append(f"terminal_failure_mode={terminal}")
        if has_terminal_failure or not sorted_steps:
            end = sorted_steps[-1].loop_index if sorted_steps else start
        else:
            last_held = start
            consecutive_broken = 0
            closed = False
            for s in sorted_steps:
                if s.loop_index <= start:
                    continue
                if s.dup_rate > 0.50 and s.novel_claims <= 1:
                    last_held = s.loop_index
                    consecutive_broken = 0
                else:
                    consecutive_broken += 1
                    if consecutive_broken >= 2:
                        closed = True
                        break
            if closed:
                end = last_held
                evidence.append(
                    f"Phase V trigger no longer holds for >=2 consecutive loops "
                    f"after loop {last_held}; span closed at {last_held}"
                )
            else:
                end = sorted_steps[-1].loop_index
        return PhaseSpan(name=PHASE_V, start_loop=start, end_loop=end,
                         trigger_evidence=evidence, confidence="high")
    assert sorted_steps
    start = sorted_steps[-1].loop_index
    return PhaseSpan(name=PHASE_V, start_loop=start, end_loop=start,
                     trigger_evidence=[f"terminal_failure_mode={terminal} (metrics not at threshold)"],
                     confidence="medium")


@dataclass(frozen=True)
class PhaseDetectionResult:
    phases: list[PhaseSpan] = field(default_factory=list)

    def names(self) -> list[str]:
        return [p.name for p in self.phases]


def _clip_phase_overlaps(spans: list[PhaseSpan]) -> list[PhaseSpan]:
    """Generalization-loop cycle 2: when an earlier phase span overlaps with
    a later phase span (later in PHASES_ORDERED), clip the earlier one to
    end one loop before the later one starts. Drop spans that become empty.

    Pattern motivating this: n=20 baseline showed 5/20 fixtures with
    II/V or III/IV or III/V overlap; the n=10 suite already had 3/10.
    Detectors are independent and don't reconcile their boundaries.
    """
    order = {name: i for i, name in enumerate(PHASES_ORDERED)}
    indexed = sorted(spans, key=lambda s: order.get(s.name, 99))
    clipped: list[PhaseSpan] = []
    for i, earlier in enumerate(indexed):
        e_start, e_end = earlier.start_loop, earlier.end_loop
        for later in indexed[i + 1:]:
            if later.start_loop <= e_end and order.get(later.name, 99) > order.get(earlier.name, 99):
                e_end = min(e_end, later.start_loop - 1)
        if e_end >= e_start:
            if e_end != earlier.end_loop:
                evidence = list(earlier.trigger_evidence) + [
                    f"clipped end from {earlier.end_loop} to {e_end} (later phase started)"
                ]
                clipped.append(PhaseSpan(
                    name=earlier.name, start_loop=e_start, end_loop=e_end,
                    trigger_evidence=evidence, confidence=earlier.confidence,
                ))
            else:
                clipped.append(earlier)
        # else: drop — earlier phase entirely subsumed by a later one
    # Restore original PHASES_ORDERED ordering for downstream stability.
    clipped.sort(key=lambda s: (order.get(s.name, 99), s.start_loop))
    return clipped


def detect_phases(trajectory: Trajectory) -> PhaseDetectionResult:
    detectors = (detect_phase_i, detect_phase_ii, detect_phase_iii,
                 detect_phase_iv, detect_phase_v)
    found: list[PhaseSpan] = []
    for fn in detectors:
        span = fn(trajectory)
        if span is not None:
            found.append(span)
    return PhaseDetectionResult(phases=_clip_phase_overlaps(found))
