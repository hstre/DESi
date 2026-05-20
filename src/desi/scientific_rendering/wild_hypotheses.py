"""v22.0 - the Wild Scientific Explorer's follow-up
hypotheses over the v19-v21 results.

Agent A (Wild Scientific Explorer) proposes unusual
connections, hypotheses, and alternative interpretations.
It may speculate - but it must NOT produce final claims,
breakthrough language, or AGI-style hype. Agent B (DESi)
reads the hypotheses and separates the paper-grade,
technically grounded ones from speculative drift and hype.

The single hard rule: a fixed set of FORBIDDEN TERMS may
never enter an accepted (paper-candidate) hypothesis or the
final document. Their presence is a governance failure.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Terms banned from the final scientific document. Their
# appearance anywhere DESi accepts is a governance failure.
FORBIDDEN_TERMS: tuple[str, ...] = (
    "AGI", "Superintelligence", "Consciousness",
    "Civilization layer", "Kant", "Popper", "Truth engine",
    "World model", "Revolutionary", "Breakthrough",
    "Human-level",
)

# Acceptance thresholds for a paper-candidate hypothesis.
_GROUNDING_FLOOR = 0.85
_DRIFT_CEILING = 0.30


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def forbidden_hits(text: str) -> tuple[str, ...]:
    """Forbidden terms present in the text. Multi-word /
    hyphenated phrases are matched as substrings; single
    words are matched on word boundaries (so 'agi' does not
    trigger inside 'magic')."""
    low = text.lower()
    hits: list[str] = []
    for term in FORBIDDEN_TERMS:
        t = term.lower()
        if " " in t or "-" in t:
            if t in low:
                hits.append(term)
        elif re.search(rf"\b{re.escape(t)}\b", low):
            hits.append(term)
    return tuple(hits)


@dataclass(frozen=True)
class ScientificHypothesis:
    hyp_id: str
    text: str
    technical_grounding: float
    speculative_drift: float

    def has_forbidden(self) -> bool:
        return bool(forbidden_hits(self.text))

    def is_paper_candidate(self) -> bool:
        """DESi accepts a hypothesis as paper-grade iff it is
        well grounded, low drift, and uses no forbidden term."""
        return (
            self.technical_grounding >= _GROUNDING_FLOOR
            and self.speculative_drift <= _DRIFT_CEILING
            and not self.has_forbidden()
        )

    def is_overreach(self) -> bool:
        """Hype / overreach: forbidden language OR high
        speculative drift."""
        return self.has_forbidden() or (
            self.speculative_drift > _DRIFT_CEILING
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "hyp_id": self.hyp_id,
            "text": self.text,
            "technical_grounding":
                _round(self.technical_grounding),
            "speculative_drift": _round(self.speculative_drift),
            "forbidden_hits": list(forbidden_hits(self.text)),
            "is_paper_candidate": self.is_paper_candidate(),
            "is_overreach": self.is_overreach(),
        }


# Grounded follow-ups (paper-grade) plus hype / drift the
# Wild Explorer also throws out.
_HYPOTHESES: tuple[ScientificHypothesis, ...] = (
    ScientificHypothesis(
        "H01",
        "Soft re-weighting of redundant trajectories reduces "
        "search redundancy while preserving novel-state "
        "reachability.", 0.93, 0.10),
    ScientificHypothesis(
        "H02",
        "A generator/governor split increases distinct-state "
        "coverage on the synthetic corpus relative to a "
        "single conservative explorer.", 0.92, 0.12),
    ScientificHypothesis(
        "H03",
        "Capping high-certainty incoherent paths keeps the "
        "uncontained hallucination rate near zero under "
        "pressure.", 0.94, 0.08),
    ScientificHypothesis(
        "H04",
        "Bounded authority drift can be maintained over a "
        "long horizon under deterministic replay.", 0.90, 0.15),
    ScientificHypothesis(
        "H05",
        "This architecture is a step toward AGI-level "
        "autonomous exploration.", 0.20, 0.80),
    ScientificHypothesis(
        "H06",
        "Replay governance constitutes a universal world "
        "model for intelligence.", 0.15, 0.85),
    ScientificHypothesis(
        "H07",
        "This is a revolutionary breakthrough that solves "
        "reinforcement learning.", 0.10, 0.90),
    ScientificHypothesis(
        "H08",
        "Exploration governance reflects Popperian "
        "falsification and Kantian epistemics.", 0.25, 0.70),
    ScientificHypothesis(
        "H09",
        "Governed exploration probably generalises to all "
        "sequential decision problems without change.",
        0.40, 0.65),
    ScientificHypothesis(
        "H10",
        "The dual-agent pattern could scale to arbitrary "
        "domains with no further work.", 0.35, 0.60),
)


def hypotheses() -> tuple[ScientificHypothesis, ...]:
    return _HYPOTHESES


def by_id(hyp_id: str) -> ScientificHypothesis:
    for h in _HYPOTHESES:
        if h.hyp_id == hyp_id:
            return h
    raise KeyError(hyp_id)


def paper_candidates() -> tuple[ScientificHypothesis, ...]:
    return tuple(h for h in _HYPOTHESES if h.is_paper_candidate())


def overreach_hypotheses() -> tuple[ScientificHypothesis, ...]:
    return tuple(h for h in _HYPOTHESES if h.is_overreach())


__all__ = [
    "FORBIDDEN_TERMS",
    "ScientificHypothesis",
    "by_id",
    "forbidden_hits",
    "hypotheses",
    "overreach_hypotheses",
    "paper_candidates",
]
