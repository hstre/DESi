"""Run and OperatorEvent — context nodes in the memory graph.

A ``Run`` is the outermost scope: one execution of a DESi-driven session.
An ``OperatorEvent`` is the per-step record of an operator firing. Both
are stored as their own Neo4j node labels so that claims produced inside
a run can be queried back through the run, and so that the operator
provenance of a claim survives even if the claim itself is later
deleted.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Run(BaseModel):
    """A single DESi run.

    ``run_id`` is the join key between Run, OperatorEvent, and Claim
    nodes. The memory layer does not generate run ids; the caller assigns
    one (typically a UUID or timestamp string) and the same id appears
    on every event and claim produced inside the run.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str = Field(..., min_length=1)
    label: str = Field(default="", description="Optional human-readable label.")
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    finished_at: datetime | None = Field(
        default=None, description="Set when the run completes; None while live.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Free-form metadata. Values must be Neo4j-property-safe "
                    "scalars or lists thereof.",
    )

    def to_record(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "label": self.label,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat()
                            if self.finished_at else None,
            # Metadata is flattened with a "meta_" prefix to stay
            # within Neo4j's flat-property-namespace rule.
            **{f"meta_{k}": v for k, v in self.metadata.items()},
        }

    @classmethod
    def from_record(cls, rec: dict[str, Any]) -> "Run":
        meta = {k[len("meta_"):]: v for k, v in rec.items()
                if k.startswith("meta_")}
        started_at = rec["started_at"]
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)
        finished_at = rec.get("finished_at")
        if isinstance(finished_at, str):
            finished_at = datetime.fromisoformat(finished_at)
        return cls(
            run_id=rec["run_id"],
            label=rec.get("label", ""),
            started_at=started_at,
            finished_at=finished_at,
            metadata=meta,
        )


class OperatorEvent(BaseModel):
    """One operator firing inside a run.

    The event records the operator code (T1..T9 or a paper8 method
    operator), the input and output claim ids if any, the loop index
    inside the run, and an optional payload of operator-specific data.
    """

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(..., min_length=1)
    run_id: str = Field(..., min_length=1)
    operator_code: str = Field(..., min_length=1)
    loop_index: int = Field(..., ge=0)
    sub_role: str = Field(default="", description="DES sub-role tag if any "
                                                  "(e.g. 'hypothesis_builder', "
                                                  "'falsifier').")
    input_claim_ids: tuple[str, ...] = Field(default_factory=tuple)
    output_claim_ids: tuple[str, ...] = Field(default_factory=tuple)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Operator-specific extras (Neo4j-property-safe scalars).",
    )

    def to_record(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "run_id": self.run_id,
            "operator_code": self.operator_code,
            "loop_index": self.loop_index,
            "sub_role": self.sub_role,
            "input_claim_ids": list(self.input_claim_ids),
            "output_claim_ids": list(self.output_claim_ids),
            "timestamp": self.timestamp.isoformat(),
            **{f"payload_{k}": v for k, v in self.payload.items()},
        }

    @classmethod
    def from_record(cls, rec: dict[str, Any]) -> "OperatorEvent":
        payload = {k[len("payload_"):]: v for k, v in rec.items()
                   if k.startswith("payload_")}
        ts = rec["timestamp"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        return cls(
            event_id=rec["event_id"],
            run_id=rec["run_id"],
            operator_code=rec["operator_code"],
            loop_index=int(rec["loop_index"]),
            sub_role=rec.get("sub_role", ""),
            input_claim_ids=tuple(rec.get("input_claim_ids") or ()),
            output_claim_ids=tuple(rec.get("output_claim_ids") or ()),
            timestamp=ts,
            payload=payload,
        )
