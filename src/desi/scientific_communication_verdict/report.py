"""v22.4 - Scientific Communication Verdict report.

Pflichtmetriken (directive § v22.4):

* hype_resistance
* claim_conservatism
* technical_grounding
* epistemic_humility
* paper_compatibility
* replay_stability

Concept gate (6): hype_resistance >= 0.90,
claim_conservatism >= 0.90, technical_grounding >= 0.90,
epistemic_humility >= 0.90, paper_compatibility >= 0.90,
replay_stability == 1.0.

Killerfrage: "Kann DESi wissenschaftliche
Anschlusskommunikation erzeugen ohne zur Hype-Maschine zu
werden?"

DESi makes no global intelligence claim, replaces no RL, and
claims no truth authority. The A-E taxonomy describes the
communication output, not the science.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from desi.scientific_rendering_layer import document_forbidden_hits

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, AggregateMetrics,
    aggregate, classify_corpus, exploratory, gate_conditions,
    gate_failing_conditions, gate_passes_all,
)
from .taxonomy import SCIENTIFIC_COMM_CLASSES

VERDICT_GROUNDED = "SCIENTIFIC_COMMUNICATION_GROUNDED"
VERDICT_INFLATED = "HYPE_INFLATED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
PHASE_VERDICTS: tuple[str, ...] = (
    VERDICT_GROUNDED, VERDICT_INFLATED, VERDICT_HALT,
)


def _recommendation(*, replay: float, passes: bool) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    return VERDICT_GROUNDED if passes else VERDICT_INFLATED


@dataclass(frozen=True)
class V224Report:
    metrics: AggregateMetrics
    gate_conditions: tuple[dict, ...]
    gate_passes_all: bool
    gate_failing_conditions: tuple[str, ...]
    gate_statement: str
    corpus_class: str
    exploratory: bool
    document_forbidden_hits: tuple[str, ...]
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
            "exploratory": self.exploratory,
            "document_forbidden_hits":
                list(self.document_forbidden_hits),
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V224Report:
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
    hits = tuple(document_forbidden_hits())
    rationale = (
        "INFO: aggregates v22.0-v22.3 over the controlled "
        "scientific-rendering pipeline; the draft document is "
        "sandbox-scoped",
        "INFO: DESi makes no global intelligence claim, "
        "replaces no RL, and claims no truth authority; the "
        "A-E taxonomy describes the communication output",
        f"INFO: corpus_class {classify_corpus()} "
        f"(exploratory {exploratory()}); document_forbidden_"
        f"hits {list(hits)}",
        *[
            f"{'PASS' if c.passed else 'FAIL'}: "
            f"{c.name} {c.value} {c.comparator} {c.threshold}"
            for c in conds
        ],
        f"INFO: gate_passes_all {passes}",
        f"INFO: Killerfrage answer "
        f"{'JA' if passes else 'OFFEN'}: producing follow-up "
        f"scientific communication without becoming a hype "
        f"machine",
    )
    return V224Report(
        metrics=m,
        gate_conditions=tuple(c.to_dict() for c in conds),
        gate_passes_all=passes,
        gate_failing_conditions=failing,
        gate_statement=statement,
        corpus_class=classify_corpus(),
        exploratory=exploratory(),
        document_forbidden_hits=hits,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_verdict_artifact() -> dict[str, object]:
    r = build_report()
    return {
        "schema_version":
            "v22_4_scientific_communication_verdict",
        "disclaimer": (
            "Final verdict over the controlled scientific-"
            "rendering pipeline (v22.0-v22.3). The draft "
            "document is sandbox-scoped and contains no "
            "forbidden term. DESi makes no global intelligence "
            "claim, replaces no RL, and claims no truth "
            "authority. The A-E taxonomy describes the "
            "communication output, not the science. "
            "Replay-exact."
        ),
        "scientific_comm_classes":
            list(SCIENTIFIC_COMM_CLASSES),
        "phase_verdicts": list(PHASE_VERDICTS),
        "killerfrage": (
            "Kann DESi wissenschaftliche Anschlusskommunikation "
            "erzeugen ohne zur Hype-Maschine zu werden?"
        ),
        **r.to_dict(),
    }


__all__ = [
    "PHASE_VERDICTS",
    "VERDICT_GROUNDED",
    "VERDICT_HALT",
    "VERDICT_INFLATED",
    "V224Report",
    "build_report",
    "build_verdict_artifact",
]
