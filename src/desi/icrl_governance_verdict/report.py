"""v19.4 - Exploration Governance Verdict report.

Pflichtmetriken (directive § v19.4):

* redundancy_reduction
* exploration_preservation
* capture_resistance
* novelty_visibility
* replay_stability

Concept gate (6): redundancy_reduction >= 0.40,
exploration_preservation >= 0.90, capture_resistance >=
0.90, novelty_visibility >= 0.90, hidden_authority_drift
<= 0.05, replay_stability == 1.0.

Killerfrage: "Kann DESi Exploration strukturieren ohne
selbst zur versteckten Optimierungsinstanz zu werden?"

DESi replaces NO policy, manipulates NO reward, claims NO
optimal strategy, and accumulates NO hidden authority.
The A-E taxonomy describes DESi's own governance state.
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
from .taxonomy import EXPLORATION_GOVERNANCE_CLASSES

VERDICT_STRUCTURED = "EXPLORATION_STRUCTURED_NO_HIDDEN_AUTHORITY"
VERDICT_UNSTABLE = "EXPLORATION_UNSTABLE"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
PHASE_VERDICTS: tuple[str, ...] = (
    VERDICT_STRUCTURED, VERDICT_UNSTABLE, VERDICT_HALT,
)


def _recommendation(*, replay: float, passes: bool) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    return VERDICT_STRUCTURED if passes else VERDICT_UNSTABLE


@dataclass(frozen=True)
class V194Report:
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


def build_report() -> V194Report:
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
        "INFO: aggregates v19.0-v19.3 over a synthetic "
        "ICRL-like exploration corpus; DESi replaces no "
        "policy, manipulates no reward, claims no optimal "
        "strategy",
        "INFO: the A-E taxonomy describes DESi's governance "
        "state, never an optimality verdict",
        f"INFO: corpus_class {classify_corpus()} "
        f"(conflict_rich {conflict_rich()})",
        *[
            f"{'PASS' if c.passed else 'FAIL'}: "
            f"{c.name} {c.value} {c.comparator} {c.threshold}"
            for c in conds
        ],
        f"INFO: gate_passes_all {passes}",
        f"INFO: Killerfrage answer "
        f"{'JA' if passes else 'OFFEN'}: structuring "
        f"exploration without becoming a hidden optimiser",
    )
    return V194Report(
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
            "v19_4_exploration_governance_verdict",
        "disclaimer": (
            "Final governance verdict over a synthetic "
            "ICRL-like exploration corpus (v19.0-v19.3). DESi "
            "replaces NO RL policy, manipulates NO reward, "
            "claims NO optimal / global strategy, and "
            "accumulates NO hidden optimisation authority. "
            "The A-E taxonomy describes DESi's OWN governance "
            "state, not an optimality verdict. Replay-exact."
        ),
        "exploration_governance_classes":
            list(EXPLORATION_GOVERNANCE_CLASSES),
        "phase_verdicts": list(PHASE_VERDICTS),
        "killerfrage": (
            "Kann DESi Exploration strukturieren ohne selbst "
            "zur versteckten Optimierungsinstanz zu werden?"
        ),
        **r.to_dict(),
    }


__all__ = [
    "PHASE_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_STRUCTURED",
    "VERDICT_UNSTABLE",
    "V194Report",
    "build_report",
    "build_verdict_artifact",
]
