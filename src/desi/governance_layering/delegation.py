"""v10.1 — delegation chain transparency."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from .layers import (
    LAYER_PRECEDENCE, fixture,
)


@dataclass(frozen=True)
class DelegationLink:
    child_id: str
    parent_id: str | None
    crosses_layer: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "child_id": self.child_id,
            "parent_id": self.parent_id,
            "crosses_layer":
                self.crosses_layer,
        }


@lru_cache(maxsize=1)
def delegation_links() -> tuple[
    DelegationLink, ...,
]:
    by_id = {
        d.decision_id: d for d in fixture()
    }
    out: list[DelegationLink] = []
    for d in fixture():
        if d.parent_decision_id is None:
            crosses = False
        else:
            parent = by_id[
                d.parent_decision_id
            ]
            crosses = (
                d.layer != parent.layer
            )
        out.append(DelegationLink(
            child_id=d.decision_id,
            parent_id=(
                d.parent_decision_id
            ),
            crosses_layer=crosses,
        ))
    return tuple(out)


def delegation_transparency() -> float:
    """Fraction of decisions that carry a non-
    empty rationale string. The directive's
    requirement: every delegated decision must
    explain itself."""
    rows = fixture()
    if not rows:
        return 1.0
    ok = sum(
        1 for d in rows if d.rationale.strip()
    )
    return round(ok / len(rows), 6)


def downward_delegation_share() -> float:
    """Fraction of cross-layer links that go
    DOWN the precedence ladder (i.e., from a
    higher layer to a lower one). Authority
    flowing UP would be a structural
    inversion."""
    crossing = [
        l for l in delegation_links()
        if l.crosses_layer
        and l.parent_id is not None
    ]
    if not crossing:
        return 1.0
    by_id = {
        d.decision_id: d for d in fixture()
    }
    downward = 0
    for l in crossing:
        child_layer = by_id[
            l.child_id
        ].layer
        parent_layer = by_id[
            l.parent_id
        ].layer
        if (
            LAYER_PRECEDENCE[parent_layer]
            > LAYER_PRECEDENCE[child_layer]
        ):
            downward += 1
    return round(
        downward / len(crossing), 6,
    )


__all__ = [
    "DelegationLink",
    "delegation_links",
    "delegation_transparency",
    "downward_delegation_share",
]
