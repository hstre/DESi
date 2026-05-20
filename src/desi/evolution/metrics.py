"""PathQualityMetrics — deterministic raw metrics per evaluation.

v0.6 introduces the metric *interface* but no statistical tests, no
significance bounds, no comparisons. The point in this release is
that every promotion candidate carries a stable, reproducible vector
of raw counts that v0.7 can build deltas / significance tests on top
of without further changes to the producer code.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..eval import EvaluationResult


@dataclass(frozen=True)
class PathQualityMetrics:
    """Raw, deterministic per-run metrics.

    The first six fields are integer counts derived directly from the
    evaluation result's timeline and end-state snapshot. Identical
    input + identical seed yields identical metrics (tested).

    v0.9 adds three signature fields so two runs over the same
    scenario can be compared by *path*, not just by count:

    * ``unique_claim_order_hash`` — 16-char hash of the ordered list of
      newly-introduced claim_ids over the run.
    * ``branch_signature`` — 16-char hash of the ordered list of
      ``(focus_claim_id, evidence, threshold)`` triples on every
      BRANCH_OPENED event. Two runs with identical branch decisions
      share this signature; two runs that opened different branches
      do not.
    * ``merge_signature`` — 16-char hash of the ordered list of
      ``(source, target)`` pairs on every MERGED_INTO relation in
      the end snapshot.

    These fields default to ``""`` so v0.7 / v0.8 constructors that
    pass only the original six counts keep working unchanged.
    """

    scenario_id: str
    timeline_length: int
    branch_opened_count: int
    guard_blocked_count: int
    contradicts_count: int
    merged_into_count: int
    hook_error_count: int
    # v0.9: structural signatures
    unique_claim_order_hash: str = ""
    branch_signature: str = ""
    merge_signature: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "timeline_length": self.timeline_length,
            "branch_opened_count": self.branch_opened_count,
            "guard_blocked_count": self.guard_blocked_count,
            "contradicts_count": self.contradicts_count,
            "merged_into_count": self.merged_into_count,
            "hook_error_count": self.hook_error_count,
            "unique_claim_order_hash": self.unique_claim_order_hash,
            "branch_signature": self.branch_signature,
            "merge_signature": self.merge_signature,
        }


def _short_hash(payload: Any) -> str:
    import hashlib
    raw = repr(payload).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def compute_path_quality(result: EvaluationResult) -> PathQualityMetrics:
    """Extract :class:`PathQualityMetrics` from one evaluation result."""
    branch_opened = sum(
        1 for e in result.timeline
        if e.event_type.value == "branch_opened"
    )
    guard_blocked = sum(
        1 for e in result.timeline
        if e.event_type.value == "guard_blocked"
    )
    end_snap = next(
        (s for s in result.snapshots if s.label == "end"),
        None,
    )
    if end_snap is None:
        contradicts = 0
        merged_into = 0
        merge_pairs: tuple = ()
    else:
        contradicts = sum(
            1 for r in end_snap.relations
            if r.get("rel_type") == "CONTRADICTS"
        )
        merged_into = sum(
            1 for r in end_snap.relations
            if r.get("rel_type") == "MERGED_INTO"
        )
        merge_pairs = tuple(
            (r.get("source"), r.get("target"))
            for r in end_snap.relations
            if r.get("rel_type") == "MERGED_INTO"
        )
    # v0.9 signatures.
    claim_order = tuple(
        e.payload.get("claim_id")
        for e in result.timeline
        if e.event_type.value == "claim_created"
    )
    branch_triples = tuple(
        (
            e.payload.get("focus_claim_id"),
            round(float(e.payload.get("evidence", 0.0)), 4),
            round(float(e.payload.get("threshold", 0.0)), 4),
        )
        for e in result.timeline
        if e.event_type.value == "branch_opened"
    )
    return PathQualityMetrics(
        scenario_id=result.scenario_id,
        timeline_length=len(result.timeline),
        branch_opened_count=branch_opened,
        guard_blocked_count=guard_blocked,
        contradicts_count=contradicts,
        merged_into_count=merged_into,
        hook_error_count=len(result.hook_errors),
        unique_claim_order_hash=_short_hash(claim_order),
        branch_signature=_short_hash(branch_triples),
        merge_signature=_short_hash(merge_pairs),
    )


__all__ = [
    "MetricsDelta",
    "PathQualityMetrics",
    "compute_path_quality",
]


# ---------------------------------------------------------------------------
# v0.7: clone-vs-stable delta
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MetricsDelta:
    """Difference between a stable run and a clone run on the same scenario.

    Absolute deltas are computed as ``clone_value - stable_value`` so
    that a *reduction* in a counter shows up as a negative integer.
    Convention: a negative ``branch_opened_delta`` is *good* (the
    clone produced fewer branches).

    The :attr:`verdict` aggregates the six absolute deltas into one
    of three coarse labels:

    * ``improved``  — at least one favourable absolute delta and no
                       unfavourable one (regression cannot be hidden)
    * ``regressed`` — at least one unfavourable absolute delta
                       (regressions dominate, even with offsets)
    * ``neutral``   — every absolute delta is exactly zero

    Favourable directions:

    * fewer branches opened
    * fewer guard blocks (a guard that fired on stable would block
      promotion via the v0.5 gate; if the clone still triggers it,
      it has not improved)
    * shorter timeline
    * fewer or equal hook errors
    * contradicts / merged_into counts: change is treated as
      *behavioural drift*, not improvement. The Skeptiker veto-path
      catches drift on these.
    """

    stable: PathQualityMetrics
    clone: PathQualityMetrics

    # Absolute deltas (clone - stable). Negative is reduction.
    @property
    def timeline_length_delta(self) -> int:
        return self.clone.timeline_length - self.stable.timeline_length

    @property
    def branch_opened_delta(self) -> int:
        return self.clone.branch_opened_count - self.stable.branch_opened_count

    @property
    def guard_blocked_delta(self) -> int:
        return self.clone.guard_blocked_count - self.stable.guard_blocked_count

    @property
    def contradicts_delta(self) -> int:
        return self.clone.contradicts_count - self.stable.contradicts_count

    @property
    def merged_into_delta(self) -> int:
        return self.clone.merged_into_count - self.stable.merged_into_count

    @property
    def hook_error_delta(self) -> int:
        return self.clone.hook_error_count - self.stable.hook_error_count

    # Relative deltas, expressed as percentages of the stable baseline.
    @property
    def branch_reduction_pct(self) -> float:
        return _pct_reduction(self.stable.branch_opened_count,
                              self.clone.branch_opened_count)

    @property
    def timeline_reduction_pct(self) -> float:
        return _pct_reduction(self.stable.timeline_length,
                              self.clone.timeline_length)

    # Verdict.
    @property
    def verdict(self) -> str:
        """Three-state assessment.

        v0.7 rules:

        * fewer branches opened              → favourable
        * fewer hook errors                  → favourable
        * shorter timeline                   → favourable (modulo
                                                guard-blocked, which
                                                adds events)
        * more hook errors                   → unfavourable
        * any change to CONTRADICTS count    → unfavourable (drift)
        * any change to MERGED_INTO count    → unfavourable (drift)

        ``guard_blocked_delta`` is treated as **neutral** in v0.7: the
        one active knob (``branch_open_evidence_min``) generates
        guard-blocked events as its mechanism of action. Counting
        those as regressions would mark every working mutation as a
        regression. v0.8 may revisit this when more than one guard is
        config-effective.

        Timeline-length changes that are *exactly explained* by the
        branch / guard delta are also treated as neutral, so that the
        verdict reflects the substantive epistemic delta rather than
        bookkeeping events the v0.7 mechanism is known to produce.
        """
        unfavourable = False
        favourable = False
        if self.branch_opened_delta < 0:
            favourable = True
        elif self.branch_opened_delta > 0:
            unfavourable = True
        if self.hook_error_delta > 0:
            unfavourable = True
        elif self.hook_error_delta < 0:
            favourable = True
        if self.contradicts_delta != 0:
            unfavourable = True
        if self.merged_into_delta != 0:
            unfavourable = True
        # Timeline-length drift attributable to (branch-open + guard-
        # blocked) accounting is neutral. Each branch suppression in
        # v0.7 substitutes one BRANCH_OPENED for one GUARD_BLOCKED;
        # the net timeline delta from that exchange is zero. Larger
        # timeline drifts NOT explained by guard/branch swaps are
        # treated as unfavourable.
        net_event_swap = (
            self.branch_opened_delta + self.guard_blocked_delta
        )
        explained_timeline = self.timeline_length_delta - net_event_swap
        if explained_timeline > 0:
            unfavourable = True
        elif explained_timeline < 0:
            favourable = True

        if unfavourable:
            return "regressed"
        if favourable:
            return "improved"
        return "neutral"

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.stable.scenario_id,
            "stable": self.stable.to_dict(),
            "clone": self.clone.to_dict(),
            "absolute": {
                "timeline_length_delta": self.timeline_length_delta,
                "branch_opened_delta": self.branch_opened_delta,
                "guard_blocked_delta": self.guard_blocked_delta,
                "contradicts_delta": self.contradicts_delta,
                "merged_into_delta": self.merged_into_delta,
                "hook_error_delta": self.hook_error_delta,
            },
            "relative": {
                "branch_reduction_pct": self.branch_reduction_pct,
                "timeline_reduction_pct": self.timeline_reduction_pct,
            },
            "verdict": self.verdict,
        }


def _pct_reduction(stable_value: int, clone_value: int) -> float:
    """Percent reduction from stable to clone.

    Positive means clone is smaller than stable (good). Returns 0.0
    when ``stable_value`` is zero (no baseline to compare against).
    """
    if stable_value == 0:
        return 0.0
    return 100.0 * (stable_value - clone_value) / stable_value
