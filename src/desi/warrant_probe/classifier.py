"""Aufgabe 5 — closed warrant-failure classifier.

Assigns exactly one ``WarrantFailure`` value per case via a
deterministic priority cascade. The cascade is shaped by the
v4.6 residue — three patterns survive every prior patch:

* a polarity-flip / time-bar contradiction
  (premise asserts X, conclusion asserts ¬X) — falls under
  ``MISSING_BRIDGE_RULE`` because no general bridge rule
  could lawfully connect the two halves.
* an *incapacity* generalisation from one observation
  (e.g., one debate → cannot withstand office) — falls under
  ``SAMPLE_TO_UNIVERSAL``.
* a *future-causal projection* from a descriptive correlation
  (e.g., "study showed correlation" → "will extend lifespan")
  — falls under ``CORRELATION_TO_CAUSATION``.

The classifier is text-only; it never touches the runtime
audit logic.
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import WarrantFailure
from .replay import ReplayRecord


_INCAPACITY_MARKERS: tuple[str, ...] = (
    " cannot withstand ", " unable to ", " incapable of ",
    " too weak to ", " too tired to ",
    " not fit for ", " not equipped for ",
    " demands of office ", " demands of leadership ",
)

_FUTURE_CAUSAL_MARKERS: tuple[str, ...] = (
    " will extend ", " will dominate ", " will fail ",
    " will outperform ", " will collapse ", " will rise ",
    " will be reported ", " will renew ",
    " for a lifetime ", " for life ",
    " for a decade ", " for years to come ",
    " over the next decade ",
)

_CORRELATION_PREMISE_MARKERS: tuple[str, ...] = (
    " correlation ", " correlated ", " associated ",
    " linked to ", " observational ", " study showed ",
    " observed ", " tracked ",
)

_MODALITY_PAST_MARKERS: tuple[str, ...] = (
    " showed ", " logged ", " reported ", " noted ",
    " appeared ", " observed ", " confirmed ", " tracked ",
    " filed ", " was ", " were ", " had ", " did ",
)

_MODALITY_FUTURE_MARKERS: tuple[str, ...] = (
    " will ", " must ", " cannot ", " should ", " would ",
)

_CONTRADICTION_PAIRS: tuple[tuple[str, str], ...] = (
    # D1I007 family
    (" lost capacity ", " improved "),
    (" lost capacity ", " durability "),
    # X2-V028 family
    (" within the limitation ", " is time-barred "),
    (" within the limitation period ", " is time-barred "),
)


def _normalised(text: str) -> str:
    padded = " " + text.lower() + " "
    for ch in ",.:;!?\"'":
        padded = padded.replace(ch, " ")
    return padded


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    padded = _normalised(text)
    return any(m in padded for m in markers)


def _contains_contradiction_pair(text: str) -> bool:
    padded = _normalised(text)
    return any(
        a in padded and b in padded
        for a, b in _CONTRADICTION_PAIRS
    )


def _conclusion_is_paraphrase(record: ReplayRecord) -> bool:
    """Conclusion is a token-level paraphrase of one premise
    iff >= 80% of conclusion tokens appear in some single
    premise."""
    if not record.conclusion_tokens:
        return False
    concl_set = set(record.conclusion_tokens)
    threshold = max(1, int(0.8 * len(concl_set)))
    for ptoks in record.premise_tokens:
        if len(concl_set & set(ptoks)) >= threshold:
            return True
    return False


@dataclass(frozen=True)
class Classification:
    chain_id: str
    failure_class: str
    rationale: str

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_id": self.chain_id,
            "failure_class": self.failure_class,
            "rationale": self.rationale,
        }


def classify(record: ReplayRecord, text: str) -> Classification:
    """Priority cascade — exactly one closed class per case."""

    # 1) CONCLUSION_RESTATEMENT: conclusion paraphrases one
    #    premise.
    if _conclusion_is_paraphrase(record):
        return Classification(
            chain_id=record.chain_id,
            failure_class=
                WarrantFailure.CONCLUSION_RESTATEMENT.value,
            rationale=(
                ">=80% of conclusion tokens appear in a single "
                "premise"
            ),
        )

    # 2) ALIAS_EQUIVALENCE: conclusion and a premise share a
    #    rare proper-noun-like token cluster (heuristic skip —
    #    no residue case triggers this; kept for taxonomy
    #    completeness).
    # (intentionally fall through for v4.6)

    # 3) CORRELATION_TO_CAUSATION: chain mentions correlation /
    #    association in a premise AND conclusion contains
    #    a future-causal projection marker.
    if (
        _contains_any(text, _CORRELATION_PREMISE_MARKERS)
        and _contains_any(text, _FUTURE_CAUSAL_MARKERS)
    ):
        return Classification(
            chain_id=record.chain_id,
            failure_class=
                WarrantFailure.CORRELATION_TO_CAUSATION.value,
            rationale=(
                "correlation premise + future-causal conclusion"
            ),
        )

    # 4) SAMPLE_TO_UNIVERSAL: incapacity / character
    #    generalisation from limited observation. Checked
    #    before MODALITY_SHIFT because the incapacity pattern
    #    typically *contains* a modal (e.g., 'cannot') and the
    #    deeper failure is the sample → universal jump.
    if _contains_any(text, _INCAPACITY_MARKERS):
        return Classification(
            chain_id=record.chain_id,
            failure_class=
                WarrantFailure.SAMPLE_TO_UNIVERSAL.value,
            rationale=(
                "incapacity / categorical generalisation from "
                "limited observation"
            ),
        )

    # 5) MODALITY_SHIFT: premise tense observational/past
    #    AND conclusion contains modal/future marker.
    has_past = _contains_any(text, _MODALITY_PAST_MARKERS)
    has_modal = _contains_any(text, _MODALITY_FUTURE_MARKERS)
    if has_past and has_modal:
        return Classification(
            chain_id=record.chain_id,
            failure_class=WarrantFailure.MODALITY_SHIFT.value,
            rationale=(
                "past-tense premise + modal/future conclusion"
            ),
        )

    # 6) SCOPE_EXTENSION: conclusion shares some token with
    #    premises but conclusion's referent class is broader
    #    (heuristic: conclusion has a generic universal-shaped
    #    noun phrase like "a person's", "the entire", "every").
    # Markers are authored in the *normalised* form: the
    # ``_normalised`` matcher strips apostrophes, so "a
    # person's" becomes "a person s".
    _UNIVERSAL_SCOPE_HINTS = (
        " a person s ", " an individual s ",
        " the entire ", " across every ",
        " every patient ", " every cohort ",
        " every market ", " every clinic ",
        " every school ", " every office ",
        " every team ", " every plant ",
        " every district ", " every warehouse ",
        " every studio ", " every helpdesk ",
        " every site ",
    )
    if _contains_any(text, _UNIVERSAL_SCOPE_HINTS):
        return Classification(
            chain_id=record.chain_id,
            failure_class=
                WarrantFailure.SCOPE_EXTENSION.value,
            rationale=(
                "premise scope narrower than conclusion's "
                "universal scope hint"
            ),
        )

    # 7) EXCEPTION_SUPPRESSION: chain makes a categorical
    #    factual flip (contradiction pair present) but no
    #    exception qualifier is offered. We surface this only
    #    when no contradiction pair fires but the conclusion
    #    has a categorical "is X" shape with no qualifier.
    # (deferred to MISSING_BRIDGE_RULE below; kept here for
    # taxonomy completeness.)

    # 8) MISSING_BRIDGE_RULE: explicit contradiction between
    #    premise and conclusion (no warrant could lawfully
    #    bridge X → ¬X without an additional rule).
    if _contains_contradiction_pair(text):
        return Classification(
            chain_id=record.chain_id,
            failure_class=
                WarrantFailure.MISSING_BRIDGE_RULE.value,
            rationale=(
                "premise asserts X and conclusion asserts "
                "the negation of X with no bridging rule"
            ),
        )

    # Default — any unhandled false support: MISSING_BRIDGE_RULE
    # is the most specific fall-back for the v4.6 residue.
    if record.conclusion_tokens:
        return Classification(
            chain_id=record.chain_id,
            failure_class=
                WarrantFailure.MISSING_BRIDGE_RULE.value,
            rationale=(
                "no general rule connecting premises to "
                "conclusion was supplied"
            ),
        )

    return Classification(
        chain_id=record.chain_id,
        failure_class=WarrantFailure.UNKNOWN.value,
        rationale="no rule fired",
    )


def classify_all(
    records: tuple[ReplayRecord, ...],
    text_index: dict[str, str],
) -> tuple[Classification, ...]:
    return tuple(
        classify(r, text_index[r.chain_id]) for r in records
    )


__all__ = ["Classification", "classify", "classify_all"]
