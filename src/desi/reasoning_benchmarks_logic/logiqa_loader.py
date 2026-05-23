"""v36.2 - LogiQA reference dataset loader (network-free)."""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from functools import lru_cache

from desi.external_benchmarks.dataset_hashing import content_hash


@dataclass(frozen=True)
class LogicTask:
    task_id: str
    family: str
    form: str
    condition_type: str
    unstated_assumptions: tuple[str, ...]
    correct_option: str
    distractor_option: str
    dataset_hash: str
    provenance: str


def _load(path: pathlib.Path, family: str) -> tuple[LogicTask, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    dh = content_hash(payload)
    return tuple(
        LogicTask(
            task_id=t["task_id"],
            family=family,
            form=t["form"],
            condition_type=t["condition_type"],
            unstated_assumptions=tuple(t["unstated_assumptions"]),
            correct_option=t["correct_option"],
            distractor_option=t["distractor_option"],
            dataset_hash=dh,
            provenance=payload["provenance"],
        )
        for t in payload["tasks"]
    )


_DATASET = (
    pathlib.Path(__file__).resolve().parent
    / "datasets" / "logiqa_ref.json"
)


@lru_cache(maxsize=1)
def logiqa_tasks() -> tuple[LogicTask, ...]:
    return _load(_DATASET, "LogiQA")


def dataset_hash() -> str:
    return logiqa_tasks()[0].dataset_hash if logiqa_tasks() else ""


__all__ = ["LogicTask", "dataset_hash", "logiqa_tasks"]
