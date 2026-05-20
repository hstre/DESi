"""Aufgabe 5 — closed content-failure classifier.

Assigns exactly one ``ContentFailure`` value per case via a
deterministic priority cascade. The cascade is shaped by the
v4.8 residue — two distinct patterns survive every prior
patch:

* a direct lexical contradiction at the **statutory /
  procedural** level ("filed within the limitation period →
  is time-barred") — ``DIRECT_CONTRADICTION``,
* a polarity inversion at the **observable property** level
  ("lost capacity → improved durability") —
  ``PROPERTY_REVERSAL``.

The classifier is text-only; no runtime touch.
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import ContentFailure
from .replay import ReplayRecord


# Closed contradiction-pair table. Each pair is a tuple of
# (premise_substring, conclusion_substring); when both appear
# in the chain text the contradiction is *direct* — the
# conclusion explicitly asserts the negation of the premise's
# truth-conditional content.
_DIRECT_CONTRADICTION_PAIRS: tuple[tuple[str, str], ...] = (
    (" within the limitation ", " is time-barred "),
    (" within the limitation period ", " is time-barred "),
    (" timely ", " is time-barred "),
    (" not yet expired ", " is time-barred "),
)

# Polarity-flip pairs: premise asserts a negative
# observable outcome, conclusion asserts the positive
# outcome of the same observable. These are *property*-level
# reversals, distinct from procedural contradictions.
_POLARITY_REVERSAL_PAIRS: tuple[tuple[str, str], ...] = (
    (" lost capacity ", " improved "),
    (" lost capacity ", " durability "),
    (" capacity dropped ", " durability improved "),
    (" yield dropped ", " yield improved "),
    (" performance fell ", " performance improved "),
    (" output declined ", " output improved "),
)

# Cause/effect inversion: premise asserts X causes Y;
# conclusion asserts Y causes X (or X is caused by Y).
_INVERSION_PAIRS: tuple[tuple[str, str], ...] = (
    (" caused by ", " causes "),
    (" results from ", " results in "),
    (" follows from ", " produces "),
)

# Necessary/sufficient swap: premise asserts X is necessary
# for Y; conclusion treats X as sufficient for Y (or vice
# versa).
_NECESSARY_SUFFICIENT_PAIRS: tuple[tuple[str, str], ...] = (
    (" necessary ", " sufficient "),
    (" sufficient ", " necessary "),
)


def _normalised(text: str) -> str:
    padded = " " + text.lower() + " "
    for ch in ",.:;!?\"'":
        padded = padded.replace(ch, " ")
    return padded


def _has_pair(text: str, pairs: tuple[tuple[str, str], ...]) -> bool:
    padded = _normalised(text)
    return any(a in padded and b in padded for a, b in pairs)


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

    # 1) DIRECT_CONTRADICTION — procedural / temporal
    #    contradiction (the v4.6/v4.7 X2-V028 family).
    if _has_pair(text, _DIRECT_CONTRADICTION_PAIRS):
        return Classification(
            chain_id=record.chain_id,
            failure_class=
                ContentFailure.DIRECT_CONTRADICTION.value,
            rationale=(
                "premise asserts X and conclusion asserts the "
                "explicit negation of X with no qualifier"
            ),
        )

    # 2) PROPERTY_REVERSAL — polarity inversion at the
    #    observable-property level (the D1I007 family).
    if _has_pair(text, _POLARITY_REVERSAL_PAIRS):
        return Classification(
            chain_id=record.chain_id,
            failure_class=
                ContentFailure.PROPERTY_REVERSAL.value,
            rationale=(
                "premise asserts a negative-polarity outcome; "
                "conclusion asserts the positive-polarity form"
            ),
        )

    # 3) CAUSE_EFFECT_INVERSION
    if _has_pair(text, _INVERSION_PAIRS):
        return Classification(
            chain_id=record.chain_id,
            failure_class=
                ContentFailure.CAUSE_EFFECT_INVERSION.value,
            rationale=(
                "cause/effect direction is inverted between "
                "premise and conclusion"
            ),
        )

    # 4) NECESSARY_SUFFICIENT_SWAP
    if _has_pair(text, _NECESSARY_SUFFICIENT_PAIRS):
        return Classification(
            chain_id=record.chain_id,
            failure_class=
                ContentFailure.NECESSARY_SUFFICIENT_SWAP.value,
            rationale=(
                "necessary/sufficient roles are conflated"
            ),
        )

    # 5-8) The remaining v4.8 taxonomy values are kept for
    # completeness — none of them fire on the 9 residue
    # cases. The cascade falls through to UNKNOWN.

    return Classification(
        chain_id=record.chain_id,
        failure_class=ContentFailure.UNKNOWN.value,
        rationale="no content-failure pattern matched",
    )


def classify_all(
    records: tuple[ReplayRecord, ...],
    text_index: dict[str, str],
) -> tuple[Classification, ...]:
    return tuple(
        classify(r, text_index[r.chain_id]) for r in records
    )


__all__ = ["Classification", "classify", "classify_all"]
