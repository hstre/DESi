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
    CAUSAL_CHAIN = "causal_chain"


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


# ---------------------------------------------------------------------------
# v2.7 — CAUSAL_CHAIN
# ---------------------------------------------------------------------------
#
# The two guards from v2.6's read-only probe are encoded directly in
# this validator. Both are necessary; both must hold; neither uses a
# new operator, ClaimState, BridgeKind, or external library.
#
# Guard 1 (CONTRADICTION-FIRST): the validator is registered AFTER
# the v1.2 CONTRADICTION rule in ``_VALIDATORS``, so any premise set
# the contradiction rule already matches will return its own match
# before CAUSAL_CHAIN is even tried (``try_each_rule`` short-circuits
# on the first hit). The validator additionally refuses to fire on
# any input containing a negation marker so contradictions whose
# syntactic shape is not captured by the v1.2 CONTRADICTION rule do
# not slip through here either.
#
# Guard 2 (CYCLE-DELEGATION): structural cycles in the premise set
# are detected by a content-token repetition check — any token
# appearing in 3+ distinct premises, or any explicit cyclic-
# reference connective ("because", "depends on", "requires",
# "relies on", "uses"), defers to the resolver's cycle infrastructure.

_NEGATION_MARKERS: tuple[str, ...] = (
    " not ", "n't ", " never ", " none ", " no ",
)

# Universal / quantifier markers in surface text. Their presence
# signals a logical form (syllogism, contradiction, etc.) that
# CAUSAL_CHAIN must not shadow.
_QUANTIFIER_MARKERS: tuple[str, ...] = (
    " all ", " every ", " some ", " any ", " each ", " no ",
)

# Explicit cyclic-reference connectives — defer to cycle resolution.
_CYCLE_CONNECTIVES: tuple[str, ...] = (
    " because ", " depends on ", " requires ",
    " relies on ", " uses ",
)


# v3.16 — adversarial suspension extensions. v3.15's red-team probe
# demonstrated that the v2.7 marker tuples above are bypassable by
# synonyms. The constants below close those gaps for the families
# v3.15 identified. They are intentionally kept as separate tuples
# so reviewers can see the v2.7 baseline and the v3.16 increment
# side-by-side. Justification: docs/memory/v3_16.md.
_V316_NEGATION_EXTENSIONS: tuple[str, ...] = (
    " lacked ", " lacks ", " lacking ", " lack ",
    " absent ", " vanished ", " vanishes ", " vanish ",
    " missing ", " ceased ", " ceases ", " cease ",
    " infertile ", " ran out ", " gone ",
    # Note: "failed/broke/destroyed/shattered/torn" intentionally
    # *omitted* — they appear in v2.3 R1 / R2_02 chains as
    # legitimate cause-effect verbs. Treating them as negations
    # would break the v2.3 multistep benchmark.
)

_V316_QUANTIFIER_EXTENSIONS: tuple[str, ...] = (
    " consistently ", " universally ", " throughout ",
    " invariably ", " always ", " globally ",
    " perpetually ", " continuously ", " everywhere ",
    " constantly ",
)

# Authority-like verbs OUTSIDE the v1.8 closed lemma library. These
# bypass PremiseExtractor's AUTHORITY classification and therefore
# would slip through as ATOMIC premises. We block them inside the
# chain rule's own guard instead of touching PremiseExtractor.
_V316_AUTHORITY_LIKE_VERBS: tuple[str, ...] = (
    " wrote ", " writes ", " argued ", " argues ",
    " noted ", " notes ", " observed ", " observes ",
    " thought ", " thinks ", " felt ", " feels ",
    " suggested ", " suggests ", " believed ", " believes ",
)

# X-is-Y metaphor markers. The metaphor-as-claim shape is caught
# by the v3.4 FrameDetector elsewhere, but inside an unframed
# CAUSAL_CHAIN candidate the same shape slips through. We block
# the chain when any premise looks like a category-identification
# metaphor ("Time is a river"). Syllogisms ("Socrates is a man")
# carry an explicit "All ..." premise which lets the SYLLOGISM
# rule match first.
_V316_METAPHOR_MARKERS: tuple[str, ...] = (
    " is a ", " is an ", " are a ", " are an ",
)

# Cycle-reference synonyms beyond the v2.7 list. Same defer-to-
# cycle-resolver semantics as v2.7's _CYCLE_CONNECTIVES.
_V316_CYCLE_REF_EXTENSIONS: tuple[str, ...] = (
    " rests on ", " rest on ", " follows from ",
    " stems from ", " comes from ", " stands on ",
    " leans against ", " emerges from ", " grows from ",
    " grow from ",
)

# Number-word vocabulary for tool-contamination detection. A chain
# whose premises *and* conclusion both quote numeric quantities is
# an arithmetic claim disguised as a causal chain — it belongs to
# the tool-computable pipeline, not the chain rule.
_V316_NUMBER_WORDS: frozenset[str] = frozenset({
    "one", "two", "three", "four", "five", "six", "seven",
    "eight", "nine", "ten", "eleven", "twelve", "thirteen",
    "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
    "nineteen", "twenty", "thirty", "forty", "fifty", "sixty",
    "seventy", "eighty", "ninety", "hundred", "thousand",
})


# v4.3 — externally localised marker extensions. Every token
# here is taken verbatim from a v4.2 ExternalAuditFailure
# cluster with counterfactual_reduction >= 5 and contamination
# = 0 against the v1.5 / v2.3 / v3.14 / v3.15 / v3.16 / v4.0
# protected pool. The three tuples target exactly three v4.2
# clusters: HIDDEN_NEGATION, QUANTIFIER_DRIFT,
# AUTHORITY_CONTAMINATION. CYCLE_DISGUISE is deliberately not
# patched here — its v4.2 candidate tokens are content tokens,
# not connective patterns, and adding them would not respect
# the closed marker family. Justification:
# docs/memory/v4_3.md.
_V43_NEGATION_EXTENSIONS: tuple[str, ...] = (
    " rules out ", " ruled out ",
    " is excluded ", " are excluded ", " excluded by ",
    " is forgotten ", " was forgotten ",
    " safely deferred ",
    " is singular ", " are supplementary ",
    " no real ",
    " suppressed cell growth ",
    " accelerated disease ",
    " reduced the desired ",
)

_V43_QUANTIFIER_EXTENSIONS: tuple[str, ...] = (
    " guaranteed ", " single-handedly ", " alone ",
    " solely ", " sole cause ", " entire decline ",
    " for a decade ", " conclusively ", " unambiguously ",
    " only at ", " in perpetuity ",
)

_V43_AUTHORITY_LIKE_VERBS: tuple[str, ...] = (
    " endorsed ", " validated ", " reportedly ",
    " conclusively established ",
)


def _has_number_word(text: str) -> bool:
    padded = " " + text.lower() + " "
    # Hyphenated compounds like "thirty-one" / "twenty-five" must
    # split so their parts are checked against the number-word set.
    for ch in ",.:;!?'\"-":
        padded = padded.replace(ch, " ")
    for tok in padded.split():
        if tok in _V316_NUMBER_WORDS:
            return True
        if any(c.isdigit() for c in tok):
            return True
    return False


_TOKEN_STOPWORDS: frozenset[str] = frozenset({
    "the", "a", "an", "this", "that", "these", "those",
    "it", "they", "he", "she", "we", "you", "i", "him", "her",
    "his", "hers", "their", "its",
    "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had",
    "of", "in", "on", "at", "to", "for", "with", "and", "or", "but",
    "as", "by", "from", "than", "then",
    "therefore", "thus", "so", "hence",
    "if", "while", "when", "where",
    "not", "no", "yes", "all", "some", "any",
})


def _content_tokens(text: str) -> set[str]:
    """Lowercase content-word set; punctuation stripped. No regex."""
    s = " " + text.lower() + " "
    for ch in ",.:;!?'\"":
        s = s.replace(ch, " ")
    out: set[str] = set()
    for tok in s.split():
        if tok in _TOKEN_STOPWORDS:
            continue
        if len(tok) < 3:
            continue
        out.add(tok)
    return out


def _contains_marker(text: str, markers: tuple[str, ...]) -> bool:
    padded = " " + text.lower() + " "
    return any(m in padded for m in markers)


def _try_causal_chain(
    premises: tuple[Premise, ...],
    conclusion: ConclusionProposition,
) -> InferenceMatch | None:
    """v2.7 — linear cause-effect chain.

    Matches deterministic sequential-cause text such as
    "A. B. C. Therefore D." when **all** of the following hold:

    1. premise count >= 2 (true chain, not a single fact)
    2. every premise is ATOMIC or PARTICULAR (no universal /
       conditional / implication / authority premise — those have
       their own rules and CAUSAL_CHAIN must not shadow them)
    3. conclusion is ATOMIC or PARTICULAR
    4. no premise or conclusion text contains a negation marker
    5. no premise text contains a universal/quantifier marker
    6. no premise text contains a cyclic-reference connective
    7. no content token appears in 3+ distinct premises
       (structural cycle guard)
    8. no conclusion content token appears in 2+ distinct premises
       (recycled-conclusion guard against the
       v2.3 R4 false-positive shape)

    On match the validator returns an :class:`InferenceMatch` over
    every premise — the whole chain participated in the verdict.
    """
    if conclusion is None or len(premises) < 2:
        return None

    allowed_kinds = {PremiseKind.ATOMIC, PremiseKind.PARTICULAR}
    if conclusion.kind not in allowed_kinds:
        return None
    if any(p.kind not in allowed_kinds for p in premises):
        return None

    # Guard 1 (negation): a premise or conclusion negating any term
    # signals contradiction-shape, not chain-shape.
    if _contains_marker(conclusion.text, _NEGATION_MARKERS):
        return None
    for p in premises:
        if _contains_marker(p.text, _NEGATION_MARKERS):
            return None

    # Universal / quantifier guard: a quantified premise belongs to
    # SYLLOGISM / CONTRADICTION territory, not to CAUSAL_CHAIN.
    for p in premises:
        if _contains_marker(p.text, _QUANTIFIER_MARKERS):
            return None
    if _contains_marker(conclusion.text, _QUANTIFIER_MARKERS):
        return None

    # Guard 2 (cycle connective): explicit cycle wiring delegates to
    # the resolver's cycle infrastructure.
    for p in premises:
        if _contains_marker(p.text, _CYCLE_CONNECTIVES):
            return None

    # Guard 2 (token-repetition cycle): a content token in three or
    # more distinct premises is a structural cycle.
    token_to_premises: dict[str, set[int]] = {}
    premise_tokens: list[set[str]] = []
    for idx, p in enumerate(premises):
        toks = _content_tokens(p.text)
        premise_tokens.append(toks)
        for t in toks:
            token_to_premises.setdefault(t, set()).add(idx)
    if any(len(v) >= 3 for v in token_to_premises.values()):
        return None

    # Recycled-conclusion guard: no conclusion content token in 2+
    # distinct premises. R4's "Penguins fly" / "rectangles are
    # squares" / "light bends in straight lines" shapes are caught
    # here.
    concl_tokens = _content_tokens(conclusion.text)
    for t in concl_tokens:
        owners = token_to_premises.get(t, set())
        if len(owners) >= 2:
            return None

    # v3.16 — adversarial suspension guards. Synthesised from the
    # v3.15 red-team families. Any hit returns None, which lets the
    # existing auditor pipeline route via _classify_gap → an
    # existing ClaimState (no new states introduced).

    # Guard 9 — extended negation (synonym bypass).
    if _contains_marker(conclusion.text, _V316_NEGATION_EXTENSIONS):
        return None
    for p in premises:
        if _contains_marker(p.text, _V316_NEGATION_EXTENSIONS):
            return None

    # Guard 10 — extended quantifier drift.
    if _contains_marker(conclusion.text, _V316_QUANTIFIER_EXTENSIONS):
        return None
    for p in premises:
        if _contains_marker(p.text, _V316_QUANTIFIER_EXTENSIONS):
            return None

    # Guard 11 — authority-like verbs (PremiseExtractor lemma bypass).
    for p in premises:
        if _contains_marker(p.text, _V316_AUTHORITY_LIKE_VERBS):
            return None

    # Guard 12 — X-is-Y metaphor markers in any premise.
    for p in premises:
        if _contains_marker(p.text, _V316_METAPHOR_MARKERS):
            return None
    if _contains_marker(conclusion.text, _V316_METAPHOR_MARKERS):
        return None

    # Guard 13 — extended cycle-reference synonyms.
    for p in premises:
        if _contains_marker(p.text, _V316_CYCLE_REF_EXTENSIONS):
            return None

    # Guard 14 — tool contamination: numbers in *both* premise and
    # conclusion mean the claim is arithmetic, not causal.
    if (any(_has_number_word(p.text) for p in premises)
            and _has_number_word(conclusion.text)):
        return None

    # v4.3 — externally localized marker extensions. Sourced from
    # v4.2's ExternalAuditFailure clusters (HIDDEN_NEGATION,
    # QUANTIFIER_DRIFT, AUTHORITY_CONTAMINATION). Every token in
    # these tuples has counterfactual evidence in
    # artifacts/v4_2/report.json with zero benchmark
    # contamination. Justification: docs/memory/v4_3.md.

    # Guard 15 — externally localized HIDDEN_NEGATION surface
    # forms not in the v3.16 negation set.
    if _contains_marker(
            conclusion.text, _V43_NEGATION_EXTENSIONS):
        return None
    for p in premises:
        if _contains_marker(p.text, _V43_NEGATION_EXTENSIONS):
            return None

    # Guard 16 — externally localized QUANTIFIER_DRIFT
    # intensifiers and over-generalisations.
    if _contains_marker(
            conclusion.text, _V43_QUANTIFIER_EXTENSIONS):
        return None
    for p in premises:
        if _contains_marker(p.text, _V43_QUANTIFIER_EXTENSIONS):
            return None

    # Guard 17 — externally localized AUTHORITY_CONTAMINATION
    # verbs that ground the conclusion on a speaker rather than
    # evidence.
    if _contains_marker(
            conclusion.text, _V43_AUTHORITY_LIKE_VERBS):
        return None
    for p in premises:
        if _contains_marker(p.text, _V43_AUTHORITY_LIKE_VERBS):
            return None

    # v4.5 — bidirectional-cycle structural guard. Pure graph
    # check; no marker tuple, no synonym list, no content
    # vocabulary. Reuses ``_content_tokens`` and the v2.7
    # token-to-premise index already built above. Justification:
    # docs/memory/v4_5.md.
    #
    # Guard 18 — BIDIRECTIONAL_CYCLE: the conclusion content
    # tokens overlap with at least two distinct premises, with
    # total cross-premise overlap of at least three tokens.
    # The v2.7 recycled-conclusion guard (Guard 8 above) catches
    # the case where one conclusion token spans 2+ premises;
    # this guard catches the complementary shape — *different*
    # conclusion tokens spread across multiple premises with
    # no single premise carrying the warrant.
    if _bidirectional_cycle(premises, conclusion, concl_tokens):
        return None

    # v4.7 — modality-consistency guard. Pure tense/modal
    # structural check; no marker tuple, no synonym list, no
    # content vocabulary. Uses two closed sets of *grammatical*
    # tokens: modal auxiliaries (modality indicators) and past
    # auxiliaries (tense indicators), plus the -ed suffix as a
    # past-tense morphological cue. Justification:
    # docs/memory/v4_7.md.
    #
    # Guard 19 — MODALITY_INCONSISTENCY: the conclusion uses a
    # modal verb that no premise introduces, while every
    # premise carries only past-observational tense. This
    # captures the v4.6 W3 pattern (CORRELATION_TO_CAUSATION +
    # SAMPLE_TO_UNIVERSAL) without inspecting any domain word.
    if _modality_inconsistent(premises, conclusion):
        return None

    return InferenceMatch(
        rule=InferenceRule.CAUSAL_CHAIN,
        used_premise_ids=tuple(p.premise_id for p in premises),
    )


_V45_MIN_OVERLAP_PREMISES: int = 2
_V45_MIN_OVERLAP_TOTAL:    int = 3


def _bidirectional_cycle(
    premises: tuple[Premise, ...],
    conclusion: ConclusionProposition,
    concl_tokens: set[str],
) -> bool:
    """Pure structural test for the BIDIRECTIONAL_CYCLE shape
    isolated by v4.4. Fires when the conclusion's content
    tokens overlap with at least ``_V45_MIN_OVERLAP_PREMISES``
    distinct premises and the total overlap reaches
    ``_V45_MIN_OVERLAP_TOTAL`` tokens. Operates only on the
    already-extracted link cardinality; no lexical heuristic,
    no token marker, no synonym list. ``concl_tokens`` is the
    same set computed for Guard 8 above and is passed in so
    the check costs one extra pass over the premise list.
    """
    if conclusion is None or len(premises) < 2:
        return False
    if not concl_tokens:
        return False
    overlap_premises = 0
    overlap_total = 0
    for p in premises:
        shared = concl_tokens & _content_tokens(p.text)
        if shared:
            overlap_premises += 1
            overlap_total += len(shared)
    return (
        overlap_premises >= _V45_MIN_OVERLAP_PREMISES
        and overlap_total >= _V45_MIN_OVERLAP_TOTAL
    )


# v4.7 — modality consistency. Two closed grammatical sets
# (modal auxiliaries and past auxiliaries) plus a single
# morphological suffix cue (-ed). These are *tense indicators*
# in the directive's sense, not synonym lists of domain words.
#
# Only the *strong / categorical* modals are kept. The
# epistemic hedges ('may', 'might', 'could', 'would') and
# the normative auxiliaries ('must', 'should', 'shall',
# 'ought') are deliberately excluded: protected benchmark
# chains use them as standard legal / medical hedging
# language ('the trades may constitute insider activity',
# 'cholestasis must be evaluated promptly'), and including
# them would cause false-negative regressions on valid
# chains. 'will' and 'cannot' are sufficient to catch every
# v4.6 W3 target case (correlation->future projection and
# sample->incapacity generalisation) without contaminating
# the protected pool.
_V47_MODAL_TOKENS: frozenset[str] = frozenset({
    "will", "cannot",
})

_V47_PAST_AUXILIARIES: frozenset[str] = frozenset({
    "was", "were", "had", "did",
})


def _strip_punct(text: str) -> str:
    low = text.lower()
    for ch in ",.:;!?\"'":
        low = low.replace(ch, " ")
    return low


def _has_modal_v47(text: str) -> bool:
    """Conclusion- or premise-side modality indicator."""
    for tok in _strip_punct(text).split():
        if tok in _V47_MODAL_TOKENS:
            return True
    return False


def _is_past_observational_v47(text: str) -> bool:
    """A premise counts as past-observational if it carries
    either a past auxiliary or any -ed-suffix verb. Pure
    morphological/closed-class check — no domain word list."""
    for tok in _strip_punct(text).split():
        if tok in _V47_PAST_AUXILIARIES:
            return True
        if len(tok) >= 4 and tok.endswith("ed"):
            return True
    return False


def _modality_inconsistent(
    premises: tuple[Premise, ...],
    conclusion: ConclusionProposition,
) -> bool:
    """Fires iff the conclusion uses a modal verb that no
    premise introduces, *and* every premise is
    past-observational. Captures the v4.6 W3 pattern with
    contamination 0 on the protected pool."""
    if conclusion is None or not premises:
        return False
    if not _has_modal_v47(conclusion.text):
        return False
    if any(_has_modal_v47(p.text) for p in premises):
        return False
    if not all(_is_past_observational_v47(p.text)
               for p in premises):
        return False
    return True


_VALIDATORS = {
    InferenceRule.SYLLOGISM: _try_syllogism,
    InferenceRule.IMPLICATION: _try_implication,
    InferenceRule.TRANSITIVITY: _try_transitivity,
    InferenceRule.CONTRADICTION: _try_contradiction,
    InferenceRule.EQUIVALENCE: _try_equivalence,
    # v2.7 — must remain LAST so the four logical rules above get
    # the first shot at every input. The CONTRADICTION-first
    # guard depends on this ordering.
    InferenceRule.CAUSAL_CHAIN: _try_causal_chain,
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
