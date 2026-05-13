"""Deterministic DESi diagnostics. No LLM calls live here."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .models import ENEvent, Trajectory


ENI_LOW_THRESHOLD = 0.10
ENI_HIGH_THRESHOLD = 0.12


@dataclass(frozen=True)
class ENClassification:
    loop_index: int
    eni_novelty: float
    label: str


def classify_en_event(event: ENEvent) -> ENClassification:
    eni = event.eni_novelty
    if eni < ENI_LOW_THRESHOLD:
        label = "local_variation_or_false_return"
    elif eni > ENI_HIGH_THRESHOLD:
        label = "genuine_transformation"
    else:
        label = "borderline"
    return ENClassification(loop_index=event.loop_index, eni_novelty=eni, label=label)


def classify_en_events(events: Iterable[ENEvent]) -> list[ENClassification]:
    return [classify_en_event(e) for e in events]


@dataclass(frozen=True)
class NoveltyRecovery:
    loop_index: int
    dup_delta: float | None
    novel_claims_next: int | None
    recovered: bool


def compute_novelty_recovery(event: ENEvent) -> NoveltyRecovery:
    dup_delta: float | None
    if event.dup_rate_before is not None and event.dup_rate_after is not None:
        dup_delta = event.dup_rate_after - event.dup_rate_before
    else:
        dup_delta = None
    nc_next = event.novel_claims_next
    recovered = (
        dup_delta is not None and dup_delta <= -0.10
        and nc_next is not None and nc_next >= 1
    )
    return NoveltyRecovery(
        loop_index=event.loop_index, dup_delta=dup_delta,
        novel_claims_next=nc_next, recovered=recovered,
    )


@dataclass(frozen=True)
class CompositeENClassification:
    loop_index: int
    eni_novelty: float
    recovered: bool
    label: str
    note: str


def classify_en_event_composite(event: ENEvent) -> CompositeENClassification:
    recovery = compute_novelty_recovery(event)
    eni = event.eni_novelty
    if eni > ENI_HIGH_THRESHOLD:
        bucket = "high"
    elif eni < ENI_LOW_THRESHOLD:
        bucket = "low"
    else:
        bucket = "borderline"
    if bucket == "high" and recovery.recovered:
        label = "genuine_transformation_confirmed"
    elif bucket == "high" and not recovery.recovered:
        label = "genuine_transformation_unconfirmed"
    elif bucket == "borderline" and recovery.recovered:
        label = "borderline_with_recovery"
    elif bucket == "borderline" and not recovery.recovered:
        label = "borderline_no_recovery"
    elif bucket == "low" and recovery.recovered:
        label = "low_eni_with_unexpected_recovery"
    else:
        label = "false_return_confirmed"
    note = f"eni_novelty={eni:.2f} bucket={bucket} recovered={recovery.recovered}"
    return CompositeENClassification(
        loop_index=event.loop_index, eni_novelty=eni,
        recovered=recovery.recovered, label=label, note=note,
    )


def classify_en_events_composite(events: Iterable[ENEvent]) -> list[CompositeENClassification]:
    return [classify_en_event_composite(e) for e in events]


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
            has_candidate=False, penultimate_loop=None, penultimate_label=None,
            last_loop=None, last_label=None,
            note="fewer than 2 EN events; principle not applicable",
        )
    composite = classify_en_events_composite(events)
    penult = composite[-2]
    last = composite[-1]
    is_candidate = (
        penult.label == "genuine_transformation_confirmed"
        and last.label != "genuine_transformation_confirmed"
    )
    note = (
        "penultimate EN was the last *confirmed* genuine transformation "
        "(high ENI + downstream recovery)"
        if is_candidate
        else f"penultimate EN does not match the principle's signature (penultimate label = {penult.label})"
    )
    return PenultimateENAssessment(
        has_candidate=is_candidate,
        penultimate_loop=penult.loop_index, penultimate_label=penult.label,
        last_loop=last.loop_index, last_label=last.label, note=note,
    )


@dataclass(frozen=True)
class TerminalAttractorReport:
    candidate_claim_ids: list[str]
    method: str
    note: str


# Cycle 1 (generalization loop): tail-saturation guard.
# Cycle 4 (generalization loop): strict-> on the dup boundary.
ATTRACTOR_TAIL_MAX_MEAN_NOVEL = 3.0
ATTRACTOR_TAIL_MIN_MEAN_DUP = 0.30


def detect_terminal_attractor_subjects(trajectory: Trajectory, *, tail_loops: int = 3) -> TerminalAttractorReport:
    steps = trajectory.steps[-tail_loops:]
    if not steps:
        return TerminalAttractorReport(candidate_claim_ids=[], method="tail_focus_repetition", note="trajectory has no steps")
    mean_novel = sum(s.novel_claims for s in steps) / len(steps)
    mean_dup = sum(s.dup_rate for s in steps) / len(steps)
    saturated = (
        mean_novel <= ATTRACTOR_TAIL_MAX_MEAN_NOVEL
        and mean_dup > ATTRACTOR_TAIL_MIN_MEAN_DUP
    )
    if not saturated:
        return TerminalAttractorReport(
            candidate_claim_ids=[], method="tail_focus_repetition_guarded",
            note=(
                f"tail not saturated: mean_novel={mean_novel:.1f} (>{ATTRACTOR_TAIL_MAX_MEAN_NOVEL}) "
                f"OR mean_dup={mean_dup:.2f} (<{ATTRACTOR_TAIL_MIN_MEAN_DUP})"
            ),
        )
    focus_counts: dict[str, int] = {}
    presence_counts: dict[str, int] = {}
    for step in steps:
        if step.focus_claim_id:
            focus_counts[step.focus_claim_id] = focus_counts.get(step.focus_claim_id, 0) + 1
        for claim in step.claims:
            presence_counts[claim.claim_id] = presence_counts.get(claim.claim_id, 0) + 1
    candidates = sorted(
        {cid for cid, n in focus_counts.items() if n >= 2}
        | {cid for cid, n in presence_counts.items() if n == len(steps) and n >= 2}
    )
    return TerminalAttractorReport(
        candidate_claim_ids=candidates, method="tail_focus_repetition_guarded",
        note=(
            f"tail saturated (mean_novel={mean_novel:.1f}, mean_dup={mean_dup:.2f}); "
            f"candidate = focus repeated twice OR claim present in every tail step"
        ),
    )


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
        if trajectory.terminal_failure_mode is not None else None
    )
    return FailureModeSummary(terminal=terminal, per_step=per_step)


BRANCH_EXPLOSION_MIN_BRANCHES = 5
BRANCH_EXPLOSION_MAX_AVG_DUP = 0.20
BRANCH_EXPLOSION_MIN_AVG_NOVEL = 5.0
BRANCH_EXPLOSION_TAIL = 3  # gen-cycle 3


@dataclass(frozen=True)
class BranchExplosionReport:
    detected: bool
    distinct_open_branches: int
    avg_dup_rate: float
    avg_novel_claims: float
    parent_claim_ids: list[str]
    note: str


def detect_branch_explosion(trajectory: Trajectory) -> BranchExplosionReport:
    distinct_open: set[str] = set()
    parents: set[str] = set()
    for step in trajectory.steps:
        for c in step.claims:
            if c.branch_open:
                distinct_open.add(c.id)
                if c.parent_id:
                    parents.add(c.parent_id)
    sorted_steps = sorted(trajectory.steps, key=lambda s: s.loop_index)
    tail = sorted_steps[-BRANCH_EXPLOSION_TAIL:] if sorted_steps else []
    n_tail = max(1, len(tail))
    avg_dup = sum(s.dup_rate for s in tail) / n_tail if tail else 0.0
    avg_novel = sum(s.novel_claims for s in tail) / n_tail if tail else 0.0
    detected = (
        len(distinct_open) >= BRANCH_EXPLOSION_MIN_BRANCHES
        and avg_dup < BRANCH_EXPLOSION_MAX_AVG_DUP
        and avg_novel >= BRANCH_EXPLOSION_MIN_AVG_NOVEL
    )
    if detected:
        note = (
            f"distinct open branches={len(distinct_open)} (>=5) "
            f"tail-{BRANCH_EXPLOSION_TAIL} avg_dup={avg_dup:.2f} (<0.20) "
            f"tail-{BRANCH_EXPLOSION_TAIL} avg_novel={avg_novel:.1f} (>=5)"
        )
    else:
        note = (
            f"no branch explosion: distinct_open={len(distinct_open)}, "
            f"tail-{BRANCH_EXPLOSION_TAIL} avg_dup={avg_dup:.2f}, "
            f"tail-{BRANCH_EXPLOSION_TAIL} avg_novel={avg_novel:.1f}"
        )
    return BranchExplosionReport(
        detected=detected, distinct_open_branches=len(distinct_open),
        avg_dup_rate=round(avg_dup, 3), avg_novel_claims=round(avg_novel, 2),
        parent_claim_ids=sorted(parents), note=note,
    )


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
            has_genuine_en_in_tail=False, note=f"tail too short (len={len(tail)})",
        )
    mean_novel = sum(s.novel_claims for s in tail) / len(tail)
    dup_rates = [s.dup_rate for s in tail]
    strictly_increasing = all(b > a for a, b in zip(dup_rates, dup_rates[1:]))
    tail_loop_set = {s.loop_index for s in tail}
    has_genuine_en_in_tail = any(
        classify_en_event(e).label == "genuine_transformation"
        and e.loop_index in tail_loop_set for e in trajectory.en_events
    )
    detected = (
        not has_phase_v and mean_novel <= MILD_STAGNATION_MAX_AVG_NOVEL
        and strictly_increasing and not has_genuine_en_in_tail
    )
    if detected:
        note = f"mild stagnation in tail of {len(tail)} loops: mean_novel={mean_novel:.2f} (<= {MILD_STAGNATION_MAX_AVG_NOVEL}), dup strictly increasing, no genuine EN, no Phase V hard trigger"
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
        detected=detected, tail_loops=len(tail), tail_mean_novel=round(mean_novel, 2),
        dup_strictly_increasing=strictly_increasing, has_phase_v_trigger=has_phase_v,
        has_genuine_en_in_tail=has_genuine_en_in_tail, note=note,
    )


# --- Borderline-EN chain detector (generalization-loop cycle 5) ------------
BORDERLINE_CHAIN_MIN_RUN = 3


@dataclass(frozen=True)
class BorderlineChainReport:
    detected: bool
    longest_run: int
    run_start_loop: int | None
    run_end_loop: int | None
    note: str


def detect_borderline_chain(trajectory: Trajectory) -> BorderlineChainReport:
    events = sorted(trajectory.en_events, key=lambda e: e.loop_index)
    if not events:
        return BorderlineChainReport(
            detected=False, longest_run=0, run_start_loop=None, run_end_loop=None,
            note="no EN events",
        )
    longest = 0
    cur = 0
    best_start: int | None = None
    best_end: int | None = None
    cur_start: int | None = None
    for e in events:
        cls = classify_en_event(e)
        if cls.label == "borderline":
            cur += 1
            if cur_start is None:
                cur_start = e.loop_index
            if cur > longest:
                longest = cur
                best_start = cur_start
                best_end = e.loop_index
        else:
            cur = 0
            cur_start = None
    detected = longest >= BORDERLINE_CHAIN_MIN_RUN
    note = (
        f"borderline chain length {longest} at loops {best_start}..{best_end}"
        if detected
        else f"longest borderline run = {longest} (< {BORDERLINE_CHAIN_MIN_RUN})"
    )
    return BorderlineChainReport(
        detected=detected, longest_run=longest,
        run_start_loop=best_start, run_end_loop=best_end, note=note,
    )


@dataclass(frozen=True)
class IncoherentStep:
    loop_index: int
    reason: str


@dataclass(frozen=True)
class StepCoherenceReport:
    detected: bool
    incoherent_steps: list[IncoherentStep]
    note: str


def validate_step_metric_coherence(trajectory: Trajectory) -> StepCoherenceReport:
    incoherent: list[IncoherentStep] = []
    sorted_steps = sorted(trajectory.steps, key=lambda s: s.loop_index)
    for i, s in enumerate(sorted_steps):
        reasons: list[str] = []
        if s.dup_rate > 0.70 and s.novel_claims >= 5:
            reasons.append(
                f"dup_rate={s.dup_rate:.2f}>0.70 AND novel_claims={s.novel_claims}>=5 (heavy duplication + many novel claims is contradictory)"
            )
        if i > 0 and s.dup_rate < 0.05 and s.novel_claims == 0:
            reasons.append(
                f"dup_rate={s.dup_rate:.2f}<0.05 AND novel_claims=0 (no exploration and no duplication after loop 0 is impossible)"
            )
        if reasons:
            incoherent.append(IncoherentStep(loop_index=s.loop_index, reason="; ".join(reasons)))
    detected = bool(incoherent)
    if detected:
        note = f"{len(incoherent)} incoherent step(s) at loops {[s.loop_index for s in incoherent]}; LLM roles should refuse to interpret these steps"
    else:
        note = "all steps coherent"
    return StepCoherenceReport(detected=detected, incoherent_steps=incoherent, note=note)


@dataclass(frozen=True)
class DeterministicMetrics:
    trajectory_id: str
    n_steps: int
    n_en_events: int
    en_classifications: list[ENClassification]
    en_classifications_composite: list[CompositeENClassification]
    novelty_recoveries: list[NoveltyRecovery]
    penultimate: PenultimateENAssessment
    attractor: TerminalAttractorReport
    failure: FailureModeSummary
    branch_explosion: BranchExplosionReport
    mild_stagnation: MildStagnationReport
    step_coherence: StepCoherenceReport
    borderline_chain: BorderlineChainReport


def compute_all(trajectory: Trajectory) -> DeterministicMetrics:
    return DeterministicMetrics(
        trajectory_id=trajectory.trajectory_id,
        n_steps=len(trajectory.steps),
        n_en_events=len(trajectory.en_events),
        en_classifications=classify_en_events(trajectory.en_events),
        en_classifications_composite=classify_en_events_composite(trajectory.en_events),
        novelty_recoveries=[compute_novelty_recovery(e) for e in trajectory.en_events],
        penultimate=detect_penultimate_en_candidate(trajectory),
        attractor=detect_terminal_attractor_subjects(trajectory),
        failure=summarize_failure_mode(trajectory),
        branch_explosion=detect_branch_explosion(trajectory),
        mild_stagnation=detect_mild_stagnation(trajectory),
        step_coherence=validate_step_metric_coherence(trajectory),
        borderline_chain=detect_borderline_chain(trajectory),
    )
