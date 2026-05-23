"""v36.3 - MuSiQue reference dataset loader (network-free)."""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from functools import lru_cache

from desi.external_benchmarks.dataset_hashing import content_hash


@dataclass(frozen=True)
class Hop:
    hop_id: str
    fact: str
    redundant: bool


@dataclass(frozen=True)
class MultiHopTask:
    task_id: str
    family: str
    question: str
    hops: tuple[Hop, ...]
    required_hops: tuple[str, ...]
    dataset_hash: str
    provenance: str


def load(path: pathlib.Path, family: str) -> tuple[MultiHopTask, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    dh = content_hash(payload)
    out = []
    for t in payload["tasks"]:
        out.append(MultiHopTask(
            task_id=t["task_id"],
            family=family,
            question=t["question"],
            hops=tuple(
                Hop(h["hop_id"], h["fact"], bool(h["redundant"]))
                for h in t["hops"]
            ),
            required_hops=tuple(t["required_hops"]),
            dataset_hash=dh,
            provenance=payload["provenance"],
        ))
    return tuple(out)


_DATASET = (
    pathlib.Path(__file__).resolve().parent
    / "datasets" / "musique_ref.json"
)


@lru_cache(maxsize=1)
def musique_tasks() -> tuple[MultiHopTask, ...]:
    return load(_DATASET, "MuSiQue")


__all__ = ["Hop", "MultiHopTask", "load", "musique_tasks"]
