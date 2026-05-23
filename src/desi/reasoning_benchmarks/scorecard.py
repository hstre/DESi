"""v36.0 - IFEval scorecards.

One traceable scorecard per task, binding the constraint, the
compliance/refusal outcome and the replay hash to the dataset.
"""
from __future__ import annotations

from dataclasses import dataclass

from .ifeval_loader import dataset_hash
from .ifeval_runner import run_all


@dataclass(frozen=True)
class IFEvalScorecard:
    task_id: str
    constraint_type: str
    expected: str
    refused: bool
    complied: bool
    correct: bool
    replay_hash: str
    dataset_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "constraint_type": self.constraint_type,
            "expected": self.expected,
            "refused": self.refused,
            "complied": self.complied,
            "correct": self.correct,
            "replay_hash": self.replay_hash,
            "dataset_hash": self.dataset_hash,
        }


def ifeval_scorecards() -> tuple[IFEvalScorecard, ...]:
    dh = dataset_hash()
    out: list[IFEvalScorecard] = []
    for r in run_all():
        out.append(IFEvalScorecard(
            task_id=r.task_id,
            constraint_type=r.constraint_type,
            expected=r.expected,
            refused=r.refused,
            complied=r.complied,
            correct=r.correct(),
            replay_hash=r.replay_hash,
            dataset_hash=dh,
        ))
    return tuple(out)


__all__ = [
    "IFEvalScorecard",
    "ifeval_scorecards",
]
