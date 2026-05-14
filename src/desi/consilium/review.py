"""Role reviews — four deterministic adversarial reviewers (v1.3).

Each role consumes the same input (a structured ``ReviewContext``)
and produces a frozen :class:`RoleReview`. Reviews are independent
— no role reads another role's output — so a role-order permutation
produces an identical aggregated verdict.

The four reviewers are pure functions over the v1.2 logic surface
plus a small closed library of counterexamples / metaphors. They
never read author / title / source / citation_count / document_count
metadata, even when those values are stapled to the context.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ..logic.bridge_claims import BridgeClaim
from ..logic.premises import PremiseExtractor, PremiseKind, Propositions
from .counterexamples import (
    CounterexampleHit,
    MetaphorHit,
    find_counterexample,
    find_metaphor,
)
from .roles import ConsiliumRole


@dataclass(frozen=True)
class ReviewContext:
    """Everything the four reviewers may consult.

    ``additional_conditions`` is the SKEPTIC's adversarial input.
    ``context`` is the DOMAIN_EXAMINER's discourse-type hint (e.g.
    ``"financial_newspaper"``). Both are explicit, audited inputs;
    neither carries authority metadata.
    """

    bridge: BridgeClaim
    source_claim_id: str
    original_text: str
    additional_conditions: tuple[str, ...] = ()
    context: str = ""


@dataclass(frozen=True)
class RoleReview:
    """One role's structured review.

    ``unresolved_gap`` triggers a VETO. ``needs_more_premises``
    (without ``unresolved_gap``) triggers ``NEEDS_MORE_PREMISES``.
    Both False on every role → ACCEPT_AS_BRIDGE.
    """

    role: ConsiliumRole
    unresolved_gap: bool
    needs_more_premises: bool
    rationale: str
    findings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role.value,
            "unresolved_gap": self.unresolved_gap,
            "needs_more_premises": self.needs_more_premises,
            "rationale": self.rationale,
            "findings": list(self.findings),
        }


# ---------------------------------------------------------------------------
# Internal helpers — shared by the four role reviewers.
# ---------------------------------------------------------------------------


_TOKEN = re.compile(r"[A-Za-z]+")


def _tokens(text: str) -> set[str]:
    return {tok.lower() for tok in _TOKEN.findall(text)}


_STOPWORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been",
    "and", "or", "of", "to", "in", "on", "at", "by", "for",
    "with", "as", "it", "this", "that", "these", "those",
    "therefore", "thus", "so", "then", "from",
})


def _lemma(word: str) -> str:
    """Strip common English inflection suffixes.

    The transformation is deliberately narrow and lossless within
    the v1.3 vocabulary: ``raining`` → ``rain``, ``exposed`` →
    ``expos``, ``streets`` → ``street``. Anything not covered by
    the suffix table is returned verbatim, so the audit log stays
    inspectable.
    """
    w = word.lower()
    for suffix in ("ing", "ed", "es", "s"):
        if w.endswith(suffix) and len(w) > len(suffix) + 1:
            return w[: -len(suffix)]
    return w


def _content_words(text: str) -> set[str]:
    return {_lemma(t) for t in _tokens(text)} - _STOPWORDS


def _extract_premise_conclusion(text: str) -> Propositions:
    return PremiseExtractor().extract(text)


# ---------------------------------------------------------------------------
# LOGICIAN — structural soundness
# ---------------------------------------------------------------------------


def review_logician(ctx: ReviewContext) -> RoleReview:
    """The bridge must structurally connect at least one premise to the
    conclusion. Pure linguistic linkage: the bridge text must share
    a non-stopword content token with both a premise and the
    conclusion. This is the v1.3 equivalent of asking "does the
    bridge inhabit the same world as the argument?".
    """
    bridge_words = _content_words(ctx.bridge.text)
    if not bridge_words:
        return RoleReview(
            role=ConsiliumRole.LOGICIAN,
            unresolved_gap=True,
            needs_more_premises=False,
            rationale="bridge text contains no content words.",
            findings=("empty_bridge",),
        )
    props = _extract_premise_conclusion(ctx.original_text)
    if props.conclusion is None or not props.premises:
        return RoleReview(
            role=ConsiliumRole.LOGICIAN,
            unresolved_gap=True,
            needs_more_premises=False,
            rationale=(
                "original argument has no premises/conclusion "
                "structure; the bridge cannot connect what isn't "
                "structurally present."
            ),
            findings=("no_explicit_chain",),
        )
    premise_words = set()
    for p in props.premises:
        premise_words.update(_content_words(p.text))
    conclusion_words = _content_words(props.conclusion.text)
    shares_premise = bool(bridge_words & premise_words)
    shares_conclusion = bool(bridge_words & conclusion_words)
    if shares_premise and shares_conclusion:
        return RoleReview(
            role=ConsiliumRole.LOGICIAN,
            unresolved_gap=False,
            needs_more_premises=False,
            rationale=(
                "bridge shares content tokens with at least one "
                "premise and the conclusion; structurally sound."
            ),
        )
    return RoleReview(
        role=ConsiliumRole.LOGICIAN,
        unresolved_gap=True,
        needs_more_premises=False,
        rationale=(
            "bridge does not connect a premise to the conclusion: "
            f"shares with premise={shares_premise}, "
            f"shares with conclusion={shares_conclusion}."
        ),
        findings=("structural_disconnect",),
    )


# ---------------------------------------------------------------------------
# SKEPTIC — adversarial counterexamples
# ---------------------------------------------------------------------------


def review_skeptic(ctx: ReviewContext) -> RoleReview:
    """If any additional condition adversarially negates the bridge's
    claim, register an unresolved counterexample."""
    hit = find_counterexample(ctx.bridge.text, ctx.additional_conditions)
    if hit is None:
        return RoleReview(
            role=ConsiliumRole.SKEPTIC,
            unresolved_gap=False,
            needs_more_premises=False,
            rationale=(
                "no adversarial counterexample matched the bridge "
                f"against {len(ctx.additional_conditions)} condition(s)."
            ),
        )
    return RoleReview(
        role=ConsiliumRole.SKEPTIC,
        unresolved_gap=True,
        needs_more_premises=False,
        rationale=(
            f"counterexample: bridge claims '{hit.opposing_concept}' "
            f"but condition '{hit.condition}' negates it "
            f"(pattern='{hit.pattern}')."
        ),
        findings=(f"counterexample:{hit.pattern}",),
    )


# ---------------------------------------------------------------------------
# DOMAIN_EXAMINER — metaphor / discourse ambiguity
# ---------------------------------------------------------------------------


def review_domain_examiner(ctx: ReviewContext) -> RoleReview:
    """If the bridge (or its source) uses vocabulary that is
    metaphorical in the declared context, the consilium needs more
    premises to disambiguate. This is a *needs_more_premises* signal,
    not an unresolved-gap VETO."""
    if not ctx.context:
        return RoleReview(
            role=ConsiliumRole.DOMAIN_EXAMINER,
            unresolved_gap=False,
            needs_more_premises=False,
            rationale=(
                "no discourse context declared; nothing to disambiguate."
            ),
        )
    target = ctx.bridge.text + " " + ctx.original_text
    hit = find_metaphor(target, ctx.context)
    if hit is None:
        return RoleReview(
            role=ConsiliumRole.DOMAIN_EXAMINER,
            unresolved_gap=False,
            needs_more_premises=False,
            rationale=(
                f"no metaphor-prone vocabulary detected under context "
                f"'{ctx.context}'."
            ),
        )
    return RoleReview(
        role=ConsiliumRole.DOMAIN_EXAMINER,
        unresolved_gap=False,
        needs_more_premises=True,
        rationale=(
            f"'{hit.word}' is ambiguous in context '{hit.context}': "
            f"{hit.note}. More premises are required to disambiguate."
        ),
        findings=(f"metaphor:{hit.word}",),
    )


# ---------------------------------------------------------------------------
# INTEGRATOR — closure of the original gap
# ---------------------------------------------------------------------------


def review_integrator(ctx: ReviewContext) -> RoleReview:
    """Holistic closure check.

    v1.3 keeps the check surface-level on purpose. The integrator
    asks two questions:

    1. Does the bridge mention the **subject** of the conclusion?
       (If not, the bridge is talking past the conclusion.)
    2. Does the bridge connect to **at least one premise** by a
       shared content lemma? (Otherwise the bridge floats free.)

    Both must be true. If either fails, the integrator surfaces an
    unresolved gap. This is intentionally a *second* eye on the
    same surface the LOGICIAN scans — two roles independently
    confirming structural coherence.
    """
    props = _extract_premise_conclusion(ctx.original_text)
    if props.conclusion is None:
        return RoleReview(
            role=ConsiliumRole.INTEGRATOR,
            unresolved_gap=True,
            needs_more_premises=False,
            rationale=(
                "no explicit conclusion to integrate against."
            ),
        )
    bridge_words = _content_words(ctx.bridge.text)
    conclusion_subject_tokens = _content_words(
        props.conclusion.subject
        or props.conclusion.text
    )
    premise_words = set()
    for p in props.premises:
        premise_words.update(_content_words(p.text))
    subject_in_bridge = bool(bridge_words & conclusion_subject_tokens)
    connects_to_premise = bool(bridge_words & premise_words)
    if subject_in_bridge and connects_to_premise:
        return RoleReview(
            role=ConsiliumRole.INTEGRATOR,
            unresolved_gap=False,
            needs_more_premises=False,
            rationale=(
                "bridge mentions the conclusion's subject and links "
                "to at least one premise; holistic closure holds."
            ),
        )
    findings: list[str] = []
    parts: list[str] = []
    if not subject_in_bridge:
        findings.append("subject_not_in_bridge")
        parts.append("bridge does not mention the conclusion subject")
    if not connects_to_premise:
        findings.append("bridge_floats_free")
        parts.append("bridge shares no content lemma with any premise")
    return RoleReview(
        role=ConsiliumRole.INTEGRATOR,
        unresolved_gap=True,
        needs_more_premises=False,
        rationale="; ".join(parts) + ".",
        findings=tuple(findings),
    )


_REVIEWERS = {
    ConsiliumRole.LOGICIAN: review_logician,
    ConsiliumRole.SKEPTIC: review_skeptic,
    ConsiliumRole.DOMAIN_EXAMINER: review_domain_examiner,
    ConsiliumRole.INTEGRATOR: review_integrator,
}


def run_role_reviews(
    ctx: ReviewContext,
    *,
    role_order: tuple[ConsiliumRole, ...] | None = None,
) -> tuple[RoleReview, ...]:
    """Run all four reviewers; return the reviews in the iteration order.

    ``role_order`` is honoured only for the order of the returned
    tuple (and the ledger writes). The aggregated verdict is
    computed over the set of reviews — INV-C1 (role-order
    independence).
    """
    if role_order is None:
        from .roles import CANONICAL_ROLE_ORDER
        role_order = CANONICAL_ROLE_ORDER
    seen: set[ConsiliumRole] = set()
    out: list[RoleReview] = []
    for r in role_order:
        if r in seen:
            raise ValueError(f"role {r} appears twice in role_order")
        seen.add(r)
        out.append(_REVIEWERS[r](ctx))
    missing = set(_REVIEWERS) - seen
    if missing:
        raise ValueError(
            f"role_order must list every ConsiliumRole exactly once; "
            f"missing: {sorted(r.value for r in missing)}"
        )
    return tuple(out)


__all__ = [
    "ReviewContext",
    "RoleReview",
    "review_domain_examiner",
    "review_integrator",
    "review_logician",
    "review_skeptic",
    "run_role_reviews",
]
