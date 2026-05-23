"""v36.2 - ReClor reference dataset loader (network-free)."""
from __future__ import annotations

import pathlib
from functools import lru_cache

from .logiqa_loader import LogicTask, _load

_DATASET = (
    pathlib.Path(__file__).resolve().parent
    / "datasets" / "reclor_ref.json"
)


@lru_cache(maxsize=1)
def reclor_tasks() -> tuple[LogicTask, ...]:
    return _load(_DATASET, "ReClor")


def dataset_hash() -> str:
    return reclor_tasks()[0].dataset_hash if reclor_tasks() else ""


__all__ = ["dataset_hash", "reclor_tasks"]
