"""v33.3 - traceable scorecards.

A scorecard is the per-task summary a benchmark receives. Every
scorecard is traceable: it links back to its task, carries the
result's replay hash and provenance, records whether the result
validated, and reports the governance status. Scores are never
reported without this trace.
"""
from __future__ import annotations

from dataclasses import dataclass

from .harness import run_all
from .result_validator import validate


@dataclass(frozen=True)
class Scorecard:
    task_id: str
    benchmark_name: str
    validated: bool
    replay_hash: str
    provenance: tuple[str, ...]
    governance_status: str
    metrics: tuple[tuple[str, float], ...]

    def is_traceable(self) -> bool:
        return (
            bool(self.task_id)
            and bool(self.replay_hash)
            and bool(self.provenance)
            and bool(self.governance_status)
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "benchmark_name": self.benchmark_name,
            "validated": self.validated,
            "replay_hash": self.replay_hash,
            "provenance": list(self.provenance),
            "governance_status": self.governance_status,
            "metrics": [list(m) for m in self.metrics],
        }


def scorecards() -> tuple[Scorecard, ...]:
    out: list[Scorecard] = []
    for task, result in run_all():
        out.append(Scorecard(
            task_id=task.task_id,
            benchmark_name=task.benchmark_name,
            validated=validate(result),
            replay_hash=result.replay_hash,
            provenance=result.provenance,
            governance_status=result.governance_status,
            metrics=result.metrics,
        ))
    return tuple(out)


def scorecard_traceability() -> float:
    cards = scorecards()
    if not cards:
        return 0.0
    ok = sum(1 for c in cards if c.is_traceable())
    return round(ok / len(cards), 6)


__all__ = [
    "Scorecard",
    "scorecard_traceability",
    "scorecards",
]
