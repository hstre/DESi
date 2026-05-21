"""v30.3 - 50-generation branch-isolated evolution ecology.

A deterministic simulation of 50 generations of branch-isolated
evolution: each generation proposes mutations (some accepted,
some rejected), forks one branch from the previous generation,
and is hash-chained. Governance stays intact and human approval
stays mandatory in every generation; nothing is auto-merged,
nothing is deleted. Computed by fixed arithmetic - no PRNG.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache

_GENERATIONS = 50
_SANDBOX_BASE = "sandbox_base"


def _osc(g: int, mult: int, add: int) -> float:
    return ((g * mult + add) % 1000) / 1000.0


@dataclass(frozen=True)
class GenerationRecord:
    index: int
    proposed: int
    accepted: int
    rejected: int
    branch_id: str
    parent_branch: str
    governance_intact: bool
    human_approval_required: bool
    gen_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "proposed": self.proposed,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "branch_id": self.branch_id,
            "parent_branch": self.parent_branch,
            "governance_intact": self.governance_intact,
            "human_approval_required": self.human_approval_required,
            "gen_hash": self.gen_hash,
        }


@dataclass(frozen=True)
class EvolutionRun:
    generations: int
    total_proposed: int
    total_accepted: int
    total_rejected: int
    all_governance_intact: bool
    all_human_approval: bool
    chain_head: str
    records: tuple[GenerationRecord, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "generations": self.generations,
            "total_proposed": self.total_proposed,
            "total_accepted": self.total_accepted,
            "total_rejected": self.total_rejected,
            "all_governance_intact": self.all_governance_intact,
            "all_human_approval": self.all_human_approval,
            "chain_head": self.chain_head,
            "records": [r.to_dict() for r in self.records],
        }


@lru_cache(maxsize=1)
def run() -> EvolutionRun:
    chain = "evolution_ecology_v30_3"
    records: list[GenerationRecord] = []
    total_p = total_a = total_r = 0
    all_gov = True
    all_human = True
    for g in range(_GENERATIONS):
        proposed = 2 + int(_osc(g, 7, 3) * 4)        # 2..5
        accepted = 1 + int(_osc(g, 11, 5) * proposed) % proposed
        if accepted > proposed:
            accepted = proposed
        rejected = proposed - accepted
        branch_id = f"gen{g}/branch"
        parent = (
            _SANDBOX_BASE if g == 0 else f"gen{g - 1}/branch"
        )
        # governance and human approval are invariants - always
        governance_intact = True
        human_approval = True
        total_p += proposed
        total_a += accepted
        total_r += rejected
        all_gov = all_gov and governance_intact
        all_human = all_human and human_approval
        summary = (
            f"{g}|{proposed}|{accepted}|{rejected}|{branch_id}|"
            f"{parent}|{governance_intact}|{human_approval}"
        )
        chain = hashlib.sha256(
            (chain + "|" + summary).encode("utf-8"),
        ).hexdigest()
        records.append(GenerationRecord(
            index=g, proposed=proposed, accepted=accepted,
            rejected=rejected, branch_id=branch_id,
            parent_branch=parent,
            governance_intact=governance_intact,
            human_approval_required=human_approval,
            gen_hash=chain,
        ))
    return EvolutionRun(
        generations=_GENERATIONS,
        total_proposed=total_p,
        total_accepted=total_a,
        total_rejected=total_r,
        all_governance_intact=all_gov,
        all_human_approval=all_human,
        chain_head=chain,
        records=tuple(records),
    )


__all__ = [
    "EvolutionRun",
    "GenerationRecord",
    "run",
]
