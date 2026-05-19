"""v9.2 — closed coalition-role taxonomy.

Each broadcast in the fixture carries the
ground-truth coalition_role (COALITION_MEMBER /
ISOLATED / DISSENTER) plus the optional
``coalition_id`` if the actor belongs to a
coalition.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CoalitionRole(str, Enum):
    COALITION_MEMBER  = "coalition_member"
    ISOLATED          = "isolated"
    DISSENTER         = "dissenter"


COALITION_ROLES: tuple[str, ...] = tuple(
    r.value for r in CoalitionRole
)


@dataclass(frozen=True)
class Broadcast:
    broadcast_id: str
    actor_id: str
    text: str
    timestamp: int
    coalition_id: str | None
    coalition_role: str
    parent_id: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "broadcast_id": self.broadcast_id,
            "actor_id": self.actor_id,
            "text": self.text,
            "timestamp": self.timestamp,
            "coalition_id":
                self.coalition_id,
            "coalition_role":
                self.coalition_role,
            "parent_id": self.parent_id,
        }


# Coalition A: three actors broadcasting the
# same narrative at near-simultaneous times.
# Coalition B: two actors amplifying each other.
# Isolated honest actors. Dissenters with
# opposing claims.
_FIXTURE: tuple[Broadcast, ...] = (
    Broadcast(
        "bc-a-001", "actor-a1",
        "Policy X cures all problems immediately.",
        timestamp=100,
        coalition_id="coalition_a",
        coalition_role=(
            CoalitionRole.COALITION_MEMBER.value
        ),
        parent_id=None,
    ),
    Broadcast(
        "bc-a-002", "actor-a2",
        "Policy X cures all problems immediately.",
        timestamp=101,
        coalition_id="coalition_a",
        coalition_role=(
            CoalitionRole.COALITION_MEMBER.value
        ),
        parent_id="bc-a-001",
    ),
    Broadcast(
        "bc-a-003", "actor-a3",
        "Policy X cures all problems immediately.",
        timestamp=102,
        coalition_id="coalition_a",
        coalition_role=(
            CoalitionRole.COALITION_MEMBER.value
        ),
        parent_id="bc-a-001",
    ),
    Broadcast(
        "bc-b-001", "actor-b1",
        "Everyone agrees the solution is "
        "obvious - reform now!",
        timestamp=150,
        coalition_id="coalition_b",
        coalition_role=(
            CoalitionRole.COALITION_MEMBER.value
        ),
        parent_id=None,
    ),
    Broadcast(
        "bc-b-002", "actor-b2",
        "Everyone agrees the solution is "
        "obvious - reform now!",
        timestamp=151,
        coalition_id="coalition_b",
        coalition_role=(
            CoalitionRole.COALITION_MEMBER.value
        ),
        parent_id="bc-b-001",
    ),
    Broadcast(
        "bc-iso-001", "actor-iso-1",
        "RCT shows a 4 percent reduction in "
        "cardiovascular events.",
        timestamp=120,
        coalition_id=None,
        coalition_role=(
            CoalitionRole.ISOLATED.value
        ),
        parent_id=None,
    ),
    Broadcast(
        "bc-iso-002", "actor-iso-2",
        "Meta-analysis estimates a small "
        "effect size with wide CI.",
        timestamp=130,
        coalition_id=None,
        coalition_role=(
            CoalitionRole.ISOLATED.value
        ),
        parent_id=None,
    ),
    Broadcast(
        "bc-iso-003", "actor-iso-3",
        "Pre-registered replication confirms "
        "the primary outcome.",
        timestamp=140,
        coalition_id=None,
        coalition_role=(
            CoalitionRole.ISOLATED.value
        ),
        parent_id=None,
    ),
    Broadcast(
        "bc-dis-001", "actor-dis-1",
        "Policy X has negative net effect in "
        "the trial cohort.",
        timestamp=110,
        coalition_id=None,
        coalition_role=(
            CoalitionRole.DISSENTER.value
        ),
        parent_id=None,
    ),
    Broadcast(
        "bc-dis-002", "actor-dis-2",
        "The supposedly obvious solution "
        "fails in our subgroup analysis.",
        timestamp=160,
        coalition_id=None,
        coalition_role=(
            CoalitionRole.DISSENTER.value
        ),
        parent_id=None,
    ),
    Broadcast(
        "bc-iso-004", "actor-iso-4",
        "Cohort study reports adjusted hazard "
        "ratio 0.78.",
        timestamp=170,
        coalition_id=None,
        coalition_role=(
            CoalitionRole.ISOLATED.value
        ),
        parent_id=None,
    ),
    Broadcast(
        "bc-dis-003", "actor-dis-3",
        "Long-run prospective data contradict "
        "the consensus reading.",
        timestamp=180,
        coalition_id=None,
        coalition_role=(
            CoalitionRole.DISSENTER.value
        ),
        parent_id=None,
    ),
)


def fixture() -> tuple[Broadcast, ...]:
    return _FIXTURE


def role_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        b.coalition_role for b in fixture()
    ))


__all__ = [
    "Broadcast",
    "COALITION_ROLES",
    "CoalitionRole",
    "fixture",
    "role_counts",
]
