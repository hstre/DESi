"""Inference validation — the five closed rule types of v1.2.

Only these rule types may produce a ``LOGICALLY_SUPPORTED`` verdict:

* :attr:`InferenceRule.SYLLOGISM`     — Barbara form
* :attr:`InferenceRule.IMPLICATION`    — modus ponens
* :attr:`InferenceRule.TRANSITIVITY`   — A→B, B→C ⇒ A→C
* :attr:`InferenceRule.CONTRADICTION`  — P ∧ ¬P → reject
* :attr:`InferenceRule.EQUIVALENCE`    — substitution under P ↔ Q

An "unknown" inference rule (anything outside this enum) is not
representable; the auditor must run ``try_each_rule`` and only
return ``LOGICALLY_SUPPORTED`` when one of the five matches.
Everything else is either ``BRIDGE_REQUIRED`` (a missing premise
would close the gap) or ``LOGICALLY_REJECTED`` (no chain reachable
inside this rule set).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .premises import (
    ConclusionProposition,
    Premise,
    PremiseKind,
    Propositions,
)


class InferenceRule(str, Enum):
    SYLLOGISM = "syllogism"
    IMPLICATION = "implication"
    TRANSITIVITY = "transitivity"
    CONTRADICTION = "contradiction"
    EQUIVALENCE = "equivalence"


@dataclass(frozen=True)
class InferenceMatch:
    """One successful application of an inference rule."""

    rule: InferenceRule
    used_premise_ids: tuple[str, ...]


# ---------------------------------------------------------------------------
# Per-rule validators
# ---------------------------------------------------------------------------


def _try_syllogism(
    premises: tuple[Premise, ...],
    conclusion: ConclusionProposition,
) -> InferenceMatch | None:
    """Barbara: All M are P. S is M. Therefore S is P.

    v1.7: universal-conclusion form.
    All A are B. All B are C. Therefore all A are C.

    The two forms differ only in conclusion shape (PARTICULAR vs
    UNIVERSAL); the universal form requires two universal premises
    that share a middle term. Adding it is a narrow extension of
    the existing rule, not a new operator.
    """
    if conclusion.kind == PremiseKind.PARTICULAR:
        s, p = conclusion.subject, conclusion.predicate
        if not (s and p):
            return None
        for univ in premises:
            if univ.kind != PremiseKind.UNIVERSAL:
                continue
            if univ.predicate != p:
                continue
            m = univ.subject
            for part in premises:
                if part.premise_id == univ.premise_id:
                    continue
                if part.kind != PremiseKind.PARTICULAR:
                    continue
                if part.subject != s:
                    continue
                if part.predicate != m:
                    continue
                return InferenceMatch(
                    rule=InferenceRule.SYLLOGISM,
                    used_premise_ids=(univ.premise_id, part.premise_id),
                )
        return None
    if conclusion.kind == PremiseKind.UNIVERSAL:
        # v1.7: universal-conclusion Barbara.
        a, c = conclusion.subject, conclusion.predicate
        if not (a and c):
            return None
        for p1 in premises:
            if p1.kind != PremiseKind.UNIVERSAL:
                continue
            if p1.subject != a:
                continue
            b = p1.predicate
            for p2 in premises:
                if p2.premise_id == p1.premise_id:
                    continue
                if p2.kind != PremiseKind.UNIVERSAL:
                    continue
                if p2.subject != b:
                    continue
                if p2.predicate != c:
                    continue
                return InferenceMatch(
                    rule=InferenceRule.SYLLOGISM,
                    used_premise_ids=(p1.premise_id, p2.premise_id),
                )
        return None
    return None


def _try_implication(
    premises: tuple[Premise, ...],
    conclusion: ConclusionProposition,
) -> InferenceMatch | None:
    """Modus ponens: P. (If P then Q). Therefore Q."""
    for cond in premises:
        if cond.kind not in (PremiseKind.CONDITIONAL, PremiseKind.IMPLICATION):
            continue
        ant, con = cond.antecedent, cond.consequent
        if not (ant and con):
            continue
        # Conclusion must syntactically match Q.
        if not _atom_matches(conclusion.text, con):
            continue
        # P must appear as another premise.
        for ant_p in premises:
            if ant_p.premise_id == cond.premise_id:
                continue
            if _atom_matches(ant_p.text, ant):
                return InferenceMatch(
                    rule=InferenceRule.IMPLICATION,
                    used_premise_ids=(ant_p.premise_id, cond.premise_id),
                )
    return None


def _try_transitivity(
    premises: tuple[Premise, ...],
    conclusion: ConclusionProposition,
) -> InferenceMatch | None:
    """A→B. B→C. Therefore A→C."""
    if conclusion.kind not in (PremiseKind.IMPLICATION,
                                PremiseKind.CONDITIONAL):
        return None
    a, c = conclusion.antecedent, conclusion.consequent
    if not (a and c):
        return None
    for p1 in premises:
        if p1.kind not in (PremiseKind.IMPLICATION,
                            PremiseKind.CONDITIONAL):
            continue
        if p1.antecedent != a:
            continue
        x = p1.consequent
        for p2 in premises:
            if p2.premise_id == p1.premise_id:
                continue
            if p2.kind not in (PremiseKind.IMPLICATION,
                                PremiseKind.CONDITIONAL):
                continue
            if p2.antecedent != x:
                continue
            if p2.consequent != c:
                continue
            return InferenceMatch(
                rule=InferenceRule.TRANSITIVITY,
                used_premise_ids=(p1.premise_id, p2.premise_id),
            )
    return None


def _try_contradiction(
    premises: tuple[Premise, ...],
    conclusion: ConclusionProposition,
) -> InferenceMatch | None:
    """Detect P and ¬P among the premises.

    v1.2 recognises a contradiction syntactically: a particular
    premise "S is P" plus a particular premise "S is not P". The
    conclusion must explicitly assert the contradiction (e.g. "the
    premises contradict") for the rule to apply.
    """
    if "contradict" not in conclusion.text.lower():
        return None
    pos: dict[tuple[str, str], str] = {}
    for p in premises:
        if p.kind != PremiseKind.PARTICULAR:
            continue
        if p.predicate.startswith("not "):
            base = p.predicate[len("not "):].strip()
            key = (p.subject, base)
            if key in pos:
                return InferenceMatch(
                    rule=InferenceRule.CONTRADICTION,
                    used_premise_ids=(pos[key], p.premise_id),
                )
        else:
            key = (p.subject, p.predicate)
            for q in premises:
                if q.premise_id == p.premise_id:
                    continue
                if q.kind != PremiseKind.PARTICULAR:
                    continue
                if q.subject != p.subject:
                    continue
                if q.predicate == f"not {p.predicate}":
                    return InferenceMatch(
                        rule=InferenceRule.CONTRADICTION,
                        used_premise_ids=(p.premise_id, q.premise_id),
                    )
            pos[key] = p.premise_id
    return None


def _try_equivalence(
    premises: tuple[Premise, ...],
    conclusion: ConclusionProposition,
) -> InferenceMatch | None:
    """Substitution under an "X is the same as Y" premise.

    Equivalence is recognised by a premise of the form
    "X means Y" or "X is equivalent to Y". The conclusion is valid
    if it matches another premise's text with X / Y substituted.
    """
    eq_premises = [p for p in premises
                   if p.kind == PremiseKind.PARTICULAR
                   and (p.predicate.startswith("equivalent to ")
                        or p.predicate.startswith("the same as "))]
    for eq in eq_premises:
        x = eq.subject
        if eq.predicate.startswith("equivalent to "):
            y = eq.predicate[len("equivalent to "):].strip()
        else:
            y = eq.predicate[len("the same as "):].strip()
        for src in premises:
            if src.premise_id == eq.premise_id:
                continue
            substituted = src.text.replace(x, y)
            if _atom_matches(conclusion.text, substituted):
                return InferenceMatch(
                    rule=InferenceRule.EQUIVALENCE,
                    used_premise_ids=(eq.premise_id, src.premise_id),
                )
    return None


_VALIDATORS = {
    InferenceRule.SYLLOGISM: _try_syllogism,
    InferenceRule.IMPLICATION: _try_implication,
    InferenceRule.TRANSITIVITY: _try_transitivity,
    InferenceRule.CONTRADICTION: _try_contradiction,
    InferenceRule.EQUIVALENCE: _try_equivalence,
}


def _atom_matches(a: str, b: str) -> bool:
    """Permissive equality between two atomic strings.

    Lowercase, strip, drop trailing period — that is all. The
    extractor already canonicalised inflections inside structured
    phrases; this helper handles the loose remainder.
    """
    return a.strip().rstrip(".").lower() == b.strip().rstrip(".").lower()


def try_each_rule(props: Propositions) -> InferenceMatch | None:
    """Try every rule in :class:`InferenceRule` order; return the first
    successful match, or ``None``.
    """
    if props.conclusion is None:
        return None
    for rule, validator in _VALIDATORS.items():
        match = validator(props.premises, props.conclusion)
        if match is not None:
            return match
    return None


def validate_inference(
    rule: InferenceRule,
    premises: tuple[Premise, ...],
    conclusion: ConclusionProposition,
) -> InferenceMatch | None:
    """Validate a *specific* rule against the inputs."""
    return _VALIDATORS[rule](premises, conclusion)


__all__ = [
    "InferenceMatch",
    "InferenceRule",
    "try_each_rule",
    "validate_inference",
]
