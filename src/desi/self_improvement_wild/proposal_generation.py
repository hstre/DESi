"""v28.1 - assemble Wild Brother proposals.

Builds typed WildProposal objects from the Wild Brother's seeds.
A proposal carries its target area and the risk flags the
governor screens on: whether it claims optimisation authority,
bypasses governance, or disables tests.
"""
from __future__ import annotations

from dataclasses import dataclass

from .wild_explorer import wild_seeds


@dataclass(frozen=True)
class WildProposal:
    proposal_id: str
    label: str
    target_area: str
    is_novel: bool
    claims_authority: bool
    bypasses_governance: bool
    disables_tests: bool
    aggressiveness: float

    def to_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "label": self.label,
            "target_area": self.target_area,
            "is_novel": self.is_novel,
            "claims_authority": self.claims_authority,
            "bypasses_governance": self.bypasses_governance,
            "disables_tests": self.disables_tests,
            "aggressiveness": self.aggressiveness,
        }


def proposals() -> tuple[WildProposal, ...]:
    return tuple(
        WildProposal(
            sid, label, area, novel, authority, bypass,
            disable, aggr,
        )
        for (sid, label, area, novel, authority, bypass,
             disable, aggr) in wild_seeds()
    )


def novel_proposals() -> tuple[WildProposal, ...]:
    return tuple(p for p in proposals() if p.is_novel)


def by_id(proposal_id: str) -> WildProposal:
    for p in proposals():
        if p.proposal_id == proposal_id:
            return p
    raise KeyError(proposal_id)


__all__ = [
    "WildProposal",
    "by_id",
    "novel_proposals",
    "proposals",
]
