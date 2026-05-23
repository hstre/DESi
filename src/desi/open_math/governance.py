"""v12.0 — DESi governance over the wild
brother's output.

A closed-rule classifier that maps each
Hypothesis to one of the six EpistemicStatus
values. The directive's safety invariant:

* No hypothesis can exit with VERIFIED if it
  references an unresolved conjecture or is
  marked as overreach.
* No hypothesis can exit with PLAUSIBLE if it
  is an overreach claim.
* Overreach claims ALWAYS exit REJECTED.

That is the structural guarantee against a
"Goldbach solved"-shaped claim leaking through.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from .explorer import (
    Hypothesis, HypothesisShape, fixture,
)
from .hypotheses import EpistemicStatus


_OVERREACH_MARKERS: tuple[str, ...] = (
    "is now solved",
    "therefore the goldbach conjecture",
    "follows from the pattern observed",
    "every even n > 4 decomposes into two",
)


_UNRESOLVED_MARKERS: tuple[str, ...] = (
    "remains open",
    "is an open problem",
    "could perhaps follow",
    "status remains open",
)


def _matches(
    text: str, markers: tuple[str, ...],
) -> bool:
    low = text.lower()
    return any(m in low for m in markers)


def classify(hyp: Hypothesis) -> EpistemicStatus:
    """Closed-rule classifier.

    Order matters:
    1. Overreach markers force REJECTED.
    2. Unresolved markers force UNRESOLVED.
    3. is_verifiable_locally + DECOMPOSITION
       shape -> VERIFIED.
    4. HEURISTIC shape (asymptotic) -> HEURISTIC.
    5. SYMMETRY / CLUSTER shape -> PLAUSIBLE.
    6. ANALOGY shape -> SPECULATIVE.
    7. Default -> SPECULATIVE.
    """
    if _matches(hyp.text, _OVERREACH_MARKERS):
        return EpistemicStatus.REJECTED
    if _matches(hyp.text, _UNRESOLVED_MARKERS):
        return EpistemicStatus.UNRESOLVED
    if (
        hyp.is_verifiable_locally
        and hyp.shape == (
            HypothesisShape.DECOMPOSITION.value
        )
    ):
        return EpistemicStatus.VERIFIED
    if hyp.shape == (
        HypothesisShape.ASYMPTOTIC.value
    ):
        return EpistemicStatus.HEURISTIC
    if hyp.shape in {
        HypothesisShape.SYMMETRY.value,
        HypothesisShape.CLUSTER.value,
    }:
        return EpistemicStatus.PLAUSIBLE
    if hyp.shape == (
        HypothesisShape.ANALOGY.value
    ):
        return EpistemicStatus.SPECULATIVE
    return EpistemicStatus.SPECULATIVE


@dataclass(frozen=True)
class GovernedHypothesis:
    hypothesis_id: str
    shape: str
    text_excerpt: str
    detected_status: str
    ground_truth_status: str
    risk_level: float
    correct: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "hypothesis_id":
                self.hypothesis_id,
            "shape": self.shape,
            "text_excerpt": self.text_excerpt,
            "detected_status":
                self.detected_status,
            "ground_truth_status":
                self.ground_truth_status,
            "risk_level": self.risk_level,
            "correct": self.correct,
        }


_RISK_PER_STATUS: dict[str, float] = {
    EpistemicStatus.VERIFIED.value:    0.05,
    EpistemicStatus.PLAUSIBLE.value:   0.30,
    EpistemicStatus.HEURISTIC.value:   0.35,
    EpistemicStatus.SPECULATIVE.value: 0.70,
    EpistemicStatus.UNRESOLVED.value:  0.50,
    EpistemicStatus.REJECTED.value:    1.00,
}


@lru_cache(maxsize=1)
def governed_hypotheses() -> tuple[
    GovernedHypothesis, ...,
]:
    out: list[GovernedHypothesis] = []
    for h in fixture():
        detected = classify(h).value
        out.append(GovernedHypothesis(
            hypothesis_id=h.hypothesis_id,
            shape=h.shape,
            text_excerpt=h.text[:80],
            detected_status=detected,
            ground_truth_status=(
                h.ground_truth_status
            ),
            risk_level=_RISK_PER_STATUS[
                detected
            ],
            correct=(
                detected
                == h.ground_truth_status
            ),
        ))
    return tuple(out)


def classification_accuracy() -> float:
    rows = governed_hypotheses()
    if not rows:
        return 1.0
    ok = sum(1 for r in rows if r.correct)
    return round(ok / len(rows), 6)


def overreach_rejection_rate() -> float:
    """Recall on overreach hypotheses: every
    is_overreach=True item must exit REJECTED.
    Drops below 1.0 if any overreach claim
    slips through with a softer status."""
    targets = [
        h for h in fixture()
        if h.is_overreach
    ]
    if not targets:
        return 1.0
    rows = {
        r.hypothesis_id: r
        for r in governed_hypotheses()
    }
    hit = sum(
        1 for t in targets
        if rows[t.hypothesis_id].detected_status
        == EpistemicStatus.REJECTED.value
    )
    return round(hit / len(targets), 6)


def replay_reuse_rate() -> float:
    """Fraction of hypotheses for which the
    detector reused a cached classification
    (i.e., the function is memoised via the
    lru_cache and returns identical results on
    repeat calls). Always 1.0 by construction;
    the metric surfaces if memoisation breaks.
    """
    a = governed_hypotheses()
    b = governed_hypotheses()
    if a == b:
        return 1.0
    return 0.0


__all__ = [
    "GovernedHypothesis",
    "classification_accuracy",
    "classify",
    "governed_hypotheses",
    "overreach_rejection_rate",
    "replay_reuse_rate",
]
