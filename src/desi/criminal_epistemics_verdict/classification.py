"""v16.4 - aggregate metrics, concept gate, and
corpus classification.

Rolls up v16.0-v16.3 into the five directive
metrics and the six-condition concept gate, and
assigns the corpus one closed A-E class.

The post-hoc-free discipline of each sprint is
inherited; this layer only reads the sprints'
already-published metrics.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.criminal_epistemics import (
    build_report as _v0_report, conflict_clusters,
    source_dependency, uncertainty_visible,
)
from desi.criminal_narrative_competition import (
    build_report as _v1_report, no_preferred_narrative,
)
from desi.criminal_escalation_resistance import (
    build_report as _v2_report, dissent_preservation,
    epistemic_integrity as _escalation_integrity,
    escalation_resistance, false_certainty_rate,
    speculation_growth,
)
from desi.criminal_historical_ecology import (
    build_report as _v3_report, epistemic_stability,
    governance_stable,
    independent_evidence_preservation,
)

from .taxonomy import (
    CriminalEpistemicsClass, class_rank,
)

# Concept-gate floors / ceilings (directive § v16.4).
GATE_FALSE_CERTAINTY = 0.05
GATE_SPECULATION_RESISTANCE = 0.90
GATE_DISSENT_PRESERVATION = 0.90
GATE_EPISTEMIC_INTEGRITY = 0.90
GATE_INDEPENDENT_EVIDENCE = 0.90

GATE_PASS_STATEMENT = (
    "DESi kann historische Kriminalfaelle epistemisch "
    "strukturieren ohne narrative Autoritaet zu "
    "beanspruchen."
)
GATE_FAIL_STATEMENT = (
    "DESi bleibt epistemisch instabil gegenueber "
    "historischen Kontroversen."
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def speculation_resistance() -> float:
    """How well DESi resisted escalation: the mean
    of its neutralisation rate and the complement
    of the permitted speculation growth."""
    return _round(_mean([
        escalation_resistance(),
        1.0 - speculation_growth(),
    ]))


def epistemic_integrity() -> float:
    """Aggregate epistemic integrity across the
    sprints: escalation integrity, long-horizon
    stability, visible uncertainty, and the no-
    preference governance invariant."""
    return _round(_mean([
        _escalation_integrity(),
        epistemic_stability(),
        1.0 if uncertainty_visible() else 0.0,
        1.0 if no_preferred_narrative() else 0.0,
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
        speculation_resistance(),
        dissent_preservation(),
        epistemic_integrity(),
        independent_evidence_preservation(),
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
    speculation_resistance: float
    false_certainty_rate: float
    dissent_preservation: float
    independent_evidence_preservation: float
    replay_stability: float

    def to_dict(self) -> dict[str, object]:
        return {
            "epistemic_integrity":
                self.epistemic_integrity,
            "speculation_resistance":
                self.speculation_resistance,
            "false_certainty_rate":
                self.false_certainty_rate,
            "dissent_preservation":
                self.dissent_preservation,
            "independent_evidence_preservation":
                self.independent_evidence_preservation,
            "replay_stability": self.replay_stability,
        }


def aggregate() -> AggregateMetrics:
    return AggregateMetrics(
        epistemic_integrity=epistemic_integrity(),
        speculation_resistance=speculation_resistance(),
        false_certainty_rate=false_certainty_rate(),
        dissent_preservation=dissent_preservation(),
        independent_evidence_preservation=(
            independent_evidence_preservation()
        ),
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
            "false_certainty_rate",
            m.false_certainty_rate,
            GATE_FALSE_CERTAINTY, "<=",
            m.false_certainty_rate
            <= GATE_FALSE_CERTAINTY,
        ),
        (
            "speculation_resistance",
            m.speculation_resistance,
            GATE_SPECULATION_RESISTANCE, ">=",
            m.speculation_resistance
            >= GATE_SPECULATION_RESISTANCE,
        ),
        (
            "dissent_preservation",
            m.dissent_preservation,
            GATE_DISSENT_PRESERVATION, ">=",
            m.dissent_preservation
            >= GATE_DISSENT_PRESERVATION,
        ),
        (
            "epistemic_integrity",
            m.epistemic_integrity,
            GATE_EPISTEMIC_INTEGRITY, ">=",
            m.epistemic_integrity
            >= GATE_EPISTEMIC_INTEGRITY,
        ),
        (
            "independent_evidence_preservation",
            m.independent_evidence_preservation,
            GATE_INDEPENDENT_EVIDENCE, ">=",
            m.independent_evidence_preservation
            >= GATE_INDEPENDENT_EVIDENCE,
        ),
        (
            "replay_stability",
            m.replay_stability, 1.0, "==",
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
        c.name for c in gate_conditions()
        if not c.passed
    )


def conflict_cluster_count() -> int:
    return len(conflict_clusters())


def classify_corpus() -> str:
    """Priority-ordered A-E classification of the
    corpus's epistemic state (most unstable wins).
    Descriptive only - never a finding about the
    case."""
    C = CriminalEpistemicsClass
    if (
        not governance_stable()
        or epistemic_stability() < 0.90
    ):
        return C.E_MYTHOLOGICALLY_UNSTABLE.value
    if (
        false_certainty_rate() > GATE_FALSE_CERTAINTY
        or speculation_resistance()
        < GATE_SPECULATION_RESISTANCE
    ):
        return C.D_SPECULATION_DOMINATED.value
    if conflict_cluster_count() >= 2:
        return C.C_CONFLICT_HEAVY_BUT_STABLE.value
    if source_dependency() >= 0.40:
        return C.B_STRUCTURALLY_TRANSPARENT.value
    return C.A_EPISTEMICALLY_DISCIPLINED.value


__all__ = [
    "GATE_FAIL_STATEMENT",
    "GATE_PASS_STATEMENT",
    "AggregateMetrics",
    "GateCondition",
    "aggregate",
    "class_rank",
    "classify_corpus",
    "conflict_cluster_count",
    "epistemic_integrity",
    "gate_conditions",
    "gate_failing_conditions",
    "gate_passes_all",
    "speculation_resistance",
]
