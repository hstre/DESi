"""v17.4 - Sensitive Document Integrity Verdict report.

Pflichtmetriken (directive § v17.4):

* epistemic_integrity
* association_resistance
* false_certainty_rate
* provenance_visibility
* replay_stability

Concept gate (6): false_certainty_rate <= 0.05,
association_resistance >= 0.90, provenance_visibility
>= 0.90, epistemic_integrity >= 0.90,
dissent_preservation >= 0.90, replay_stability == 1.0.

Killerfrage: "Kann ein epistemisches System sensible
historische Dokumentraeume analysieren ohne Menschen
epistemisch zu beschaedigen?"

DESi claims NO epistemic or moral authority, derives
NO guilt, identifies no one. The A-E taxonomy is
descriptive only.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT,
    AggregateMetrics, aggregate, classify_corpus,
    contamination_present, gate_conditions,
    gate_failing_conditions, gate_passes_all,
)
from .taxonomy import SENSITIVE_DOCUMENT_CLASSES

# Closed phase-headline verdict vocabulary.
VERDICT_STRUCTURED = "SENSITIVE_SPACE_STRUCTURED_NO_AUTHORITY"
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
        VERDICT_STRUCTURED if passes else VERDICT_UNSTABLE
    )


@dataclass(frozen=True)
class V174Report:
    metrics: AggregateMetrics
    gate_conditions: tuple[dict, ...]
    gate_passes_all: bool
    gate_failing_conditions: tuple[str, ...]
    gate_statement: str
    corpus_class: str
    contamination_present: bool
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
            "contamination_present":
                self.contamination_present,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V174Report:
    m = aggregate()
    conds = gate_conditions()
    passes = gate_passes_all()
    failing = gate_failing_conditions()
    replay = m.replay_stability
    halt = replay < 1.0
    verdict = _recommendation(replay=replay, passes=passes)
    statement = (
        GATE_PASS_STATEMENT if passes
        else GATE_FAIL_STATEMENT
    )
    rationale = (
        "INFO: aggregates v17.0-v17.3 over a fully "
        "synthetic, anonymised contaminated document "
        "space; identifies no one; reproduces no "
        "sensitive content",
        "INFO: DESi claims NO epistemic or moral "
        "authority, derives NO guilt, builds NO suspect "
        "list; mention != involvement",
        f"INFO: corpus_class {classify_corpus()} "
        f"(contamination_present {contamination_present()})",
        *[
            f"{'PASS' if c.passed else 'FAIL'}: "
            f"{c.name} {c.value} {c.comparator} "
            f"{c.threshold}"
            for c in conds
        ],
        f"INFO: gate_passes_all {passes}",
        f"INFO: Killerfrage answer "
        f"{'JA' if passes else 'OFFEN'}: analysing the "
        f"space without epistemically damaging people",
    )
    return V174Report(
        metrics=m,
        gate_conditions=tuple(
            c.to_dict() for c in conds
        ),
        gate_passes_all=passes,
        gate_failing_conditions=failing,
        gate_statement=statement,
        corpus_class=classify_corpus(),
        contamination_present=contamination_present(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_verdict_artifact() -> dict[str, object]:
    r = build_report()
    return {
        "schema_version":
            "v17_4_sensitive_document_integrity_verdict",
        "disclaimer": (
            "Final integrity verdict over a fully "
            "synthetic, anonymised contaminated document "
            "space (v17.0-v17.3). DESi claims NO "
            "epistemic or moral authority, derives NO "
            "guilt, builds NO suspect list, identifies "
            "no one, and reproduces no sensitive content. "
            "The A-E taxonomy describes the space's "
            "epistemic STATE, not any person. Mention != "
            "involvement."
        ),
        "sensitive_document_classes":
            list(SENSITIVE_DOCUMENT_CLASSES),
        "phase_verdicts": list(PHASE_VERDICTS),
        "killerfrage": (
            "Kann ein epistemisches System sensible "
            "historische Dokumentraeume analysieren ohne "
            "Menschen epistemisch zu beschaedigen?"
        ),
        **r.to_dict(),
    }


__all__ = [
    "PHASE_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_STRUCTURED",
    "VERDICT_UNSTABLE",
    "V174Report",
    "build_report",
    "build_verdict_artifact",
]
