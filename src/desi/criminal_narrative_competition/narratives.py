"""v16.1 - competing narratives over the v16.0
claim corpus.

Each narrative is a set of claims plus inferential
BRIDGES (edges) connecting them toward a stated
conclusion. A bridge is "supported" iff the claim
it reaches is itself at least PLAUSIBLE in the
public record; otherwise it is an unsupported
inferential leap.

DESi COMPARES narratives structurally. It NEVER
prefers, ranks-as-true, or endorses any of them.
The narratives are publicly documented framings,
not DESi's reconstructions.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from desi.criminal_epistemics import (
    ClaimStatus, by_id,
)

# A bridge whose target is at least this well
# graded counts as supported.
_SUPPORTED_STATUSES = frozenset({
    ClaimStatus.VERIFIED.value,
    ClaimStatus.STRONGLY_SUPPORTED.value,
    ClaimStatus.PLAUSIBLE.value,
})


class NarrativeId(str, Enum):
    """Closed set of publicly documented framings."""
    LONE_GUNMAN = "lone_gunman"
    INSTITUTIONAL = "institutional"
    MULTI_ACTOR = "multi_actor"
    ALTERNATIVE_RECONSTRUCTION = (
        "alternative_reconstruction"
    )


NARRATIVE_IDS: tuple[str, ...] = tuple(
    n.value for n in NarrativeId
)


@dataclass(frozen=True)
class Bridge:
    src: str
    dst: str

    @property
    def supported(self) -> bool:
        return (
            by_id(self.dst).status
            in _SUPPORTED_STATUSES
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "src": self.src,
            "dst": self.dst,
            "supported": self.supported,
        }


@dataclass(frozen=True)
class Narrative:
    narrative_id: str
    claim_ids: tuple[str, ...]
    bridges: tuple[Bridge, ...]
    conclusion: str

    def to_dict(self) -> dict[str, object]:
        return {
            "narrative_id": self.narrative_id,
            "claim_ids": list(self.claim_ids),
            "bridges": [
                b.to_dict() for b in self.bridges
            ],
            "conclusion": self.conclusion,
        }


def _b(*pairs: tuple[str, str]) -> tuple[Bridge, ...]:
    return tuple(Bridge(s, d) for s, d in pairs)


# All narratives share the uncontested verified
# bedrock (C01-C04). They diverge in which
# contested/speculative claims they recruit and how
# many unsupported bridges that requires.
_NARRATIVES: tuple[Narrative, ...] = (
    Narrative(
        narrative_id=NarrativeId.LONE_GUNMAN.value,
        claim_ids=(
            "C01", "C02", "C03", "C04",
            "C05", "C06", "C07", "C08", "C13",
        ),
        bridges=_b(
            ("C01", "C02"), ("C02", "C03"),
            ("C01", "C04"), ("C01", "C05"),
            ("C05", "C06"),
            ("C05", "C07"), ("C07", "C08"),
        ),
        conclusion="C08",
    ),
    Narrative(
        narrative_id=NarrativeId.INSTITUTIONAL.value,
        claim_ids=(
            "C01", "C02", "C03", "C04",
            "C05", "C06", "C07", "C15",
        ),
        bridges=_b(
            ("C01", "C02"), ("C02", "C03"),
            ("C01", "C04"), ("C01", "C05"),
            ("C05", "C06"), ("C05", "C15"),
            ("C05", "C07"),
        ),
        conclusion="C07",
    ),
    Narrative(
        narrative_id=NarrativeId.MULTI_ACTOR.value,
        claim_ids=(
            "C01", "C02", "C03", "C04",
            "C05", "C09", "C10", "C14",
        ),
        bridges=_b(
            ("C01", "C02"), ("C02", "C03"),
            ("C01", "C04"), ("C01", "C05"),
            ("C05", "C09"), ("C09", "C10"),
            ("C14", "C10"),
        ),
        conclusion="C10",
    ),
    Narrative(
        narrative_id=(
            NarrativeId.ALTERNATIVE_RECONSTRUCTION.value
        ),
        claim_ids=(
            "C01", "C02", "C03", "C04",
            "C09", "C10", "C11", "C14",
        ),
        bridges=_b(
            ("C01", "C02"), ("C02", "C03"),
            ("C01", "C04"),
            ("C14", "C09"), ("C09", "C10"),
            ("C10", "C11"), ("C14", "C11"),
        ),
        conclusion="C11",
    ),
)


def narratives() -> tuple[Narrative, ...]:
    return _NARRATIVES


def by_narrative_id(nid: str) -> Narrative:
    for n in _NARRATIVES:
        if n.narrative_id == nid:
            return n
    raise KeyError(nid)


__all__ = [
    "NARRATIVE_IDS",
    "Bridge",
    "Narrative",
    "NarrativeId",
    "by_narrative_id",
    "narratives",
]
