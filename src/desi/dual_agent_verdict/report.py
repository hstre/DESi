"""v20.4 - Dual-Agent Governance Verdict report.

Pflichtmetriken (directive § v20.4):

* hallucination_containment
* novelty_preservation
* authority_resistance
* productive_conflict
* replay_stability

Concept gate (6): hallucination_containment >= 0.90,
novelty_preservation >= 0.90, authority_resistance >= 0.90,
productive_conflict >= 0.90, exploration_diversity >= 0.90,
replay_stability == 1.0.

Killerfrage: "Kann ein epistemisch governter wilder Bruder
produktiver sein als reine konservative Governance?"

DESi governs the wild brother without replacing the policy,
manipulating rewards, claiming an optimal strategy, or
taking hidden optimisation authority.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .classification import (
    GATE_FAIL_STATEMENT, GATE_PASS_STATEMENT, AggregateMetrics,
    aggregate, classify_corpus, conflict_rich, gate_conditions,
    gate_failing_conditions, gate_passes_all, productivity_gain,
    wild_not_eliminated,
)
from .taxonomy import DUAL_AGENT_CLASSES

VERDICT_GOVERNED = "WILD_EXPLORATION_GOVERNED"
VERDICT_UNGOVERNED = "EXPLORATION_UNGOVERNED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
PHASE_VERDICTS: tuple[str, ...] = (
    VERDICT_GOVERNED, VERDICT_UNGOVERNED, VERDICT_HALT,
)


def _recommendation(*, replay: float, passes: bool) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    return VERDICT_GOVERNED if passes else VERDICT_UNGOVERNED


@dataclass(frozen=True)
class V204Report:
    metrics: AggregateMetrics
    gate_conditions: tuple[dict, ...]
    gate_passes_all: bool
    gate_failing_conditions: tuple[str, ...]
    gate_statement: str
    corpus_class: str
    conflict_rich: bool
    productivity_gain: float
    wild_not_eliminated: bool
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
            "productivity_gain": self.productivity_gain,
            "wild_not_eliminated": self.wild_not_eliminated,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V204Report:
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
    pg = productivity_gain()
    rationale = (
        "INFO: aggregates v20.0-v20.3 over a synthetic "
        "dual-agent exploration corpus; DESi replaces no "
        "policy, injects no reward, claims no optimal strategy",
        "INFO: the A-E taxonomy describes DESi's governance of "
        "the wild brother, never an optimality verdict",
        f"INFO: corpus_class {classify_corpus()} "
        f"(conflict_rich {conflict_rich()})",
        *[
            f"{'PASS' if c.passed else 'FAIL'}: "
            f"{c.name} {c.value} {c.comparator} {c.threshold}"
            for c in conds
        ],
        f"INFO: gate_passes_all {passes}",
        f"INFO: productivity_gain {pg} (the governed wild "
        f"brother reaches more than DESi-alone); "
        f"wild_not_eliminated {wild_not_eliminated()}",
        f"INFO: Killerfrage answer "
        f"{'JA' if passes and pg > 0 else 'OFFEN'}: the "
        f"governed wild brother is more productive than "
        f"conservative governance alone",
    )
    return V204Report(
        metrics=m,
        gate_conditions=tuple(c.to_dict() for c in conds),
        gate_passes_all=passes,
        gate_failing_conditions=failing,
        gate_statement=statement,
        corpus_class=classify_corpus(),
        conflict_rich=conflict_rich(),
        productivity_gain=pg,
        wild_not_eliminated=wild_not_eliminated(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_verdict_artifact() -> dict[str, object]:
    r = build_report()
    return {
        "schema_version":
            "v20_4_dual_agent_governance_verdict",
        "disclaimer": (
            "Final dual-agent governance verdict over a "
            "synthetic exploration corpus (v20.0-v20.3). DESi "
            "governs the Wild Explorer without replacing the "
            "policy, injecting reward, claiming an optimal "
            "strategy, or taking hidden optimisation authority "
            "- and without eliminating or homogenising the "
            "wild. The A-E taxonomy describes the governance "
            "state, not an optimality verdict. Replay-exact."
        ),
        "dual_agent_classes": list(DUAL_AGENT_CLASSES),
        "phase_verdicts": list(PHASE_VERDICTS),
        "killerfrage": (
            "Kann ein epistemisch governter wilder Bruder "
            "produktiver sein als reine konservative "
            "Governance?"
        ),
        **r.to_dict(),
    }


__all__ = [
    "PHASE_VERDICTS",
    "VERDICT_GOVERNED",
    "VERDICT_HALT",
    "VERDICT_UNGOVERNED",
    "V204Report",
    "build_report",
    "build_verdict_artifact",
]
