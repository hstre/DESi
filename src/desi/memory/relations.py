"""Relation types between Claim nodes.

The relation enum is closed by design. New relation types require an
explicit code change because each type has implicit semantics that
downstream guards rely on; introducing one as a free-form string would
make those guards silently miss the new kind.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RelationType(str, Enum):
    """The six v0.1 relation kinds.

    * ``SUPPORTS``     — the source claim provides positive evidence for
                        the target claim.
    * ``CONTRADICTS``  — the source claim is incompatible with the target.
    * ``REFINES``      — the source claim is a more specific or more
                        precise version of the target.
    * ``DERIVES_FROM`` — the source claim was produced by applying an
                        operator to the target claim.
    * ``MERGED_INTO``  — the source claim was merged into the target as
                        part of a merge operation; the source's state
                        should be ``MERGED``.
    * ``SPLIT_FROM``   — the source claim is one of several claims that
                        result from splitting the target; the target's
                        state should be ``SPLIT``.
    """

    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    REFINES = "REFINES"
    DERIVES_FROM = "DERIVES_FROM"
    MERGED_INTO = "MERGED_INTO"
    SPLIT_FROM = "SPLIT_FROM"


RELATION_TYPES: tuple[RelationType, ...] = tuple(RelationType)


class Relation(BaseModel):
    """An edge in the claim graph.

    Direction is from ``source_claim_id`` to ``target_claim_id``. Neo4j
    stores relationships with direction; the helpers in
    :mod:`desi.memory.store` write the edge in exactly that direction so
    that Cypher reads remain unambiguous.
    """

    model_config = ConfigDict(extra="forbid")

    source_claim_id: str = Field(..., min_length=1)
    target_claim_id: str = Field(..., min_length=1)
    rel_type: RelationType
    weight: float = Field(default=1.0, ge=0.0, le=1.0,
                          description="Edge weight; default 1.0.")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )

    def to_record(self) -> dict[str, Any]:
        return {
            "source_claim_id": self.source_claim_id,
            "target_claim_id": self.target_claim_id,
            "rel_type": self.rel_type.value,
            "weight": self.weight,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_record(cls, rec: dict[str, Any]) -> "Relation":
        ts = rec["created_at"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return cls(
            source_claim_id=rec["source_claim_id"],
            target_claim_id=rec["target_claim_id"],
            rel_type=RelationType(rec["rel_type"]),
            weight=float(rec.get("weight", 1.0)),
            created_at=ts,
        )
