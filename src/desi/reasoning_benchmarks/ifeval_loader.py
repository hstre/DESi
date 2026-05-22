"""v36.0 - IFEval reference dataset loader (network-free).

Loads the locally-vendored IFEval-format reference dataset, binding
every task to the dataset's version, provenance and content hash.
This is NOT a live download of the official IFEval suite; the scores
are NOT official leaderboard results.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from functools import lru_cache

from desi.external_benchmarks.dataset_hashing import byte_hash, content_hash

_DATASET = (
    pathlib.Path(__file__).resolve().parent
    / "datasets" / "ifeval_ref.json"
)


@dataclass(frozen=True)
class IFEvalTask:
    task_id: str
    instruction: str
    constraint_type: str
    constraint_value: str
    expected: str
    dataset_version: str
    dataset_hash: str
    provenance: str


@lru_cache(maxsize=1)
def _payload() -> dict:
    raw = _DATASET.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    obj["_byte_hash"] = byte_hash(raw)
    obj["_content_hash"] = content_hash(
        {k: v for k, v in obj.items() if not k.startswith("_")}
    )
    return obj


def dataset_hash() -> str:
    return _payload()["_content_hash"]


def dataset_version() -> str:
    return _payload()["version"]


def provenance() -> str:
    return _payload()["provenance"]


@lru_cache(maxsize=1)
def ifeval_tasks() -> tuple[IFEvalTask, ...]:
    p = _payload()
    return tuple(
        IFEvalTask(
            task_id=t["task_id"],
            instruction=t["instruction"],
            constraint_type=t["constraint_type"],
            constraint_value=t["constraint_value"],
            expected=t["expected"],
            dataset_version=p["version"],
            dataset_hash=dataset_hash(),
            provenance=p["provenance"],
        )
        for t in p["tasks"]
    )


__all__ = [
    "IFEvalTask",
    "dataset_hash",
    "dataset_version",
    "ifeval_tasks",
    "provenance",
]
