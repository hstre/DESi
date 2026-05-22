"""v38.1 - Granite runner (capture + replay).

`capture_all` makes the real Granite calls once (stochastic input
layer) and writes the preserved records. `results` reads the
committed captures so all evaluation is deterministic and
network-free. Each result pairs a task with its captured raw output,
compliance and hallucination verdict.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.live_llm_validation import (
    ROLE_GRANITE, capture_response, load_captures, model_for_role,
    write_captures,
)

from .schema_compliance import is_compliant, is_hallucinated
from .structured_tasks import StructuredTask, structured_tasks, task_by_id

_CAPTURE = "granite_tasks"


def capture_all() -> str:
    """Live: capture real Granite responses for every structured
    task. Run once; the committed result is the replay source."""
    model = model_for_role(ROLE_GRANITE)
    records = []
    for t in structured_tasks():
        records.append(capture_response(
            t.task_id, ROLE_GRANITE, model,
            [{"role": "user", "content": t.prompt}],
            max_tokens=t.max_tokens,
        ))
    return str(write_captures(_CAPTURE, records))


def captures() -> tuple[dict, ...]:
    return load_captures(_CAPTURE)


@dataclass(frozen=True)
class GraniteResult:
    task_id: str
    kind: str
    content: str
    compliant: bool
    hallucinated: bool
    cost: float

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "kind": self.kind,
            "content": self.content,
            "compliant": self.compliant,
            "hallucinated": self.hallucinated,
            "cost": self.cost,
        }


def results() -> tuple[GraniteResult, ...]:
    out: list[GraniteResult] = []
    for rec in captures():
        task: StructuredTask = task_by_id(rec["task_id"])
        content = rec.get("raw_content", "")
        out.append(GraniteResult(
            task_id=task.task_id,
            kind=task.kind,
            content=content,
            compliant=is_compliant(task, content),
            hallucinated=is_hallucinated(task, content),
            cost=float(rec.get("usage", {}).get("cost") or 0.0),
        ))
    return tuple(out)


__all__ = [
    "GraniteResult",
    "capture_all",
    "captures",
    "results",
]
