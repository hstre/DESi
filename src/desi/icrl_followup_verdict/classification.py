"""v23.4 - aggregate metrics, Concept Gate, classification.

Pulls one signal per gate dimension from the lower follow-up
layers (v23.0 anchoring, v23.1 conditions, v23.2 density,
v23.3 relevance), checks the six-condition Concept Gate, and
classifies the follow-up on the closed A-E taxonomy.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from desi.scientific_rendering import forbidden_hits

from desi.icrl_followup_revision import (
    claims, paper_alignment, related_work_section,
    unconnected_claims,
)
from desi.icrl_followup_revision import (
    build_report as _v230_report,
)
from desi.icrl_followup_conditions import (
    provenance_section, result_traceability,
)
from desi.icrl_followup_conditions import (
    build_report as _v231_report,
)
from desi.icrl_followup_density import (
    claim_conservatism, density_sections,
)
from desi.icrl_followup_density import (
    build_report as _v232_report,
)
from desi.icrl_followup_relevance import (
    author_relevance, hype_probability, relevance_section,
    spam_probability,
)
from desi.icrl_followup_relevance import (
    build_report as _v233_report,
)

from .taxonomy import FollowupClass

GATE_PASS_STATEMENT = (
    "DESi kann direkt anschlussfaehige wissenschaftliche "
    "Follow-Up-Kommunikation erzeugen ohne Hype oder "
    "epistemische Inflation."
)

_FLOOR = 0.90        # gate floor for the five fraction metrics
_HIGH = 0.95         # bar for the top descriptive class A
_DISMISS_CEIL = 0.10  # max tolerated spam / hype probability


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def technical_grounding() -> float:
    """Fraction of central claims grounded in a concrete
    sprint result (anchored to a base problem and citing a
    sprint source), in [0, 1]."""
    rows = claims()
    if not rows:
        return 0.0
    grounded = sum(
        1 for c in rows
        if c.is_anchored() and bool(c.sprint_source)
    )
    return _round(grounded / len(rows))


@lru_cache(maxsize=1)
def _lower_replays() -> tuple[float, ...]:
    return (
        _v230_report().replay_stability,
        _v231_report().replay_stability,
        _v232_report().replay_stability,
        _v233_report().replay_stability,
    )


@dataclass(frozen=True)
class FollowupMetrics:
    paper_alignment: float
    result_traceability: float
    technical_grounding: float
    claim_conservatism: float
    author_relevance: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "paper_alignment": self.paper_alignment,
            "result_traceability": self.result_traceability,
            "technical_grounding": self.technical_grounding,
            "claim_conservatism": self.claim_conservatism,
            "author_relevance": self.author_relevance,
            "replay_stability": self.replay_stability,
        }


def _metric_values() -> tuple[float, float, float, float, float]:
    return (
        paper_alignment(),
        result_traceability(),
        technical_grounding(),
        claim_conservatism(),
        author_relevance(),
    )


def replay_stability() -> float:
    """1.0 iff the aggregate metric tuple is bit-identical on
    a second computation and every lower follow-up layer is
    replay-stable."""
    if _metric_values() != _metric_values():
        return 0.0
    if any(r != 1.0 for r in _lower_replays()):
        return 0.0
    return 1.0


@lru_cache(maxsize=1)
def aggregate() -> FollowupMetrics:
    pa, rt, tg, cc, ar = _metric_values()
    return FollowupMetrics(
        paper_alignment=pa,
        result_traceability=rt,
        technical_grounding=tg,
        claim_conservatism=cc,
        author_relevance=ar,
        replay_stability=replay_stability(),
    )


@lru_cache(maxsize=1)
def cached_sections() -> tuple[str, str, str, str]:
    """The four lower-layer markdown sections, built once. They
    are deterministic and read-only, so caching is safe and
    avoids rebuilding the lower-layer results repeatedly."""
    return (
        related_work_section(),
        density_sections(),
        provenance_section(),
        relevance_section(),
    )


def all_followup_text() -> str:
    return "\n".join(cached_sections())


@lru_cache(maxsize=1)
def followup_forbidden_hits() -> tuple[str, ...]:
    return tuple(sorted(set(
        forbidden_hits(all_followup_text())
    )))


@dataclass(frozen=True)
class GateCondition:
    name: str
    value: float
    threshold: float
    comparator: str
    passed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "value": self.value,
            "threshold": self.threshold,
            "comparator": self.comparator,
            "passed": self.passed,
        }


def gate_conditions() -> tuple[GateCondition, ...]:
    m = aggregate()
    return (
        GateCondition(
            "paper_alignment", m.paper_alignment, _FLOOR,
            ">=", m.paper_alignment >= _FLOOR),
        GateCondition(
            "result_traceability", m.result_traceability,
            _FLOOR, ">=", m.result_traceability >= _FLOOR),
        GateCondition(
            "technical_grounding", m.technical_grounding,
            _FLOOR, ">=", m.technical_grounding >= _FLOOR),
        GateCondition(
            "claim_conservatism", m.claim_conservatism, _FLOOR,
            ">=", m.claim_conservatism >= _FLOOR),
        GateCondition(
            "author_relevance", m.author_relevance, _FLOOR,
            ">=", m.author_relevance >= _FLOOR),
        GateCondition(
            "replay_stability", m.replay_stability, 1.0,
            "==", m.replay_stability == 1.0),
    )


def gate_passes_all() -> bool:
    return all(c.passed for c in gate_conditions())


def gate_failing_conditions() -> tuple[str, ...]:
    return tuple(
        c.name for c in gate_conditions() if not c.passed
    )


@lru_cache(maxsize=1)
def classify_corpus() -> str:
    """Priority-ordered classification on the closed A-E
    taxonomy (most severe failure first)."""
    m = aggregate()
    # E - hype / epistemic inflation (a governance failure)
    if (
        followup_forbidden_hits()
        or m.claim_conservatism < _FLOOR
        or hype_probability() > _DISMISS_CEIL
    ):
        return FollowupClass.E_HYPE_INFLATED.value
    # D - disconnected from the base paper's open problems
    if (
        m.paper_alignment < _FLOOR
        or m.author_relevance < _FLOOR
        or unconnected_claims()
    ):
        return FollowupClass.D_DISCONNECTED.value
    # C - grounded and scoped, but reads as exploratory
    if (
        m.author_relevance < _HIGH
        or spam_probability() > _DISMISS_CEIL
        or m.result_traceability < _HIGH
    ):
        return FollowupClass.C_EXPLORATORY_BUT_GROUNDED.value
    # B - technically grounded and relevant, not maximally so
    if (
        m.technical_grounding < _HIGH
        or m.paper_alignment < _HIGH
    ):
        return FollowupClass.B_TECHNICALLY_INTERESTING.value
    # A - directly continues the open exploration question
    return FollowupClass.A_DIRECTLY_RELEVANT.value


__all__ = [
    "GATE_PASS_STATEMENT",
    "FollowupMetrics",
    "GateCondition",
    "aggregate",
    "all_followup_text",
    "cached_sections",
    "classify_corpus",
    "followup_forbidden_hits",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "replay_stability",
    "technical_grounding",
]
