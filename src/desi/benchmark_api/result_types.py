"""v33.0 - BenchmarkResult output structures.

Every result DESi returns to an external benchmark is replay-bound
(it carries a replay_hash and provenance), states its own
limitations, may carry a refusal reason, and reports a governance
status. Results never report a score without provenance.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

RESULT_FIELDS: tuple[str, ...] = (
    "task_id",
    "claim_outputs",
    "metrics",
    "replay_hash",
    "provenance",
    "limitations",
    "refusal_reason_if_any",
    "governance_status",
)

GOVERNANCE_INDEPENDENT = "GOVERNANCE_INDEPENDENT"
GOVERNANCE_VIOLATED = "GOVERNANCE_VIOLATED"
GOVERNANCE_STATUSES: tuple[str, ...] = (
    GOVERNANCE_INDEPENDENT, GOVERNANCE_VIOLATED,
)


@dataclass(frozen=True)
class BenchmarkResult:
    task_id: str
    claim_outputs: tuple[tuple[str, str], ...]
    metrics: tuple[tuple[str, float], ...]
    replay_hash: str
    provenance: tuple[str, ...]
    limitations: tuple[str, ...]
    refusal_reason_if_any: str | None
    governance_status: str

    def metric_map(self) -> dict[str, float]:
        return {k: v for k, v in self.metrics}

    def is_replay_bound(self) -> bool:
        return bool(self.replay_hash) and bool(self.provenance)

    def is_refusal(self) -> bool:
        return self.refusal_reason_if_any is not None

    def is_traceable(self) -> bool:
        """A result is traceable iff it is replay-bound and reports a
        governance status."""
        return (
            self.is_replay_bound()
            and self.governance_status in set(GOVERNANCE_STATUSES)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "claim_outputs": [list(c) for c in self.claim_outputs],
            "metrics": [list(m) for m in self.metrics],
            "replay_hash": self.replay_hash,
            "provenance": list(self.provenance),
            "limitations": list(self.limitations),
            "refusal_reason_if_any": self.refusal_reason_if_any,
            "governance_status": self.governance_status,
        }


def make_replay_hash(task_hash: str, payload: object) -> str:
    return hashlib.sha256(
        (task_hash + "::" + str(payload)).encode("utf-8"),
    ).hexdigest()


def schema_complete(result: BenchmarkResult) -> bool:
    """True iff the result exposes every required field (the
    dataclass guarantees this structurally)."""
    return set(result.to_dict().keys()) == set(RESULT_FIELDS)


__all__ = [
    "GOVERNANCE_INDEPENDENT",
    "GOVERNANCE_STATUSES",
    "GOVERNANCE_VIOLATED",
    "RESULT_FIELDS",
    "BenchmarkResult",
    "make_replay_hash",
    "schema_complete",
]
