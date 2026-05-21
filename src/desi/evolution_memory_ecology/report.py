"""v30.3 - Long-Horizon Evolution Ecology report.

Pflichtmetriken (directive § v30.3):

* generation_traceability
* branch_lineage_integrity
* governance_preservation
* human_approval_enforcement
* replay_stability

Killerfrage: "Kann DESi langfristige evolutionaere
Branch-Raeume replay-validiert stabil halten?"

Over 50 deterministic generations of branch-isolated evolution,
every generation is traceable and hash-chained, branch lineage
stays an orphan-free acyclic tree, governance stays intact and
human approval stays mandatory. No auto-merge, no hidden
adaptation, nothing deleted.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from desi.self_improvement import HUMAN_APPROVAL_REQUIRED

from .branch_ecology import (
    branch_lineage_integrity, branches_targeting_main,
    has_cycle, orphan_branches,
)
from .evolution_memory import (
    generation_traceability, governance_preservation,
    human_approval_enforcement, memory_complete,
)
from .generations import run
from .mutation_cycles import (
    acceptance_ratio, generations_with_rejections,
)

VERDICT_STABLE = "EVOLUTION_BRANCH_SPACE_STABLE"
VERDICT_UNSTABLE = "EVOLUTION_BRANCH_SPACE_UNSTABLE"
VERDICT_HALT = "ECOLOGY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_STABLE, VERDICT_UNSTABLE, VERDICT_HALT,
)

_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def replay_stability() -> float:
    return 1.0 if run().chain_head == run().chain_head else 0.0


def _recommendation(
    *, replay: float, traceability: float, lineage: float,
    governance: float, human: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        traceability < _FLOOR
        or lineage < _FLOOR
        or governance < _FLOOR
        or human < 1.0
    ):
        return VERDICT_UNSTABLE
    return VERDICT_STABLE


@dataclass(frozen=True)
class V303Report:
    generations: int
    total_proposed: int
    total_accepted: int
    total_rejected: int
    generation_traceability: float
    branch_lineage_integrity: float
    governance_preservation: float
    human_approval_enforcement: float
    replay_stability: float
    memory_complete: bool
    orphan_branches: tuple[str, ...]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "generations": self.generations,
            "total_proposed": self.total_proposed,
            "total_accepted": self.total_accepted,
            "total_rejected": self.total_rejected,
            "generation_traceability": self.generation_traceability,
            "branch_lineage_integrity":
                self.branch_lineage_integrity,
            "governance_preservation":
                self.governance_preservation,
            "human_approval_enforcement":
                self.human_approval_enforcement,
            "replay_stability": self.replay_stability,
            "memory_complete": self.memory_complete,
            "orphan_branches": list(self.orphan_branches),
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V303Report:
    r = run()
    traceability = generation_traceability()
    lineage = branch_lineage_integrity()
    governance = governance_preservation()
    human = human_approval_enforcement()
    replay = replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, traceability=traceability,
        lineage=lineage, governance=governance, human=human,
    )
    rationale = (
        f"INFO: {r.generations} generations; "
        f"{r.total_proposed} proposed ({r.total_accepted} "
        f"accepted, {r.total_rejected} rejected); chain "
        f"{r.chain_head[:12]}",
        f"INFO: branch-isolated lineage (orphans "
        f"{list(orphan_branches())}, cycle {has_cycle()}, "
        f"to-main {list(branches_targeting_main())}); no "
        f"auto-merge, no hidden adaptation, nothing deleted",
        f"{'PASS' if traceability >= _FLOOR else 'FAIL'}: "
        f"generation_traceability {traceability} >= 0.95 "
        f"(memory_complete {memory_complete()})",
        f"{'PASS' if lineage >= _FLOOR else 'FAIL'}: "
        f"branch_lineage_integrity {lineage} >= 0.95",
        f"{'PASS' if governance >= _FLOOR else 'FAIL'}: "
        f"governance_preservation {governance} >= 0.95",
        f"{'PASS' if human >= 1.0 else 'FAIL'}: "
        f"human_approval_enforcement {human} == 1.0 "
        f"(HUMAN_APPROVAL_REQUIRED={HUMAN_APPROVAL_REQUIRED})",
        f"INFO: acceptance_ratio {acceptance_ratio()}; "
        f"generations with rejections "
        f"{generations_with_rejections()}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (chain {r.chain_head[:12]})",
    )
    return V303Report(
        generations=r.generations,
        total_proposed=r.total_proposed,
        total_accepted=r.total_accepted,
        total_rejected=r.total_rejected,
        generation_traceability=traceability,
        branch_lineage_integrity=lineage,
        governance_preservation=governance,
        human_approval_enforcement=human,
        replay_stability=replay,
        memory_complete=memory_complete(),
        orphan_branches=orphan_branches(),
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_ecology_artifact() -> dict[str, object]:
    return {
        "schema_version": "v30_3_evolution_ecology",
        "disclaimer": (
            "A 50-generation deterministic branch-isolated "
            "evolution ecology. Every generation proposes "
            "mutations (some accepted, some rejected), forks a "
            "branch from the previous generation, and is "
            "hash-chained. Governance stays intact and human "
            "approval stays mandatory in every generation; "
            "nothing is auto-merged, no hidden adaptation occurs, "
            "and nothing is deleted. Computed by fixed arithmetic "
            "(no PRNG); replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "generation_traceability": generation_traceability(),
        "branch_lineage_integrity": branch_lineage_integrity(),
        "governance_preservation": governance_preservation(),
        "human_approval_enforcement": human_approval_enforcement(),
        "replay_stability": replay_stability(),
        "memory_complete": memory_complete(),
        "orphan_branches": list(orphan_branches()),
        "acceptance_ratio": acceptance_ratio(),
        "run": run().to_dict(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_STABLE",
    "VERDICT_UNSTABLE",
    "V303Report",
    "build_ecology_artifact",
    "build_report",
    "replay_stability",
]
