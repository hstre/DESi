"""Deterministic DESi diagnostics. No LLM calls live here.

All thresholds match the project charter:
- eni_novelty < 0.10 -> local_variation_or_false_return
- eni_novelty > 0.12 -> genuine_transformation
- else              -> borderline
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .models import ENEvent, Trajectory


ENI_LOW_THRESHOLD = 0.10
ENI_HIGH_THRESHOLD = 0.12


# --- EN event classification ------------------------------------------------


@dataclass(frozen=True)
class ENClassification:
    loop_index: int
    eni_novelty: float
    label: str  # "local_variation_or_false_return" | "genuine_transformation" | "borderline"


def classify_en_event(event: ENEvent) -> ENClassification:
    """Apply the bimodal-EN-threshold rule to a single EN event."""
    eni = event.eni_novelty
    if eni < ENI_LOW_THRESHOLD:
        label = "local_variation_or_false_return"
    elif eni > ENI_HIGH_THRESHOLD:
        label = "genuine_transformation"
    else:
        label = "borderline"
    return ENClassification(
        loop_index=event.loop_index, eni_novelty=eni, label=label
    )


def classify_en_events(events: Iterable[ENEvent]) -> list[ENClassification]:
    return [classify_en_event(e) for e in events]


# --- Novelty recovery -------------------------------------------------------


@dataclass(frozen=True)
class NoveltyRecovery:
    loop_index: int
    dup_delta: float | None
    novel_claims_next: int | None
    recovered: bool


def compute_novelty_recovery(event: ENEvent) -> NoveltyRecovery:
    """Was the EN event followed by a measurable novelty recovery?"""
    dup_delta: float | None
    if event.dup_rate_before is not None and event.dup_rate_after is not None:
        dup_delta = event.dup_rate_after - event.dup_rate_before
    else:
        dup_delta = None
    nc_next = event.novel_claims_next
    recovered = (
        dup_delta is not None
        and dup_delta <= -0.10
        and nc_next is not None
        and nc_next >= 1
    )
    return NoveltyRecovery(
        loop_index=event.loop_index,
        dup_delta=dup_delta,
        novel_claims_next=nc_next,
        recovered=recovered,
    )


# --- Penultimate EN principle ----------------------------------------------


@dataclass(frozen=True)
class PenultimateENAssessment:
    has_candidate: bool
    penultimate_loop: int | None
    penultimate_label: str | None
    last_loop: int | None
    last_label: str | None
    note: str


def detect_penultimate_en_candidate(trajectory: Trajectory) -> PenultimateENAssessment:
    events = trajectory.en_events
    if len(events) < 2:
        return PenultimateENAssessment(
            has_candidate=False,
            penultimate_loop=None, penultimate_label=None,
            last_loop=None, last_label=None,
            note="fewer than 2 EN events; principle not applicable",
        )
    classifications = classify_en_events(events)
    penult = classifications[-2]
    last = classifications[-1]
    is_candidate = (
        penult.label == "genuine_transformation"
        and last.label != "genuine_transformation"
    )
    note = (
        "penultimate EN was the last genuine transformation"
        if is_candidate
        else "penultimate EN does not match the principle's signature"
    )
    return PenultimateENAssessment(
        has_candidate=is_candidate,
        penultimate_loop=penult.loop_index, penultimate_label=penult.label,
        last_loop=last.loop_index, last_label=last.label,
        note=note,
    )


# --- Terminal attractor subjects (stub / heuristic) ------------------------


@dataclass(frozen=True)
class TerminalAttractorReport:
    candidate_claim_ids: list[str]
    method: str
    note: str


def detect_terminal_attractor_subjects(
    trajectory: Trajectory,
    *,
    tail_loops: int = 3,
) -> TerminalAttractorReport:
    steps = trajectory.steps[-tail_loops:]
    if not steps:
        return TerminalAttractorReport(
            candidate_claim_ids=[],
            method="tail_focus_repetition",
            note="trajectory has no steps",
        )
    focus_counts: dict[str, int] = {}
    presence_counts: dict[str, int] = {}
    for step in steps:
        if step.focus_claim_id:
            focus_counts[step.focus_claim_id] = (
                focus_counts.get(step.focus_claim_id, 0) + 1
            )
        for claim in step.claims:
            presence_counts[claim.claim_id] = presence_counts.get(claim.claim_id, 0) + 1
    candidates = sorted(
        {cid for cid, n in focus_counts.items() if n >= 2}
        | {cid for cid, n in presence_counts.items() if n == len(steps) and n >= 2}
    )
    return TerminalAttractorReport(
        candidate_claim_ids=candidates,
        method="tail_focus_repetition",
        note=(
            f"examined last {len(steps)} step(s); candidate = focus repeated "
            "twice OR claim present in every tail step"
        ),
    )


# --- Failure-mode summary --------------------------------------------------


@dataclass(frozen=True)
class FailureModeSummary:
    terminal: str | None
    per_step: list[tuple[int, str]] = field(default_factory=list)


def summarize_failure_mode(trajectory: Trajectory) -> FailureModeSummary:
    per_step: list[tuple[int, str]] = []
    for step in trajectory.steps:
        if step.failure_mode and str(step.failure_mode) not in ("NONE", "None"):
            per_step.append((step.loop_index, str(step.failure_mode)))
    terminal: str | None = (
        str(trajectory.terminal_failure_mode)
        if trajectory.terminal_failure_mode is not None
        else None
    )
    return FailureModeSummary(terminal=terminal, per_step=per_step)


# --- Branch-explosion detector (cycle 4) -----------------------------------
#
# Closes DET-FAL T7 (paper0/self_reflection.md §6.1).

BRANCH_EXPLOSION_MIN_BRANCHES = 5
BRANCH_EXPLOSION_MAX_AVG_DUP = 0.20
BRANCH_EXPLOSION_MIN_AVG_NOVEL = 5.0


@dataclass(frozen=True)
class BranchExplosionReport:
    detected: bool
    distinct_open_branches: int
    avg_dup_rate: float
    avg_novel_claims: float
    parent_claim_ids: list[str]
    note: str


def detect_branch_explosion(trajectory: Trajectory) -> BranchExplosionReport:
    """Detect branch-explosion shape: many open branches + low dup + high novel."""
    distinct_open: set[str] = set()
    parents: set[str] = set()
    for step in trajectory.steps:
        for c in step.claims:
            if c.branch_open:
                distinct_open.add(c.id)
                if c.parent_id:
                    parents.add(c.parent_id)
    n_steps = max(1, len(trajectory.steps))
    avg_dup = sum(s.dup_rate for s in trajectory.steps) / n_steps
    avg_novel = sum(s.novel_claims for s in trajectory.steps) / n_steps
    detected = (
        len(distinct_open) >= BRANCH_EXPLOSION_MIN_BRANCHES
        and avg_dup < BRANCH_EXPLOSION_MAX_AVG_DUP
        and avg_novel >= BRANCH_EXPLOSION_MIN_AVG_NOVEL
    )
    if detected:
        note = (
            f"distinct open branches={len(distinct_open)} (>=5) "
            f"avg_dup_rate={avg_dup:.2f} (<0.20) "
            f"avg_novel_claims={avg_novel:.1f} (>=5)"
        )
    else:
        note = (
            f"no branch explosion: "
            f"distinct_open={len(distinct_open)}, "
            f"avg_dup={avg_dup:.2f}, "
            f"avg_novel={avg_novel:.1f}"
        )
    return BranchExplosionReport(
        detected=detected,
        distinct_open_branches=len(distinct_open),
        avg_dup_rate=round(avg_dup, 3),
        avg_novel_claims=round(avg_novel, 2),
        parent_claim_ids=sorted(parents),
        note=note,
    )


# --- Mild-stagnation detector (cycle 5) -----------------------------------
#
# Closes DET-FAL T4 (paper0/self_reflection.md §6.2 / §4.2). Mild stagnation
# is a *soft* convergence signal designed to coexist with Phase V: it fires
# only when Phase V's hard trigger never fires anywhere in the trajectory.

MILD_STAGNATION_TAIL = 5
MILD_STAGNATION_MAX_AVG_NOVEL = 2.5


@dataclass(frozen=True)
class MildStagnationReport:
    detected: bool
    tail_loops: int
    tail_mean_novel: float
    dup_strictly_increasing: bool
    has_phase_v_trigger: bool
    has_genuine_en_in_tail: bool
    note: str


def detect_mild_stagnation(trajectory: Trajectory) -> MildStagnationReport:
    """Soft convergence: tail-window mean(novel) <= tau + dup rising, *only*
    when no Phase V hard trigger fires anywhere in the trajectory."""
    steps = sorted(trajectory.steps, key=lambda s: s.loop_index)
    if not steps:
        return MildStagnationReport(
            detected=False, tail_loops=0, tail_mean_novel=0.0,
            dup_strictly_increasing=False, has_phase_v_trigger=False,
            has_genuine_en_in_tail=False, note="empty trajectory",
        )
    has_phase_v = any(s.dup_rate > 0.50 and s.novel_claims <= 1 for s in steps)
    tail = steps[-MILD_STAGNATION_TAIL:] if len(steps) >= MILD_STAGNATION_TAIL else steps[:]
    if len(tail) < 3:
        return MildStagnationReport(
            detected=False, tail_loops=len(tail), tail_mean_novel=0.0,
            dup_strictly_increasing=False, has_phase_v_trigger=has_phase_v,
            has_genuine_en_in_tail=False,
            note=f"tail too short (len={len(tail)})",
        )
    mean_novel = sum(s.novel_claims for s in tail) / len(tail)
    dup_rates = [s.dup_rate for s in tail]
    strictly_increasing = all(b > a for a, b in zip(dup_rates, dup_rates[1:]))
    tail_loop_set = {s.loop_index for s in tail}
    has_genuine_en_in_tail = any(
        classify_en_event(e).label == "genuine_transformation"
        and e.loop_index in tail_loop_set
        for e in trajectory.en_events
    )
    detected = (
        not has_phase_v
        and mean_novel <= MILD_STAGNATION_MAX_AVG_NOVEL
        and strictly_increasing
        and not has_genuine_en_in_tail
    )
    if detected:
        note = (
            f"mild stagnation in tail of {len(tail)} loops: "
            f"mean_novel={mean_novel:.2f} (<= {MILD_STAGNATION_MAX_AVG_NOVEL}), "
            f"dup strictly increasing, no genuine EN, no Phase V hard trigger"
        )
    else:
        reasons = []
        if has_phase_v:
            reasons.append("Phase V hard trigger fires (use Phase V instead)")
        if mean_novel > MILD_STAGNATION_MAX_AVG_NOVEL:
            reasons.append(f"tail mean novel={mean_novel:.2f} too high")
        if not strictly_increasing:
            reasons.append("dup not strictly increasing in tail")
        if has_genuine_en_in_tail:
            reasons.append("genuine EN in tail")
        note = "no mild stagnation: " + "; ".join(reasons) if reasons else "no mild stagnation"
    return MildStagnationReport(
        detected=detected, tail_loops=len(tail),
        tail_mean_novel=round(mean_novel, 2),
        dup_strictly_increasing=strictly_increasing,
        has_phase_v_trigger=has_phase_v,
        has_genuine_en_in_tail=has_genuine_en_in_tail,
        note=note,
    )


# --- Convenience aggregator -------------------------------------------------


@dataclass(frozen=True)
class DeterministicMetrics:
    trajectory_id: str
    n_steps: int
    n_en_events: int
    en_classifications: list[ENClassification]
    novelty_recoveries: list[NoveltyRecovery]
    penultimate: PenultimateENAssessment
    attractor: TerminalAttractorReport
    failure: FailureModeSummary
    branch_explosion: BranchExplosionReport
    mild_stagnation: MildStagnationReport


def compute_all(trajectory: Trajectory) -> DeterministicMetrics:
    return DeterministicMetrics(
        trajectory_id=trajectory.trajectory_id,
        n_steps=len(trajectory.steps),
        n_en_events=len(trajectory.en_events),
        en_classifications=classify_en_events(trajectory.en_events),
        novelty_recoveries=[compute_novelty_recovery(e) for e in trajectory.en_events],
        penultimate=detect_penultimate_en_candidate(trajectory),
        attractor=detect_terminal_attractor_subjects(trajectory),
        failure=summarize_failure_mode(trajectory),
        branch_explosion=detect_branch_explosion(trajectory),
        mild_stagnation=detect_mild_stagnation(trajectory),
    )
