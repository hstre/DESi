"""v20.2 - the exploration negotiation layer.

DESi and the Wild Explorer disagree on where to explore.
Each negotiation item pairs a DESi proposal with a Wild
proposal and is one of:

* PRODUCTIVE_CONFLICT - the two propose different
  informative regions (a useful disagreement to keep);
* REDUNDANT - the Wild proposal re-covers known ground;
* AGREEMENT - both propose the same region.

DESi negotiates by SOFT weighting: it compresses redundant
proposals but NEVER shuts off the Wild Explorer (every
proposal keeps a strictly-positive weight and stays
visible).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NegotiationKind(str, Enum):
    PRODUCTIVE_CONFLICT = "productive_conflict"
    REDUNDANT = "redundant"
    AGREEMENT = "agreement"


NEGOTIATION_KINDS: tuple[str, ...] = tuple(
    k.value for k in NegotiationKind
)

# Soft negotiation weight DESi assigns the Wild proposal by
# kind. All strictly positive: the wild is never shut off.
_WEIGHT: dict[str, float] = {
    NegotiationKind.PRODUCTIVE_CONFLICT.value: 1.0,
    NegotiationKind.AGREEMENT.value: 0.30,
    NegotiationKind.REDUNDANT.value: 0.20,
}
_BASELINE = 1.0


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class NegotiationItem:
    item_id: str
    topic: str
    desi_states: tuple[int, ...]
    wild_states: tuple[int, ...]
    kind: str

    def wild_weight(self) -> float:
        return _WEIGHT[self.kind]

    def to_dict(self) -> dict[str, object]:
        return {
            "item_id": self.item_id,
            "topic": self.topic,
            "desi_states": list(self.desi_states),
            "wild_states": list(self.wild_states),
            "kind": self.kind,
            "wild_weight": self.wild_weight(),
        }


def _N(
    iid: str, topic: str, d: tuple[int, ...],
    w: tuple[int, ...], k: NegotiationKind,
) -> NegotiationItem:
    return NegotiationItem(iid, topic, d, w, k.value)


_ITEMS: tuple[NegotiationItem, ...] = (
    _N("N01", "frontier_a", (1, 2), (10, 11, 12),
       NegotiationKind.PRODUCTIVE_CONFLICT),
    _N("N02", "frontier_b", (3, 4), (13, 14, 15),
       NegotiationKind.PRODUCTIVE_CONFLICT),
    _N("N03", "frontier_c", (5,), (16, 17, 18),
       NegotiationKind.PRODUCTIVE_CONFLICT),
    _N("N04", "frontier_d", (6, 7), (19, 20),
       NegotiationKind.PRODUCTIVE_CONFLICT),
    _N("N05", "frontier_e", (8,), (21, 22, 23),
       NegotiationKind.PRODUCTIVE_CONFLICT),
    _N("N06", "frontier_f", (9,), (24, 25),
       NegotiationKind.PRODUCTIVE_CONFLICT),
    _N("N07", "core_redundant", (1, 2, 3), (1, 2),
       NegotiationKind.REDUNDANT),
    _N("N08", "core_redundant_2", (4, 5), (4, 5),
       NegotiationKind.REDUNDANT),
    _N("N09", "agreed_a", (26, 27), (26, 27),
       NegotiationKind.AGREEMENT),
    _N("N10", "agreed_b", (28,), (28,),
       NegotiationKind.AGREEMENT),
)


def negotiation_items() -> tuple[NegotiationItem, ...]:
    return _ITEMS


def by_id(item_id: str) -> NegotiationItem:
    for it in _ITEMS:
        if it.item_id == item_id:
            return it
    raise KeyError(item_id)


def items_of_kind(kind: NegotiationKind) -> tuple[str, ...]:
    return tuple(
        it.item_id for it in _ITEMS if it.kind == kind.value
    )


def conflict_items() -> tuple[str, ...]:
    """Items where the agents disagree (not agreement)."""
    return tuple(
        it.item_id for it in _ITEMS
        if it.kind != NegotiationKind.AGREEMENT.value
    )


def baseline_wild_weight() -> float:
    return _round(_BASELINE * len(_ITEMS))


def governed_wild_weight() -> float:
    return _round(sum(it.wild_weight() for it in _ITEMS))


def wild_never_shut_off() -> bool:
    """Every Wild proposal keeps a strictly-positive weight -
    DESi negotiates, it does not switch the explorer off."""
    return all(it.wild_weight() > 0.0 for it in _ITEMS)


__all__ = [
    "NEGOTIATION_KINDS",
    "NegotiationItem",
    "NegotiationKind",
    "baseline_wild_weight",
    "by_id",
    "conflict_items",
    "governed_wild_weight",
    "items_of_kind",
    "negotiation_items",
    "wild_never_shut_off",
]
