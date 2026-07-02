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
    epistemic_mode: dict[str, Any] | None = None   # governance decision, when a report was supplied
    decision_hash: str = field(default="", init=False)

    def __post_init__(self) -> None:
        body: dict[str, Any] = {
            "query": self.query,
            "task_class": self.task_class,
            "constraints": self.constraints,
            "decision": self.decision,
        }
        # Fold the epistemic mode into the SAME tamper-evident hash only when present, so a routing
        # decision and its governance mode are one auditable record — and existing (mode-less) records
        # keep byte-identical decision hashes.
        if self.epistemic_mode is not None:
            body["epistemic_mode"] = self.epistemic_mode
        canonical = json.dumps(body, sort_keys=True, ensure_ascii=False)
        self.decision_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"decision_hash": self.decision_hash}
