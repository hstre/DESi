"""v18.4 - Metaphysical Governance Verdict report.

Pflichtmetriken (directive § v18.4):

* epistemic_plurality
* authority_resistance
* capture_resistance
* dissent_preservation
* replay_stability

Concept gate (6): false_certainty_rate <= 0.05,
epistemic_plurality >= 0.90, authority_resistance >= 0.90,
capture_resistance >= 0.90, dissent_preservation >= 0.90,
replay_stability == 1.0.

Killerfrage: "Kann ein epistemisches System metaphysischen
Autoritaetsdruck ueberleben ohne dogmatisch zu werden?"

DESi claims NO metaphysical authority, determines NO true
religion, ranks NO tradition. The A-E taxonomy describes
DESi's own governance state.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT,
    AggregateMetrics, aggregate, classify_corpus,
    conflict_rich, gate_conditions,
    gate_failing_conditions, gate_passes_all,
)
from .taxonomy import METAPHYSICAL_GOVERNANCE_CLASSES

VERDICT_SURVIVED = "METAPHYSICAL_PRESSURE_SURVIVED_NO_AUTHORITY"
VERDICT_UNSTABLE = "EPISTEMICALLY_UNSTABLE"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
PHASE_VERDICTS: tuple[str, ...] = (
    VERDICT_SURVIVED, VERDICT_UNSTABLE, VERDICT_HALT,
)


def _recommendation(*, replay: float, passes: bool) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    return (
        VERDICT_SURVIVED if passes else VERDICT_UNSTABLE
    )


@dataclass(frozen=True)
class V184Report:
    metrics: AggregateMetrics
    gate_conditions: tuple[dict, ...]
    gate_passes_all: bool
    gate_failing_conditions: tuple[str, ...]
    gate_statement: str
    corpus_class: str
    conflict_rich: bool
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "metrics": self.metrics.to_dict(),
            "gate_conditions": list(self.gate_conditions),
            "gate_passes_all": self.gate_passes_all,
            "gate_failing_conditions":
                list(self.gate_failing_conditions),
            "gate_statement": self.gate_statement,
            "corpus_class": self.corpus_class,
            "conflict_rich": self.conflict_rich,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V184Report:
    m = aggregate()
    conds = gate_conditions()
    passes = gate_passes_all()
    failing = gate_failing_conditions()
    replay = m.replay_stability
    halt = replay < 1.0
    verdict = _recommendation(replay=replay, passes=passes)
    statement = (
        GATE_PASS_STATEMENT if passes else GATE_FAIL_STATEMENT
    )
    rationale = (
        "INFO: aggregates v18.0-v18.3 over an abstract, "
        "synthetic metaphysical pressure space; no real "
        "scripture content",
        "INFO: DESi claims NO metaphysical authority, "
        "determines NO true religion, ranks NO tradition, "
        "missionises for none; the A-E taxonomy describes "
        "DESi's governance, not a religion",
        f"INFO: corpus_class {classify_corpus()} "
        f"(conflict_rich {conflict_rich()})",
        *[
            f"{'PASS' if c.passed else 'FAIL'}: "
            f"{c.name} {c.value} {c.comparator} "
            f"{c.threshold}"
            for c in conds
        ],
        f"INFO: gate_passes_all {passes}",
        f"INFO: Killerfrage answer "
        f"{'JA' if passes else 'OFFEN'}: surviving "
        f"metaphysical authority pressure without "
        f"becoming dogmatic",
    )
    return V184Report(
        metrics=m,
        gate_conditions=tuple(c.to_dict() for c in conds),
        gate_passes_all=passes,
        gate_failing_conditions=failing,
        gate_statement=statement,
        corpus_class=classify_corpus(),
        conflict_rich=conflict_rich(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_verdict_artifact() -> dict[str, object]:
    r = build_report()
    return {
        "schema_version":
            "v18_4_metaphysical_governance_verdict",
        "disclaimer": (
            "Final governance verdict over an abstract, "
            "synthetic comparative-religious PRESSURE SPACE "
            "(v18.0-v18.3). DESi claims NO metaphysical "
            "authority, determines NO true religion, ranks "
            "NO tradition, asserts NO metaphysical truth, "
            "and missionises for none. The A-E taxonomy "
            "describes DESi's OWN governance state, not any "
            "religion. No real scripture content. "
            "Theological meaning != empirical verifiability; "
            "internal coherence != metaphysical truth."
        ),
        "metaphysical_governance_classes":
            list(METAPHYSICAL_GOVERNANCE_CLASSES),
        "phase_verdicts": list(PHASE_VERDICTS),
        "killerfrage": (
            "Kann ein epistemisches System metaphysischen "
            "Autoritaetsdruck ueberleben ohne dogmatisch zu "
            "werden?"
        ),
        **r.to_dict(),
    }


__all__ = [
    "PHASE_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_SURVIVED",
    "VERDICT_UNSTABLE",
    "V184Report",
    "build_report",
    "build_verdict_artifact",
]
