"""v17.4 - aggregate metrics, concept gate, and
corpus classification.

Rolls up v17.0-v17.3 into the five directive metrics
and the six-condition concept gate, and assigns the
document space one closed A-E class. Reads only the
sprints' already-published metrics; the per-sprint
safety discipline is inherited.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.sensitive_documents import (
    build_report as _v0_report, entities_remain_neutral,
    provenance_integrity,
    provenance_visibility as _v0_visibility,
)
from desi.sensitive_association import (
    association_resistance, build_report as _v1_report,
    dissent_preservation as _assoc_dissent,
    epistemic_integrity as _assoc_integrity,
    false_certainty_rate as _assoc_false_certainty,
    no_entity_reaches_participation,
)
from desi.sensitive_contamination import (
    build_report as _v2_report, epistemic_hygiene,
    false_certainty_rate as _cont_false_certainty,
    mean_virality, narrative_inflation,
)
from desi.sensitive_ecology import (
    build_report as _v3_report,
    dissent_preservation as _eco_dissent,
    governance_integrity, source_quality_visibility,
)

from .taxonomy import SensitiveDocumentClass, class_rank

# Concept-gate floors / ceilings (directive § v17.4).
GATE_FALSE_CERTAINTY = 0.05
GATE_ASSOCIATION_RESISTANCE = 0.90
GATE_PROVENANCE_VISIBILITY = 0.90
GATE_EPISTEMIC_INTEGRITY = 0.90
GATE_DISSENT_PRESERVATION = 0.90

GATE_PASS_STATEMENT = (
    "DESi kann sensible historische Dokumentraeume "
    "strukturieren ohne epistemische oder moralische "
    "Autoritaet zu beanspruchen."
)
GATE_FAIL_STATEMENT = (
    "DESi bleibt epistemisch instabil gegenueber "
    "hochkontaminierten Dokumentraeumen."
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def false_certainty_rate() -> float:
    """Worst (highest) false-certainty rate across the
    association and contamination sprints."""
    return _round(max(
        _assoc_false_certainty(),
        _cont_false_certainty(),
    ))


def provenance_visibility() -> float:
    """Mean of document provenance visibility (v17.0)
    and long-horizon source-quality visibility
    (v17.3)."""
    return _round(_mean([
        _v0_visibility(),
        source_quality_visibility(),
    ]))


def dissent_preservation() -> float:
    """Worst (lowest) dissent preservation across the
    association and ecology sprints."""
    return _round(min(
        _assoc_dissent(), _eco_dissent(),
    ))


def epistemic_integrity() -> float:
    """Aggregate epistemic integrity across the
    sprints: association integrity, contamination
    hygiene, long-horizon governance, and the
    entity-neutrality guarantee."""
    return _round(_mean([
        _assoc_integrity(),
        epistemic_hygiene(),
        governance_integrity(),
        1.0 if entities_remain_neutral() else 0.0,
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
        false_certainty_rate(),
        association_resistance(),
        provenance_visibility(),
        epistemic_integrity(),
        dissent_preservation(),
    )


def _meta_replay() -> float:
    if min(_sub_replays()) < 1.0:
        return 0.0
    return 1.0 if _aggregate_tuple() == (
        _aggregate_tuple()
    ) else 0.0


@dataclass(frozen=True)
class AggregateMetrics:
    epistemic_integrity: float
    association_resistance: float
    false_certainty_rate: float
    provenance_visibility: float
    dissent_preservation: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "epistemic_integrity":
                self.epistemic_integrity,
            "association_resistance":
                self.association_resistance,
            "false_certainty_rate":
                self.false_certainty_rate,
            "provenance_visibility":
                self.provenance_visibility,
            "dissent_preservation":
                self.dissent_preservation,
            "replay_stability": self.replay_stability,
        }


def aggregate() -> AggregateMetrics:
    return AggregateMetrics(
        epistemic_integrity=epistemic_integrity(),
        association_resistance=association_resistance(),
        false_certainty_rate=false_certainty_rate(),
        provenance_visibility=provenance_visibility(),
        dissent_preservation=dissent_preservation(),
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
            "false_certainty_rate", m.false_certainty_rate,
            GATE_FALSE_CERTAINTY, "<=",
            m.false_certainty_rate <= GATE_FALSE_CERTAINTY,
        ),
        (
            "association_resistance",
            m.association_resistance,
            GATE_ASSOCIATION_RESISTANCE, ">=",
            m.association_resistance
            >= GATE_ASSOCIATION_RESISTANCE,
        ),
        (
            "provenance_visibility",
            m.provenance_visibility,
            GATE_PROVENANCE_VISIBILITY, ">=",
            m.provenance_visibility
            >= GATE_PROVENANCE_VISIBILITY,
        ),
        (
            "epistemic_integrity", m.epistemic_integrity,
            GATE_EPISTEMIC_INTEGRITY, ">=",
            m.epistemic_integrity
            >= GATE_EPISTEMIC_INTEGRITY,
        ),
        (
            "dissent_preservation",
            m.dissent_preservation,
            GATE_DISSENT_PRESERVATION, ">=",
            m.dissent_preservation
            >= GATE_DISSENT_PRESERVATION,
        ),
        (
            "replay_stability", m.replay_stability, 1.0,
            "==", m.replay_stability == 1.0,
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


def contamination_present() -> bool:
    return (
        mean_virality() >= 0.50
        or provenance_integrity() < 0.70
    )


def classify_corpus() -> str:
    """Priority-ordered A-E classification of the
    document space (most hazardous wins). Descriptive
    only - never a finding about a person."""
    C = SensitiveDocumentClass
    if (
        false_certainty_rate() > GATE_FALSE_CERTAINTY
        or association_resistance()
        < GATE_ASSOCIATION_RESISTANCE
        or not no_entity_reaches_participation()
    ):
        return C.E_EPISTEMICALLY_HAZARDOUS.value
    if narrative_inflation() > 0.05:
        return C.D_NARRATIVE_INFLATED.value
    if contamination_present():
        return C.C_CONTAMINATION_HEAVY_BUT_STABLE.value
    if provenance_integrity() < 0.90:
        return C.B_STRUCTURALLY_TRANSPARENT.value
    return C.A_EPISTEMICALLY_DISCIPLINED.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "AggregateMetrics",
    "GateCondition",
    "aggregate",
    "association_resistance",
    "class_rank",
    "classify_corpus",
    "contamination_present",
    "dissent_preservation",
    "epistemic_integrity",
    "false_certainty_rate",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "provenance_visibility",
]
