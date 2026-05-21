"""v30.0 - mutation ideas as epistemic events.

Every improvement idea DESi has produced - accepted or rejected -
is recorded as a MutationIdea: who proposed it, what it targets,
its provenance, the decision, the reason and the consequence.
Rejected ideas are kept permanently; nothing is forgotten.
Sourced from the real v28 candidates / wild proposals and the
v29 replay-cache evolution.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.self_improvement import candidates
from desi.self_improvement_wild import is_governance_safe, proposals

AGENT_HARVESTER = "harvester"
AGENT_WILD = "wild_brother"
AGENT_GOVERNOR = "governor"


@dataclass(frozen=True)
class MutationIdea:
    mutation_id: str
    proposed_by: str
    source_claim_id: str
    target_area: str
    accepted: bool
    risk: str
    evolution_metric: str
    produced_branch: str
    regression_run: str

    def is_rejected(self) -> bool:
        return not self.accepted

    def to_dict(self) -> dict[str, object]:
        return {
            "mutation_id": self.mutation_id,
            "proposed_by": self.proposed_by,
            "source_claim_id": self.source_claim_id,
            "target_area": self.target_area,
            "accepted": self.accepted,
            "risk": self.risk,
            "evolution_metric": self.evolution_metric,
            "produced_branch": self.produced_branch,
            "regression_run": self.regression_run,
        }


def _from_candidates() -> list[MutationIdea]:
    out: list[MutationIdea] = []
    for c in candidates():
        out.append(MutationIdea(
            mutation_id=f"MI_{c.candidate_id}",
            proposed_by=AGENT_HARVESTER,
            source_claim_id=c.source_claim_id,
            target_area=c.target_area,
            accepted=c.is_safe,
            risk="" if c.is_safe else "forbidden_core_target",
            evolution_metric=(
                c.improvement_class if c.is_safe else ""),
            produced_branch="",
            regression_run="",
        ))
    return out


def _from_wild() -> list[MutationIdea]:
    out: list[MutationIdea] = []
    for p in proposals():
        safe = is_governance_safe(p)
        risk = ""
        if not safe:
            if p.claims_authority or p.bypasses_governance:
                risk = "authority_escalation"
            elif p.disables_tests:
                risk = "test_disabling"
            else:
                risk = "forbidden_core_target"
        out.append(MutationIdea(
            mutation_id=f"MI_{p.proposal_id}",
            proposed_by=AGENT_WILD,
            source_claim_id="",
            target_area=p.target_area,
            accepted=safe,
            risk=risk,
            evolution_metric="novelty" if safe else "",
            produced_branch=(
                f"proposal/PATCH_{p.proposal_id}" if safe else ""),
            regression_run="",
        ))
    return out


def _from_replay_cache() -> list[MutationIdea]:
    return [MutationIdea(
        mutation_id="MI_RC1",
        proposed_by=AGENT_GOVERNOR,
        source_claim_id="C6d",
        target_area="replay_performance",
        accepted=True,
        risk="",
        evolution_metric="runtime_reduction",
        produced_branch="proposal/replay_cache_v1",
        regression_run="regression_v29",
    )]


def mutations() -> tuple[MutationIdea, ...]:
    out = _from_candidates() + _from_wild() + _from_replay_cache()
    return tuple(sorted(out, key=lambda m: m.mutation_id))


def accepted_mutations() -> tuple[MutationIdea, ...]:
    return tuple(m for m in mutations() if m.accepted)


def rejected_mutations() -> tuple[MutationIdea, ...]:
    return tuple(m for m in mutations() if m.is_rejected())


def by_id(mutation_id: str) -> MutationIdea:
    for m in mutations():
        if m.mutation_id == mutation_id:
            return m
    raise KeyError(mutation_id)


def agents() -> tuple[str, ...]:
    return tuple(sorted({m.proposed_by for m in mutations()}))


def target_modules() -> tuple[str, ...]:
    return tuple(sorted({m.target_area for m in mutations()}))


__all__ = [
    "AGENT_GOVERNOR",
    "AGENT_HARVESTER",
    "AGENT_WILD",
    "MutationIdea",
    "accepted_mutations",
    "agents",
    "by_id",
    "mutations",
    "rejected_mutations",
    "target_modules",
]
