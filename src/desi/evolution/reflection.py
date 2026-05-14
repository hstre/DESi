"""ReflectionEngine — post-evaluation self-analysis of a DESi run.

Given an :class:`EvaluationResult`, the engine walks the timeline and
the end-state graph and emits a :class:`ReflectionReport` listing
observable performance and quality concerns. No mutation is performed
here; the report is diagnosis only.

The set of detectors is intentionally narrow and deterministic. Adding
a detector requires a code change so that downstream governance
(jury, promotion) sees a stable taxonomy of findings.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..eval import EvaluationResult


# ---------------------------------------------------------------------------
# Report types
# ---------------------------------------------------------------------------


class ReflectionFinding(BaseModel):
    """One concrete observation extracted from a run."""

    model_config = ConfigDict(extra="forbid")

    category: str = Field(
        ..., description="One of: performance / quality / safety.",
    )
    observed_problem: str = Field(..., min_length=1)
    suspected_root_cause: str = Field(..., min_length=1)
    affected_components: tuple[str, ...] = Field(default_factory=tuple)
    confidence: float = Field(..., ge=0.0, le=1.0)
    supporting_events: tuple[int, ...] = Field(
        default_factory=tuple,
        description="Timeline ticks that support this finding.",
    )


class ReflectionReport(BaseModel):
    """Outcome of a single reflection pass."""

    model_config = ConfigDict(extra="forbid")

    evaluation_id: str = Field(..., min_length=1)
    scenario_id: str = Field(..., min_length=1)
    findings: tuple[ReflectionFinding, ...] = Field(default_factory=tuple)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @property
    def has_findings(self) -> bool:
        return len(self.findings) > 0


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class ReflectionEngine:
    """Walks an EvaluationResult and emits a ReflectionReport.

    Thresholds are explicit attributes so that downstream governance
    can audit *why* a finding was raised.
    """

    # Path-quality thresholds. Values are deliberate, modest defaults.
    MAX_BRANCHES_BEFORE_CONCERN: int = 4
    MAX_REVISIONS_PER_CLAIM: int = 2
    LATE_GUARD_TICK_PERCENTILE: float = 0.75
    DEAD_END_MIN_TICKS_SINCE_LAST_REF: int = 6

    def reflect(self, result: EvaluationResult) -> ReflectionReport:
        findings: list[ReflectionFinding] = []
        findings.extend(self._unnecessary_branches(result))
        findings.extend(self._repeated_revisions(result))
        findings.extend(self._dead_end_claims(result))
        findings.extend(self._late_guard_triggers(result))
        findings.extend(self._unstable_path(result))
        findings.extend(self._unresolved_conflicts(result))
        return ReflectionReport(
            evaluation_id=result.evaluation_id,
            scenario_id=result.scenario_id,
            findings=tuple(findings),
        )

    # ------------------------------------------------------------------
    # Detectors
    # ------------------------------------------------------------------

    def _unnecessary_branches(
        self, result: EvaluationResult,
    ) -> list[ReflectionFinding]:
        opens = [e for e in result.timeline
                 if e.event_type.value == "branch_opened"]
        if len(opens) <= self.MAX_BRANCHES_BEFORE_CONCERN:
            return []
        return [ReflectionFinding(
            category="performance",
            observed_problem=(
                f"{len(opens)} branches opened in a single run, exceeding "
                f"the configured threshold of "
                f"{self.MAX_BRANCHES_BEFORE_CONCERN}."
            ),
            suspected_root_cause=(
                "branch-opening heuristic does not penalise low-evidence "
                "focus shifts; new focus_claim_ids open a branch even when "
                "the previous branch had no closing condition."
            ),
            affected_components=("branch_heuristics", "operator_ordering"),
            confidence=0.6,
            supporting_events=tuple(e.tick for e in opens),
        )]

    def _repeated_revisions(
        self, result: EvaluationResult,
    ) -> list[ReflectionFinding]:
        revisions = [e for e in result.timeline
                     if e.event_type.value == "claim_revised"]
        c: Counter[str] = Counter()
        for e in revisions:
            cid = e.payload.get("claim_id")
            if cid is not None:
                c[str(cid)] += 1
        offenders = {cid: n for cid, n in c.items()
                     if n > self.MAX_REVISIONS_PER_CLAIM}
        if not offenders:
            return []
        ticks = tuple(e.tick for e in revisions
                      if str(e.payload.get("claim_id")) in offenders)
        return [ReflectionFinding(
            category="quality",
            observed_problem=(
                f"claim(s) revised more than "
                f"{self.MAX_REVISIONS_PER_CLAIM} times: "
                f"{sorted(offenders.items())}"
            ),
            suspected_root_cause=(
                "claim acceptance threshold is too permissive; revisions "
                "are being treated as routine instead of as evidence of "
                "an unresolved conflict."
            ),
            affected_components=("guard_thresholds", "merge_policy"),
            confidence=0.55,
            supporting_events=ticks,
        )]

    def _dead_end_claims(
        self, result: EvaluationResult,
    ) -> list[ReflectionFinding]:
        end_snap = next((s for s in result.snapshots if s.label == "end"),
                        None)
        if end_snap is None or not end_snap.claims:
            return []
        # A claim is a dead end if it never appears as the source or
        # target of any relation in the end snapshot.
        related: set[str] = set()
        for rel in end_snap.relations:
            related.add(rel.get("source_claim_id", ""))
            related.add(rel.get("target_claim_id", ""))
        dead = [c["claim_id"] for c in end_snap.claims
                if c["claim_id"] not in related]
        if not dead:
            return []
        return [ReflectionFinding(
            category="quality",
            observed_problem=(
                f"{len(dead)} claim(s) ended the run with no incoming or "
                f"outgoing relations: {sorted(dead)}"
            ),
            suspected_root_cause=(
                "claims were created but never connected to the rest of "
                "the graph; the run produced isolated artifacts."
            ),
            affected_components=("diagnostics", "branch_heuristics"),
            confidence=0.4,
            supporting_events=(),
        )]

    def _late_guard_triggers(
        self, result: EvaluationResult,
    ) -> list[ReflectionFinding]:
        if not result.timeline:
            return []
        last_tick = max(e.tick for e in result.timeline)
        late_cutoff = last_tick * self.LATE_GUARD_TICK_PERCENTILE
        guards = [e for e in result.timeline
                  if e.event_type.value in ("guard_blocked", "guard_passed")]
        late = [e for e in guards if e.tick >= late_cutoff]
        if not late:
            return []
        return [ReflectionFinding(
            category="performance",
            observed_problem=(
                f"{len(late)} guard event(s) fired in the final "
                f"{int((1 - self.LATE_GUARD_TICK_PERCENTILE) * 100)}% "
                "of the timeline."
            ),
            suspected_root_cause=(
                "guards are evaluated after the operator chain commits "
                "its decision; an earlier evaluation pass could short-"
                "circuit the late firings."
            ),
            affected_components=("guard_thresholds", "operator_ordering"),
            confidence=0.5,
            supporting_events=tuple(e.tick for e in late),
        )]

    def _unstable_path(
        self, result: EvaluationResult,
    ) -> list[ReflectionFinding]:
        # Heuristic: many operator switches between different operators
        # in a short window suggests an unstable path.
        ops = [str(e.payload.get("operator"))
               for e in result.timeline
               if e.event_type.value == "operator_started"]
        switches = sum(1 for a, b in zip(ops, ops[1:]) if a != b)
        if len(ops) < 4 or switches < max(2, len(ops) - 2):
            return []
        return [ReflectionFinding(
            category="quality",
            observed_problem=(
                f"high operator-switch rate: {switches}/{len(ops) - 1} "
                "consecutive operator pairs differ."
            ),
            suspected_root_cause=(
                "operator selection oscillates between phases; a "
                "stronger commitment heuristic could reduce churn."
            ),
            affected_components=("operator_ordering",),
            confidence=0.45,
            supporting_events=(),
        )]

    def _unresolved_conflicts(
        self, result: EvaluationResult,
    ) -> list[ReflectionFinding]:
        end_snap = next((s for s in result.snapshots if s.label == "end"),
                        None)
        if end_snap is None:
            return []
        contradicts = [r for r in end_snap.relations
                       if r.get("rel_type") == "CONTRADICTS"]
        # An odd count of CONTRADICTS suggests a one-directional
        # contradiction was emitted without its mirror — that is a
        # quality concern because contradiction is symmetric in v0.2's
        # relation taxonomy when both sides are known.
        if not contradicts or len(contradicts) % 2 == 0:
            return []
        return [ReflectionFinding(
            category="quality",
            observed_problem=(
                f"{len(contradicts)} CONTRADICTS edges present in the "
                "end-state graph; expected an even number (bidirectional)."
            ),
            suspected_root_cause=(
                "contradiction was recorded only in one direction; "
                "mirror edge missing."
            ),
            affected_components=("merge_policy", "diagnostics"),
            confidence=0.35,
            supporting_events=(),
        )]
