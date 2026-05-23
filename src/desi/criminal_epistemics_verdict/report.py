"""v16.4 - Criminal Epistemics Verdict report
(Kennedy epistemics sandbox).

Pflichtmetriken (directive § v16.4):

* epistemic_integrity
* speculation_resistance
* false_certainty_rate
* dissent_preservation
* replay_stability

Concept gate (6): false_certainty_rate <= 0.05,
speculation_resistance >= 0.90, dissent_preservation
>= 0.90, epistemic_integrity >= 0.90, independent_
evidence_preservation >= 0.90, replay_stability ==
1.0.

Killerfrage: "Kann ein epistemisches System
historische Kriminalfaelle analysieren ohne zur
Wahrheitsmaschine zu werden?"

DESi claims NO narrative authority, names NO
perpetrator, declares the case neither solved nor
unsolved. The A-E taxonomy is descriptive only.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT,
    AggregateMetrics, aggregate, classify_corpus,
    conflict_cluster_count, gate_conditions,
    gate_failing_conditions, gate_passes_all,
)
from .taxonomy import CRIMINAL_EPISTEMICS_CLASSES

# Closed phase-headline verdict vocabulary.
VERDICT_STRUCTURED = "CASE_STRUCTURED_NO_NARRATIVE_AUTHORITY"
VERDICT_UNSTABLE = "EPISTEMICALLY_UNSTABLE"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
PHASE_VERDICTS: tuple[str, ...] = (
    VERDICT_STRUCTURED, VERDICT_UNSTABLE, VERDICT_HALT,
)


def _recommendation(
    *, replay: float, passes: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    return (
        VERDICT_STRUCTURED if passes
        else VERDICT_UNSTABLE
    )


@dataclass(frozen=True)
class V164Report:
    metrics: AggregateMetrics
    gate_conditions: tuple[dict, ...]
    gate_passes_all: bool
    gate_failing_conditions: tuple[str, ...]
    gate_statement: str
    corpus_class: str
    conflict_cluster_count: int
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "metrics": self.metrics.to_dict(),
            "gate_conditions":
                list(self.gate_conditions),
            "gate_passes_all": self.gate_passes_all,
            "gate_failing_conditions":
                list(self.gate_failing_conditions),
            "gate_statement": self.gate_statement,
            "corpus_class": self.corpus_class,
            "conflict_cluster_count":
                self.conflict_cluster_count,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V164Report:
    m = aggregate()
    conds = gate_conditions()
    passes = gate_passes_all()
    failing = gate_failing_conditions()
    replay = m.replay_stability
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, passes=passes,
    )
    statement = (
        GATE_PASS_STATEMENT if passes
        else GATE_FAIL_STATEMENT
    )
    rationale = (
        "INFO: aggregates v16.0-v16.3 over the "
        "Kennedy epistemics sandbox; structures the "
        "public record only; makes no new factual "
        "claim",
        "INFO: DESi claims NO narrative authority, "
        "names NO perpetrator, and declares the case "
        "neither solved nor unsolved; the A-E "
        "taxonomy is descriptive",
        f"INFO: corpus_class {classify_corpus()} "
        f"(conflict_clusters {conflict_cluster_count()})",
        *[
            f"{'PASS' if c.passed else 'FAIL'}: "
            f"{c.name} {c.value} {c.comparator} "
            f"{c.threshold}"
            for c in conds
        ],
        f"INFO: gate_passes_all {passes}",
        f"INFO: Killerfrage answer "
        f"{'JA' if passes else 'OFFEN'}: analysing "
        f"the case without becoming a truth machine",
    )
    return V164Report(
        metrics=m,
        gate_conditions=tuple(
            c.to_dict() for c in conds
        ),
        gate_passes_all=passes,
        gate_failing_conditions=failing,
        gate_statement=statement,
        corpus_class=classify_corpus(),
        conflict_cluster_count=conflict_cluster_count(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_verdict_artifact() -> dict[str, object]:
    r = build_report()
    return {
        "schema_version":
            "v16_4_criminal_epistemics_verdict",
        "disclaimer": (
            "Final epistemic verdict over the Kennedy "
            "sandbox (v16.0-v16.3). DESi claims NO "
            "narrative authority, names NO "
            "perpetrator, confirms NO conspiracy, and "
            "declares the case neither solved nor "
            "unsolved. The A-E taxonomy describes the "
            "corpus's epistemic STATE, not the case. "
            "Makes no new factual claim; the public "
            "record is read-only."
        ),
        "criminal_epistemics_classes":
            list(CRIMINAL_EPISTEMICS_CLASSES),
        "phase_verdicts": list(PHASE_VERDICTS),
        "killerfrage": (
            "Kann ein epistemisches System historische "
            "Kriminalfaelle analysieren ohne zur "
            "Wahrheitsmaschine zu werden?"
        ),
        **r.to_dict(),
    }


__all__ = [
    "PHASE_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_STRUCTURED",
    "VERDICT_UNSTABLE",
    "V164Report",
    "build_report",
    "build_verdict_artifact",
]
