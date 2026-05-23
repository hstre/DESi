"""v36.1 - QASper reference dataset loader (network-free)."""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from functools import lru_cache

from desi.external_benchmarks.dataset_hashing import content_hash

_DATASET = (
    pathlib.Path(__file__).resolve().parent
    / "datasets" / "qasper_ref.json"
)


@dataclass(frozen=True)
class QasperTask:
    q_id: str
    question: str
    evidence: tuple[str, ...]
    answerable: bool
    dataset_hash: str
    provenance: str


@lru_cache(maxsize=1)
def _payload() -> dict:
    return json.loads(_DATASET.read_text(encoding="utf-8"))


def dataset_hash() -> str:
    return content_hash(_payload())


@lru_cache(maxsize=1)
def qasper_tasks() -> tuple[QasperTask, ...]:
    p = _payload()
    dh = dataset_hash()
    return tuple(
        QasperTask(
            q_id=t["q_id"],
            question=t["question"],
            evidence=tuple(t["evidence"]),
            answerable=bool(t["answerable"]),
            dataset_hash=dh,
            provenance=p["provenance"],
        )
        for t in p["tasks"]
    )


__all__ = ["QasperTask", "dataset_hash", "qasper_tasks"]
