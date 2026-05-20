"""DelphiJury — five deterministic role-based reviewers.

v0.5 explicitly forbids real LLM-API calls. The "jury members" are
therefore deterministic, rule-based reviewers that play five distinct
roles: Replikator, Skeptiker, Methodiker, Adversarial Reviewer, and
Integrator. Each role reads the same inputs (proposal, evaluation
report, reflection report) and produces a structured review +
final vote.

Two-round protocol per the directive:

1. Independent first-round reviews. No member sees the others'
   output.
2. Delphi-round: every member receives the round-1 reviews and casts
   a final vote (APPROVE / REVISE / VETO).

A veto is valid only if it carries claim, risk, failure_case, and
proposed_test. Invalid vetos are discarded by the jury without
ceremony; the directive requires that.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field

from .evaluation import MutationEvaluationReport
from .proposal import MutationProposal
from .reflection import ReflectionReport


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class JuryRole(str, Enum):
    REPLIKATOR = "replikator"
    SKEPTIKER = "skeptiker"
    METHODIKER = "methodiker"
    ADVERSARIAL = "adversarial"
    INTEGRATOR = "integrator"


class Vote(str, Enum):
    APPROVE = "approve"
    REVISE = "revise"
    VETO = "veto"
    # v0.9: stress-seed soft veto. CONCERN is neither APPROVE nor
    # VETO; it records that the stress seed (typically 999)
    # regressed while the mandatory seed list did not. Promotion is
    # not hard-blocked; the rationale and structured artifact must
    # be logged for review.
    CONCERN = "concern"


class Veto(BaseModel):
    """A structured veto. v0.5 directive: invalid vetos are discarded."""

    model_config = ConfigDict(extra="forbid")

    role: JuryRole
    affected_claim: str = Field(..., min_length=1)
    suspected_risk: str = Field(..., min_length=1)
    failure_case: str = Field(..., min_length=1)
    proposed_test: str = Field(..., min_length=1)
    issued_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    @property
    def is_valid(self) -> bool:
        return all([
            self.affected_claim.strip(),
            self.suspected_risk.strip(),
            self.failure_case.strip(),
            self.proposed_test.strip(),
        ])


class JuryReview(BaseModel):
    """One member's round-1 review."""

    model_config = ConfigDict(extra="forbid")

    role: JuryRole
    summary: str = Field(..., min_length=1)
    concerns: tuple[str, ...] = Field(default_factory=tuple)
    suggestions: tuple[str, ...] = Field(default_factory=tuple)
    confidence: float = Field(..., ge=0.0, le=1.0)


class JuryFinalVote(BaseModel):
    """One member's round-2 vote, optionally with a veto."""

    model_config = ConfigDict(extra="forbid")

    role: JuryRole
    vote: Vote
    rationale: str = Field(..., min_length=1)
    veto: Veto | None = None


# ---------------------------------------------------------------------------
# Jury members (deterministic, no LLM)
# ---------------------------------------------------------------------------


JuryReviewFn = Callable[
    [MutationProposal, MutationEvaluationReport, ReflectionReport],
    JuryReview,
]
JuryVoteFn = Callable[
    [
        MutationProposal,
        MutationEvaluationReport,
        ReflectionReport,
        tuple[JuryReview, ...],
    ],
    JuryFinalVote,
]


@dataclass(frozen=True)
class JuryMember:
    role: JuryRole
    review_fn: JuryReviewFn
    vote_fn: JuryVoteFn
    # v0.6: declarative metadata that lets a ledger entry document
    # *which persona* the review purports to come from. v0.6 stays
    # deterministic — there is no actual LLM behind a label — but the
    # label is recorded so that v0.7 can wire in real LLM personas
    # without changing the surrounding code.
    model_label: str = "deterministic-rule-based"


def _replikator_review(p, evalrep, refl) -> JuryReview:
    concerns: list[str] = []
    if not evalrep.passed_regression:
        concerns.append(
            "regression suite is not green; reproducibility cannot be "
            "asserted before regressions are fixed."
        )
    if evalrep.performance_delta < 0:
        concerns.append(
            f"performance regressed by {evalrep.performance_delta:+.2f}"
        )
    return JuryReview(
        role=JuryRole.REPLIKATOR,
        summary=(
            "Reproducibility check: " +
            ("green" if not concerns else "concerns raised below")
        ),
        concerns=tuple(concerns),
        suggestions=(
            "Re-run pflicht suite with seed-shift to bound variance."
            if concerns else
            "No further reproducibility steps required for v0.5 promotion.",
        ),
        confidence=0.8 if not concerns else 0.5,
    )


def _replikator_vote(p, evalrep, refl, round1) -> JuryFinalVote:
    others_flagged = any(r.concerns for r in round1
                         if r.role is not JuryRole.REPLIKATOR)
    if not evalrep.passed_regression:
        return JuryFinalVote(
            role=JuryRole.REPLIKATOR,
            vote=Vote.VETO,
            rationale="regression suite must be green",
            veto=Veto(
                role=JuryRole.REPLIKATOR,
                affected_claim=p.target.value,
                suspected_risk="silent reduction of test coverage",
                failure_case=(
                    "promoting without green regression risks shipping "
                    "a behaviour change that the regression matrix would "
                    "have caught."
                ),
                proposed_test=(
                    "before re-vote: re-run REGRESSION_SCENARIO_IDS twice "
                    "with different seeds and require both runs green."
                ),
            ),
        )
    # v0.8: when a multi_seed_report is attached, the Empiriker
    # answers "Wie hoch ist die Varianz?". High variance on the
    # candidate scenario blocks APPROVE — robustness is the point.
    ms = getattr(refl, "_multi_seed_report", None)
    if ms is not None:
        max_std = 0.0
        for agg in ms.aggregates.values():
            if agg.std_branch_delta > max_std:
                max_std = agg.std_branch_delta
        if max_std > 1.0:
            return JuryFinalVote(
                role=JuryRole.REPLIKATOR,
                vote=Vote.REVISE,
                rationale=(
                    f"multi-seed branch-delta std={max_std:.2f} > 1.0; "
                    "variance is too high to call the improvement robust."
                ),
            )
        # v0.9: "are we reproducing behaviour, or one hidden path?"
        # If a scenario was instantiated with variance (>1 unique
        # permutation) but every seed walked the same path
        # (unique_path_count == 1), the multi-seed report is misleading.
        coverage = getattr(ms, "permutation_coverage", {})
        unique_paths = getattr(ms, "unique_path_count", {})
        for sid, perms in coverage.items():
            if perms > 1 and unique_paths.get(sid, 0) <= 1:
                return JuryFinalVote(
                    role=JuryRole.REPLIKATOR,
                    vote=Vote.REVISE,
                    rationale=(
                        f"scenario {sid} carried {perms} distinct "
                        f"permutations but only 1 unique path was "
                        f"actually walked — variance is not being "
                        f"exercised."
                    ),
                )
    if others_flagged:
        return JuryFinalVote(
            role=JuryRole.REPLIKATOR,
            vote=Vote.REVISE,
            rationale="other reviewers raised concerns; reproducibility "
                      "would benefit from a revision pass.",
        )
    return JuryFinalVote(
        role=JuryRole.REPLIKATOR,
        vote=Vote.APPROVE,
        rationale="reproducibility checks pass.",
    )


def _skeptiker_review(p, evalrep, refl) -> JuryReview:
    concerns: list[str] = []
    if not p.rollback_conditions:
        concerns.append("no rollback conditions declared")
    if not p.expected_improvement:
        concerns.append("no measurable improvement target declared")
    if not p.config_delta:
        concerns.append("config_delta is empty; nothing to promote")
    return JuryReview(
        role=JuryRole.SKEPTIKER,
        summary=(
            "Looking for damage modes" +
            (" — found nothing structural." if not concerns else
             " — surface issues listed below.")
        ),
        concerns=tuple(concerns),
        suggestions=(
            "specify rollback in concrete metric terms"
            if "no rollback conditions declared" in concerns else
            "OK",
        ),
        confidence=0.7 if concerns else 0.85,
    )


def _skeptiker_vote(p, evalrep, refl, round1) -> JuryFinalVote:
    # The skeptic vetos only on missing rollback or empty config_delta.
    if not p.rollback_conditions:
        return JuryFinalVote(
            role=JuryRole.SKEPTIKER,
            vote=Vote.VETO,
            rationale="proposal carries no rollback condition.",
            veto=Veto(
                role=JuryRole.SKEPTIKER,
                affected_claim=p.target.value,
                suspected_risk="silent persistence of a regression",
                failure_case=(
                    "if the mutation degrades a downstream metric, "
                    "without rollback conditions there is no automated "
                    "trigger to revert."
                ),
                proposed_test=(
                    "add at least one rollback condition stated as a "
                    "concrete metric delta (e.g. 'revert if guard_block "
                    "count rises by > 20% over baseline')."
                ),
            ),
        )
    if not p.config_delta:
        return JuryFinalVote(
            role=JuryRole.SKEPTIKER,
            vote=Vote.REVISE,
            rationale="empty config_delta is documentation-only; not "
                      "promotable.",
        )
    # v0.8: when a multi_seed_report is attached, the Skeptiker
    # answers "Ist die Verbesserung robust?". A single-seed flicker
    # is enough to REVISE — robustness is the load-bearing claim.
    ms = getattr(refl, "_multi_seed_report", None)
    if ms is not None:
        from .significance import _evolution_candidate_scenarios
        candidate_ids = _evolution_candidate_scenarios()
        for sid in candidate_ids:
            agg = ms.aggregates.get(sid)
            if agg is None:
                continue
            if agg.improved_seed_count < 4 and agg.n_seeds >= 5:
                return JuryFinalVote(
                    role=JuryRole.SKEPTIKER,
                    vote=Vote.REVISE,
                    rationale=(
                        f"candidate {sid} improved on only "
                        f"{agg.improved_seed_count}/{agg.n_seeds} seeds; "
                        "improvement is not yet robust."
                    ),
                )
    return JuryFinalVote(
        role=JuryRole.SKEPTIKER,
        vote=Vote.APPROVE,
        rationale="rollback conditions are declared and config_delta "
                  "is non-empty.",
    )


def _methodiker_review(p, evalrep, refl) -> JuryReview:
    concerns: list[str] = []
    if refl is None or not refl.has_findings:
        concerns.append(
            "no reflection findings cited; methodologically the proposal "
            "lacks a documented motivation."
        )
    if not p.motivating_findings:
        concerns.append(
            "motivating_findings is empty; the link from observation to "
            "proposed change is undocumented."
        )
    return JuryReview(
        role=JuryRole.METHODIKER,
        summary=(
            "Measurement-validity check"
            + (" — motivation chain not documented." if concerns else
               " — motivation chain documented.")
        ),
        concerns=tuple(concerns),
        suggestions=(
            "reference the originating ReflectionFinding ids in "
            "motivating_findings."
            if concerns else "OK",
        ),
        confidence=0.6 if concerns else 0.75,
    )


def _methodiker_vote(p, evalrep, refl, round1) -> JuryFinalVote:
    if not p.motivating_findings:
        return JuryFinalVote(
            role=JuryRole.METHODIKER,
            vote=Vote.REVISE,
            rationale="proposal must cite the reflection findings it "
                      "addresses.",
        )
    return JuryFinalVote(
        role=JuryRole.METHODIKER,
        vote=Vote.APPROVE,
        rationale="proposal cites motivating findings.",
    )


def _adversarial_review(p, evalrep, refl) -> JuryReview:
    concerns: list[str] = []
    if not evalrep.passed_adversarial:
        concerns.append(
            "adversarial suite is not green; mutation may amplify "
            "an existing failure mode."
        )
    return JuryReview(
        role=JuryRole.ADVERSARIAL,
        summary=(
            "Adversarial probe summary: "
            + ("clean" if not concerns else "failure modes detected")
        ),
        concerns=tuple(concerns),
        suggestions=(
            "investigate the failing adversarial pattern before promotion."
            if concerns else "OK",
        ),
        confidence=0.85 if not concerns else 0.4,
    )


def _adversarial_vote(p, evalrep, refl, round1) -> JuryFinalVote:
    if not evalrep.passed_adversarial:
        # Find the first failing scenario_id from the adversarial suite.
        failing = next(
            (r.scenario_id for r in evalrep.adversarial_results
             if not r.passed),
            "ADV_*",
        )
        return JuryFinalVote(
            role=JuryRole.ADVERSARIAL,
            vote=Vote.VETO,
            rationale=f"adversarial pattern {failing!s} failed.",
            veto=Veto(
                role=JuryRole.ADVERSARIAL,
                affected_claim=p.target.value,
                suspected_risk="adversarial scenario regression",
                failure_case=(
                    f"clone failed adversarial scenario {failing}; "
                    "promotion would ship the regression."
                ),
                proposed_test=(
                    f"add a regression check that re-runs {failing} "
                    "and asserts run_started + run_ended + zero "
                    "hook errors."
                ),
            ),
        )
    return JuryFinalVote(
        role=JuryRole.ADVERSARIAL,
        vote=Vote.APPROVE,
        rationale="all adversarial patterns pass.",
    )


def _integrator_review(p, evalrep, refl) -> JuryReview:
    concerns: list[str] = []
    if not evalrep.all_green:
        concerns.append("at least one suite is not green; not promotable.")
    return JuryReview(
        role=JuryRole.INTEGRATOR,
        summary=(
            "Promotion-fitness check: "
            + ("ready" if not concerns else "not ready")
        ),
        concerns=tuple(concerns),
        suggestions=(
            "block promotion until all suites are green."
            if concerns else "ready for promotion.",
        ),
        confidence=0.9 if not concerns else 0.3,
    )


def _integrator_vote(p, evalrep, refl, round1) -> JuryFinalVote:
    any_other_veto = any(
        r.role is JuryRole.SKEPTIKER and "no rollback" in (r.concerns[0] if r.concerns else "")
        for r in round1
    )
    if not evalrep.all_green:
        return JuryFinalVote(
            role=JuryRole.INTEGRATOR,
            vote=Vote.REVISE,
            rationale="suites not all green; revise and re-evaluate.",
        )
    if any_other_veto:
        return JuryFinalVote(
            role=JuryRole.INTEGRATOR,
            vote=Vote.REVISE,
            rationale="another reviewer raised a structural concern.",
        )
    # v0.8: when a multi_seed_report is attached, the Integrator
    # answers "Ist das robust genug für Promotion?". The
    # SignificanceGate verdict is the load-bearing input. Robust
    # improvement → APPROVE; regression → VETO; inconclusive → REVISE.
    ms = getattr(refl, "_multi_seed_report", None)
    if ms is not None:
        from .significance import SignificanceGate
        decision = SignificanceGate().decide(ms)
        if decision.verdict == "regressed":
            failing = decision.failing_seeds or ("?",)
            return JuryFinalVote(
                role=JuryRole.INTEGRATOR,
                vote=Vote.VETO,
                rationale=(
                    f"multi-seed gate verdict='regressed' "
                    f"(failing seeds {list(failing)}): {decision.rationale}"
                ),
                veto=Veto(
                    role=JuryRole.INTEGRATOR,
                    affected_claim=p.target.value,
                    suspected_risk="multi-seed regression on a guard scenario",
                    failure_case=(
                        f"at least one seed regressed: {decision.rationale}"
                    ),
                    proposed_test=(
                        "hold the mutation; re-run the multi-seed paired "
                        "evaluation on the full default seed list and "
                        "require zero seeds with verdict='regressed' on "
                        "every regression guard."
                    ),
                ),
            )
        if decision.verdict == "inconclusive":
            return JuryFinalVote(
                role=JuryRole.INTEGRATOR,
                vote=Vote.REVISE,
                rationale=(
                    "multi-seed gate verdict='inconclusive': "
                    f"{decision.rationale}"
                ),
            )
        if decision.verdict == "improved":
            # v0.9 stress-seed soft veto. The stress seed is logged on
            # the report; if it regressed while the mandatory seeds did
            # not, the Integrator records CONCERN instead of APPROVE.
            stress = getattr(ms, "stress_outcome", None)
            if stress is not None and stress.delta.verdict == "regressed":
                return JuryFinalVote(
                    role=JuryRole.INTEGRATOR,
                    vote=Vote.CONCERN,
                    rationale=(
                        f"multi-seed gate verdict='improved' on the "
                        f"mandatory seeds, but the stress seed regressed "
                        f"on scenario {stress.scenario_id}; promotion "
                        f"proceeds with a recorded concern."
                    ),
                )
            return JuryFinalVote(
                role=JuryRole.INTEGRATOR,
                vote=Vote.APPROVE,
                rationale=(
                    "multi-seed gate verdict='improved' on supporting "
                    f"seeds {list(decision.supporting_seeds)}: "
                    f"{decision.rationale}"
                ),
            )
        # 'neutral' falls through to the v0.7 paired-report path /
        # default APPROVE.

    # v0.7: when a paired_report is attached, refuse to APPROVE unless
    # the aggregate verdict reads 'improved'. Neutral and regressed
    # block; round-2 rationale cites the measurable verdict.
    pr = getattr(refl, "_paired_report", None)
    if pr is not None:
        if pr.aggregate_verdict == "regressed":
            # Find the first scenario whose verdict regressed for the
            # ADVERSARIAL role's veto target.
            failing = next(
                (o.scenario_id for o in pr.outcomes
                 if o.delta.verdict == "regressed"),
                "?",
            )
            return JuryFinalVote(
                role=JuryRole.INTEGRATOR,
                vote=Vote.VETO,
                rationale=(
                    f"paired evaluation aggregate verdict='regressed' "
                    f"(scenario {failing} regressed)."
                ),
                veto=Veto(
                    role=JuryRole.INTEGRATOR,
                    affected_claim=p.target.value,
                    suspected_risk="behavioural regression on a guard scenario",
                    failure_case=(
                        f"scenario {failing} shows a verdict=regressed "
                        f"delta under the clone config."
                    ),
                    proposed_test=(
                        f"hold the mutation; re-run the paired "
                        f"evaluation with a different seed and require "
                        f"verdict != 'regressed' on {failing}."
                    ),
                ),
            )
        if pr.aggregate_verdict == "neutral":
            return JuryFinalVote(
                role=JuryRole.INTEGRATOR,
                vote=Vote.REVISE,
                rationale=(
                    "paired evaluation aggregate verdict='neutral'; "
                    "no measurable improvement yet — revise and re-test."
                ),
            )
        # 'improved' falls through to the standard APPROVE.
    return JuryFinalVote(
        role=JuryRole.INTEGRATOR,
        vote=Vote.APPROVE,
        rationale="all promotion preconditions are met.",
    )


DEFAULT_MEMBERS: tuple[JuryMember, ...] = (
    JuryMember(JuryRole.REPLIKATOR, _replikator_review, _replikator_vote,
               model_label="deterministic-claude-persona"),
    JuryMember(JuryRole.SKEPTIKER, _skeptiker_review, _skeptiker_vote,
               model_label="deterministic-gpt-persona"),
    JuryMember(JuryRole.METHODIKER, _methodiker_review, _methodiker_vote,
               model_label="deterministic-gemini-persona"),
    JuryMember(JuryRole.ADVERSARIAL, _adversarial_review, _adversarial_vote,
               model_label="deterministic-mistral-persona"),
    JuryMember(JuryRole.INTEGRATOR, _integrator_review, _integrator_vote,
               model_label="deterministic-llama-persona"),
)


# ---------------------------------------------------------------------------
# Jury orchestrator
# ---------------------------------------------------------------------------


@dataclass
class JuryDecision:
    """Result of a full two-round jury session."""

    round1_reviews: tuple[JuryReview, ...]
    round2_votes: tuple[JuryFinalVote, ...]

    @property
    def valid_vetos(self) -> list[Veto]:
        return [v.veto for v in self.round2_votes
                if v.vote is Vote.VETO and v.veto is not None
                and v.veto.is_valid]

    @property
    def invalid_vetos(self) -> list[JuryFinalVote]:
        """Vetos that lack the four mandatory fields are discarded."""
        out: list[JuryFinalVote] = []
        for fv in self.round2_votes:
            if fv.vote is not Vote.VETO:
                continue
            if fv.veto is None or not fv.veto.is_valid:
                out.append(fv)
        return out

    @property
    def approve_count(self) -> int:
        return sum(1 for v in self.round2_votes if v.vote is Vote.APPROVE)

    @property
    def revise_count(self) -> int:
        return sum(1 for v in self.round2_votes if v.vote is Vote.REVISE)

    @property
    def quorum_reached(self) -> bool:
        return self.approve_count >= 4


class DelphiJury:
    """Two-round deterministic jury orchestrator."""

    def __init__(
        self,
        members: tuple[JuryMember, ...] | None = None,
    ) -> None:
        self._members = members if members is not None else DEFAULT_MEMBERS

    def deliberate(
        self,
        proposal: MutationProposal,
        eval_report: MutationEvaluationReport,
        reflection: ReflectionReport,
        *,
        paired_report: Any | None = None,
        multi_seed_report: Any | None = None,
    ) -> JuryDecision:
        """Run two rounds of review on a proposal.

        v0.7: ``paired_report`` is an optional
        :class:`desi.evolution.PairedEvaluationReport`. When supplied,
        it is stapled onto the reflection report so that role
        functions can consult the per-scenario stable / clone metrics
        and the aggregate verdict. The directive: round-2 votes must
        cite measurable arguments — the paired_report is the
        load-bearing input for that.

        v0.8: ``multi_seed_report`` is an optional
        :class:`desi.evolution.MultiSeedEvaluationReport`. When
        supplied, it supersedes ``paired_report`` for promotion
        decisions: the Skeptiker probes robustness, the Replikator
        (Empiriker) probes variance, and the Integrator consults the
        :class:`desi.evolution.SignificanceGate` instead of the
        single-seed aggregate verdict.
        """
        # Snapshot the paired report on the reflection object so that
        # the existing five role functions can read it via getattr
        # without changing every signature. v0.7 keeps the signatures
        # stable so v0.6 jury subclasses keep working.
        if paired_report is not None:
            object.__setattr__(reflection, "_paired_report", paired_report)
        if multi_seed_report is not None:
            object.__setattr__(reflection, "_multi_seed_report",
                               multi_seed_report)
        # Round 1: independent reviews.
        round1 = tuple(
            m.review_fn(proposal, eval_report, reflection)
            for m in self._members
        )
        # Round 2: each member sees all round1 reviews and votes.
        round2 = tuple(
            m.vote_fn(proposal, eval_report, reflection, round1)
            for m in self._members
        )
        return JuryDecision(round1_reviews=round1, round2_votes=round2)


def paired_verdict(reflection) -> str | None:
    """Return the aggregate verdict of the v0.7 paired report, if any.

    Helper for role functions; returns None when no paired_report is
    attached (v0.6-style call).
    """
    pr = getattr(reflection, "_paired_report", None)
    if pr is None:
        return None
    return pr.aggregate_verdict
