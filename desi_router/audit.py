"""Deterministic audit record for every routing decision.

DESi's discipline: the decision is replay-stable even though the model output is
not. The audit record hashes the canonical (query + constraints + decision) so
the *routing* is reproducible and tamper-evident; the model's answer is recorded
but explicitly outside the deterministic boundary.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AuditRecord:
    query: str
    task_class: str
    constraints: dict[str, Any]
    decision: dict[str, Any]
    answer: str | None = None
    answer_source: str = ""             # "tool" | "model:<id>" | "none"
    decision_hash: str = field(default="", init=False)

    def __post_init__(self) -> None:
        canonical = json.dumps(
            {
                "query": self.query,
                "task_class": self.task_class,
                "constraints": self.constraints,
                "decision": self.decision,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        self.decision_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"decision_hash": self.decision_hash}
