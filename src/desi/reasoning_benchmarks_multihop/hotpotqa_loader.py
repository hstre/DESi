"""v36.3 - HotpotQA reference dataset loader (network-free)."""
from __future__ import annotations

import pathlib
from functools import lru_cache

from .musique_loader import MultiHopTask, load

_DATASET = (
    pathlib.Path(__file__).resolve().parent
    / "datasets" / "hotpotqa_ref.json"
)


@lru_cache(maxsize=1)
def hotpotqa_tasks() -> tuple[MultiHopTask, ...]:
    return load(_DATASET, "HotpotQA")


__all__ = ["hotpotqa_tasks"]
