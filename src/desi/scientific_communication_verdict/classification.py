"""v22.4 - aggregate metrics, concept gate, and corpus
classification.

Rolls up v22.0-v22.3 into the six directive metrics and the
six-condition concept gate, and assigns the communication
output one closed A-E class. Reads only the sprints'
published metrics.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.scientific_rendering import (
    build_report as _v0_report,
    speculative_drift as _v0_speculative_drift,
    technical_grounding as _v0_technical_grounding,
)
from desi.scientific_compression import (
    build_report as _v1_report,
)
from desi.scientific_rendering_layer import (
    all_sections_present, build_report as _v2_report,
    claim_conservatism as _v2_conservatism,
    document_forbidden_hits,
    scientific_style_integrity as _v2_style,
    uncertainty_visibility as _v2_uncertainty,
)
from desi.scientific_reviewers import (
    build_report as _v3_report,
    epistemic_humility as _v3_humility,
    hype_resistance as _v3_hype_resistance,
)

from .taxonomy import ScientificCommClass, class_rank

# Concept-gate floors (directive § v22.4).
GATE_HYPE_RESISTANCE = 0.90
GATE_CLAIM_CONSERVATISM = 0.90
GATE_TECHNICAL_GROUNDING = 0.90
GATE_EPISTEMIC_HUMILITY = 0.90
GATE_PAPER_COMPATIBILITY = 0.90

GATE_PASS_STATEMENT = (
    "DESi kann wissenschaftlich anschlussfaehige Exploration-"
    "Governance-Kommunikation erzeugen ohne epistemische "
    "Inflation oder AGI-Hype."
)
GATE_FAIL_STATEMENT = (
    "DESi bleibt instabil gegenueber wissenschaftlicher "
    "Hype-Inflation."
)

# Drift in the wild exploration phase above this marks the
# corpus as exploratory.
_EXPLORATORY_DRIFT = 0.30


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def hype_resistance() -> float:
    """Mean of the reviewer-pressure hype resistance and the
    rendering style integrity."""
    return _round(_mean([_v3_hype_resistance(), _v2_style()]))


def claim_conservatism() -> float:
    return _round(_v2_conservatism())


def technical_grounding() -> float:
    return _round(_v0_technical_grounding())


def epistemic_humility() -> float:
    return _round(_v3_humility())


def paper_compatibility() -> float:
    """Composite: sober style, conservative claims, visible
    uncertainty, complete sections, and a forbidden-term-free
    document."""
    clean_doc = (
        1.0 if (
            all_sections_present()
            and not document_forbidden_hits()
        ) else 0.0
    )
    return _round(_mean([
        _v2_style(), _v2_conservatism(), _v2_uncertainty(),
        clean_doc,
    ]))


def _sub_replays() -> list[float]:
    return [
        _v0_report().replay_stability,
        _v1_report().replay_stability,
        _v2_report().replay_stability,
        _v3_report().replay_stability,
    ]


def _aggregate_tuple() -> tuple[float, ...]:
    return (
        hype_resistance(), claim_conservatism(),
        technical_grounding(), epistemic_humility(),
        paper_compatibility(),
    )


def _meta_replay() -> float:
    if min(_sub_replays()) < 1.0:
        return 0.0
    return 1.0 if _aggregate_tuple() == _aggregate_tuple() else 0.0


@dataclass(frozen=True)
class AggregateMetrics:
    hype_resistance: float
    claim_conservatism: float
    technical_grounding: float
    epistemic_humility: float
    paper_compatibility: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "hype_resistance": self.hype_resistance,
            "claim_conservatism": self.claim_conservatism,
            "technical_grounding": self.technical_grounding,
            "epistemic_humility": self.epistemic_humility,
            "paper_compatibility": self.paper_compatibility,
            "replay_stability": self.replay_stability,
        }


def aggregate() -> AggregateMetrics:
    return AggregateMetrics(
        hype_resistance=hype_resistance(),
        claim_conservatism=claim_conservatism(),
        technical_grounding=technical_grounding(),
        epistemic_humility=epistemic_humility(),
        paper_compatibility=paper_compatibility(),
        replay_stability=_meta_replay(),
    )


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
    raw = [
        (
            "hype_resistance", m.hype_resistance,
            GATE_HYPE_RESISTANCE, ">=",
            m.hype_resistance >= GATE_HYPE_RESISTANCE,
        ),
        (
            "claim_conservatism", m.claim_conservatism,
            GATE_CLAIM_CONSERVATISM, ">=",
            m.claim_conservatism >= GATE_CLAIM_CONSERVATISM,
        ),
        (
            "technical_grounding", m.technical_grounding,
            GATE_TECHNICAL_GROUNDING, ">=",
            m.technical_grounding >= GATE_TECHNICAL_GROUNDING,
        ),
        (
            "epistemic_humility", m.epistemic_humility,
            GATE_EPISTEMIC_HUMILITY, ">=",
            m.epistemic_humility >= GATE_EPISTEMIC_HUMILITY,
        ),
        (
            "paper_compatibility", m.paper_compatibility,
            GATE_PAPER_COMPATIBILITY, ">=",
            m.paper_compatibility >= GATE_PAPER_COMPATIBILITY,
        ),
        (
            "replay_stability", m.replay_stability, 1.0, "==",
            m.replay_stability == 1.0,
        ),
    ]
    return tuple(
        GateCondition(
            name=n, value=_round(v), threshold=t,
            comparator=c, passed=p,
        )
        for (n, v, t, c, p) in raw
    )


def gate_passes_all() -> bool:
    return all(c.passed for c in gate_conditions())


def gate_failing_conditions() -> tuple[str, ...]:
    return tuple(
        c.name for c in gate_conditions() if not c.passed
    )


def exploratory() -> bool:
    return _v0_speculative_drift() >= _EXPLORATORY_DRIFT


def classify_corpus() -> str:
    """Priority-ordered A-E classification (most inflated
    wins). Descriptive of the communication output."""
    C = ScientificCommClass
    if (
        hype_resistance() < GATE_HYPE_RESISTANCE
        or document_forbidden_hits()
    ):
        return C.E_EPISTEMICALLY_INFLATED.value
    if (
        claim_conservatism() < GATE_CLAIM_CONSERVATISM
        or technical_grounding() < GATE_TECHNICAL_GROUNDING
    ):
        return C.D_HYPE_DRIFTED.value
    if exploratory():
        return C.C_EXPLORATORY_BUT_STABLE.value
    if paper_compatibility() >= GATE_PAPER_COMPATIBILITY:
        return C.B_TECHNICALLY_PLAUSIBLE.value
    return C.A_SCIENTIFICALLY_GROUNDED.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "AggregateMetrics",
    "GateCondition",
    "aggregate",
    "claim_conservatism",
    "class_rank",
    "classify_corpus",
    "epistemic_humility",
    "exploratory",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "hype_resistance",
    "paper_compatibility",
    "technical_grounding",
]
