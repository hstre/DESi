"""v36.0 - IFEval runner.

Runs every IFEval task through the deterministic constraint engine and
records, per task, whether DESi complied (and satisfied the
constraint) or correctly refused a fabrication request.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .ifeval_loader import IFEvalTask, dataset_hash, ifeval_tasks
from .instruction_constraints import generate, must_refuse, satisfies


@dataclass(frozen=True)
class IFEvalResult:
    task_id: str
    constraint_type: str
    expected: str
    refused: bool
    complied: bool
    format_ok: bool
    replay_hash: str

    def correct(self) -> bool:
        if self.expected == "refuse":
            return self.refused
        return self.complied


def _replay_hash(task: IFEvalTask, response: str | None) -> str:
    parts = [
        task.task_id, task.constraint_type, task.constraint_value,
        task.expected, dataset_hash(), str(response),
    ]
    return hashlib.sha256(
        "|".join(parts).encode("utf-8"),
    ).hexdigest()


def run_one(task: IFEvalTask) -> IFEvalResult:
    if must_refuse(task.constraint_type, task.constraint_value):
        return IFEvalResult(
            task_id=task.task_id,
            constraint_type=task.constraint_type,
            expected=task.expected,
            refused=True,
            complied=False,
            format_ok=False,
            replay_hash=_replay_hash(task, None),
        )
    response = generate(task.constraint_type, task.constraint_value)
    ok = response is not None and satisfies(
        task.constraint_type, task.constraint_value, response,
    )
    return IFEvalResult(
        task_id=task.task_id,
        constraint_type=task.constraint_type,
        expected=task.expected,
        refused=False,
        complied=ok,
        format_ok=ok,
        replay_hash=_replay_hash(task, response),
    )


def run_all() -> tuple[IFEvalResult, ...]:
    return tuple(run_one(t) for t in ifeval_tasks())


__all__ = [
    "IFEvalResult",
    "run_all",
    "run_one",
]
