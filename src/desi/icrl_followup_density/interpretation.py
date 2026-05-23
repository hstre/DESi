"""v23.2 - result interpretation and explicit hypotheses.

For each headline result, states what it means and - just as
importantly - what it does not mean, so the interpretation is
bounded. Forward-looking statements are kept separate and
must each carry an explicit hedge marker, so a hypothesis is
never dressed up as a result.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from desi.icrl_followup_conditions import by_result_id

# Markers that explicitly flag a statement as a hypothesis /
# forward-looking rather than an established result.
_HEDGE_MARKERS: tuple[str, ...] = (
    "hypothesise", "hypothesis", "conjecture", "may ", "might ",
    "could ", "would ", "remains open", "future work",
    "is expected", "we expect", "suggests", "open question",
)


def is_marked_hypothesis(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in _HEDGE_MARKERS)


@dataclass(frozen=True)
class Interpretation:
    result_id: str
    means: str
    does_not_mean: str

    def is_bounded(self) -> bool:
        return bool(self.means.strip()) and bool(
            self.does_not_mean.strip()
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "result_id": self.result_id,
            "means": self.means,
            "does_not_mean": self.does_not_mean,
            "is_bounded": self.is_bounded(),
        }


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    text: str

    def is_marked(self) -> bool:
        return is_marked_hypothesis(self.text)

    def to_dict(self) -> dict[str, object]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "text": self.text,
            "is_marked": self.is_marked(),
        }


def _interpretations() -> tuple[Interpretation, ...]:
    r1 = by_result_id("R1").value
    r7 = by_result_id("R7").value
    return (
        Interpretation(
            "R1",
            f"the governor moved {r1} of the redundant search "
            "weight away on the synthetic corpus",
            "that redundancy was removed in any real "
            "environment or that optimal exploration is "
            "guaranteed"),
        Interpretation(
            "R3",
            "high-certainty incoherent paths were capped so "
            "residual hallucination reached zero on the "
            "fixtures",
            "that hallucination is solved in general or that "
            "the governor validates truth"),
        Interpretation(
            "R7",
            f"the dual-agent design covered {r7} times the "
            "distinct states of DESi-alone on the fixtures",
            "that DESi is that much better at real "
            "reinforcement learning or that it replaces it"),
    )


def _hypotheses() -> tuple[Hypothesis, ...]:
    return (
        Hypothesis(
            "H1",
            "We hypothesise that the same read-only re-"
            "weighting could reduce redundancy in a non-"
            "synthetic ICRL setting, but this remains open."),
        Hypothesis(
            "H2",
            "Containment of high-certainty incoherent paths "
            "may generalise beyond the fixtures; future work "
            "would need a real generator to test it."),
        Hypothesis(
            "H3",
            "We conjecture that bounded drift could hold under "
            "longer horizons, though we test only 5600 steps."),
        Hypothesis(
            "H4",
            "The diversity-preserving effect might depend on "
            "the negotiation rule; this is an open question, "
            "not a result."),
    )


def interpretations() -> tuple[Interpretation, ...]:
    return _interpretations()


def hypotheses() -> tuple[Hypothesis, ...]:
    return _hypotheses()


def unmarked_hypotheses() -> tuple[str, ...]:
    return tuple(
        h.hypothesis_id for h in _hypotheses()
        if not h.is_marked()
    )


def unbounded_interpretations() -> tuple[str, ...]:
    return tuple(
        i.result_id for i in _interpretations()
        if not i.is_bounded()
    )


def hypothesis_visibility() -> float:
    """Fraction of forward-looking statements explicitly
    marked as hypotheses, in [0, 1]."""
    rows = _hypotheses()
    if not rows:
        return 0.0
    marked = sum(1 for h in rows if h.is_marked())
    return round(marked / len(rows), 6)


__all__ = [
    "Hypothesis",
    "Interpretation",
    "hypotheses",
    "hypothesis_visibility",
    "interpretations",
    "is_marked_hypothesis",
    "unbounded_interpretations",
    "unmarked_hypotheses",
]
