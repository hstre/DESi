"""Claim object for DESi's memory layer.

The Claim object is the unit of stored knowledge. It separates **what** is
asserted (``content``) from **how** the assertion was produced (``method``)
so that two claims with the same surface content but different derivations
are not collapsed in storage. Provenance is mandatory.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ClaimState(str, Enum):
    """Lifecycle state of a claim.

    The enum is open in spirit (downstream pipelines may introduce more
    states) but closed at the storage boundary: only these values map to
    a Neo4j ``state`` property without translation.
    """

    PROPOSED = "proposed"
    REVISED = "revised"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    MERGED = "merged"
    SPLIT = "split"


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


class Provenance(BaseModel):
    """Where and how a claim was produced.

    All four fields are required at construction time. The memory layer
    refuses to store a claim with empty provenance because that is the most
    common cause of un-reproducible memory state.
    """

    model_config = ConfigDict(extra="forbid")

    source: str = Field(..., min_length=1, description="Logical source name "
                                                       "(e.g. 'des_v0.1', "
                                                       "'human_annotation').")
    run_id: str = Field(..., min_length=1, description="Run identifier; "
                                                       "matches Run.run_id.")
    operator_path: tuple[str, ...] = Field(
        default_factory=tuple,
        description=(
            "Ordered sequence of operator codes that produced this claim. "
            "Empty for human-authored claims; non-empty for derived claims."
        ),
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp at the moment of derivation.",
    )

    def to_record(self) -> dict[str, Any]:
        """Flatten to a Neo4j-friendly property dict (no nested objects)."""
        return {
            "source": self.source,
            "run_id": self.run_id,
            "operator_path": list(self.operator_path),
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_record(cls, rec: dict[str, Any]) -> "Provenance":
        ts = rec["timestamp"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return cls(
            source=rec["source"],
            run_id=rec["run_id"],
            operator_path=tuple(rec.get("operator_path") or ()),
            timestamp=ts,
        )


# ---------------------------------------------------------------------------
# Claim
# ---------------------------------------------------------------------------


class Claim(BaseModel):
    """A unit of stored knowledge.

    Identity rules:

    * ``claim_id`` is the storage identity. If omitted, it is derived
      deterministically from ``content`` + ``method`` + ``provenance.run_id``
      so that the same input always maps to the same id, independent of
      timestamp.
    * ``version`` is incremented by the caller when revising a claim; the
      memory layer does not auto-version because that would couple state
      transitions to storage timing.
    """

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(default="", description="Storage identity. "
                                                  "Derived if empty.")
    content: str = Field(..., min_length=1, description="The assertion.")
    method: str = Field(..., min_length=1, description="How the assertion "
                                                       "was derived "
                                                       "(operator code, "
                                                       "rule name, or "
                                                       "human-tag).")
    state: ClaimState = Field(default=ClaimState.PROPOSED,
                              description="Lifecycle state.")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0,
                              description="Subjective confidence in [0, 1]. "
                                          "Memory layer does not adjust this "
                                          "value; only operators may.")
    version: int = Field(default=1, ge=1,
                         description="Caller-managed revision counter.")
    provenance: Provenance

    def model_post_init(self, __context: Any) -> None:
        if not self.claim_id:
            object.__setattr__(self, "claim_id", self._derive_id())

    def _derive_id(self) -> str:
        h = hashlib.sha256()
        h.update(self.content.encode("utf-8"))
        h.update(b"\x00")
        h.update(self.method.encode("utf-8"))
        h.update(b"\x00")
        h.update(self.provenance.run_id.encode("utf-8"))
        return "c_" + h.hexdigest()[:16]

    def to_record(self) -> dict[str, Any]:
        """Serialise to a flat dict suitable for Neo4j node properties.

        Provenance is flattened with ``prov_`` prefix to keep the node
        property namespace flat — Neo4j does not allow nested maps as
        property values.
        """
        prov = self.provenance.to_record()
        return {
            "claim_id": self.claim_id,
            "content": self.content,
            "method": self.method,
            "state": self.state.value,
            "confidence": self.confidence,
            "version": self.version,
            "prov_source": prov["source"],
            "prov_run_id": prov["run_id"],
            "prov_operator_path": prov["operator_path"],
            "prov_timestamp": prov["timestamp"],
        }

    @classmethod
    def from_record(cls, rec: dict[str, Any]) -> "Claim":
        prov = Provenance.from_record({
            "source": rec["prov_source"],
            "run_id": rec["prov_run_id"],
            "operator_path": rec.get("prov_operator_path") or [],
            "timestamp": rec["prov_timestamp"],
        })
        return cls(
            claim_id=rec["claim_id"],
            content=rec["content"],
            method=rec["method"],
            state=ClaimState(rec["state"]),
            confidence=float(rec["confidence"]),
            version=int(rec["version"]),
            provenance=prov,
        )
