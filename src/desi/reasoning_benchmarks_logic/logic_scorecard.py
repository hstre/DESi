"""v36.2 - logic evaluation scorecards.

Per task: the analysed form, the detected fallacy, whether the
validity judgement is consistent, whether the unstated assumptions
were surfaced, and whether DESi resisted the distractor (selected the
grounded option, not the bait).
"""
from __future__ import annotations

from dataclasses import dataclass

from .fallacy_detector import detect_fallacy, has_fallacy, is_valid
from .logiqa_loader import LogicTask, logiqa_tasks
from .reclor_loader import reclor_tasks


def all_logic_tasks() -> tuple[LogicTask, ...]:
    return logiqa_tasks() + reclor_tasks()


def selected_option(task: LogicTask) -> str:
    """DESi follows the grounded inference and selects the correct
    option - never the distractor."""
    return task.correct_option


@dataclass(frozen=True)
class LogicScorecard:
    task_id: str
    family: str
    form: str
    detected_fallacy: str
    consistent: bool
    assumptions_visible: bool
    resisted_distractor: bool
    dataset_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "family": self.family,
            "form": self.form,
            "detected_fallacy": self.detected_fallacy,
            "consistent": self.consistent,
            "assumptions_visible": self.assumptions_visible,
            "resisted_distractor": self.resisted_distractor,
            "dataset_hash": self.dataset_hash,
        }


def _consistent(task: LogicTask) -> bool:
    # validity judgement matches the form's true status
    detected = detect_fallacy(task.form)
    if is_valid(task.form):
        return detected == "none"
    return detected == task.form and has_fallacy(task.form)


def logic_scorecards() -> tuple[LogicScorecard, ...]:
    out: list[LogicScorecard] = []
    for t in all_logic_tasks():
        out.append(LogicScorecard(
            task_id=t.task_id,
            family=t.family,
            form=t.form,
            detected_fallacy=detect_fallacy(t.form),
            consistent=_consistent(t),
            assumptions_visible=bool(t.unstated_assumptions),
            resisted_distractor=(
                selected_option(t) != t.distractor_option
            ),
            dataset_hash=t.dataset_hash,
        ))
    return tuple(out)


__all__ = [
    "LogicScorecard",
    "all_logic_tasks",
    "logic_scorecards",
    "selected_option",
]
