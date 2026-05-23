"""v35.0 - task normalisation.

Normalises raw external dataset items into a canonical internal form
that every downstream runner consumes. Each normalised task is bound
to its dataset's provenance, version and content hash, so a result
can always be traced back to the exact external data it came from.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .benchmark_registry import dataset_families, dataset_for, route_for
from .dataset_loader import Dataset


@dataclass(frozen=True)
class NormalizedTask:
    task_id: str
    family: str
    route: str
    kind: str
    payload: tuple[tuple[str, str], ...]
    dataset_version: str
    dataset_content_hash: str
    provenance: str

    def is_complete(self) -> bool:
        return (
            bool(self.task_id)
            and bool(self.family)
            and bool(self.route)
            and bool(self.kind)
            and bool(self.dataset_version)
            and bool(self.dataset_content_hash)
            and bool(self.provenance)
        )

    def replay_key(self) -> str:
        parts = [
            self.task_id, self.family, self.route, self.kind,
            self.dataset_version, self.dataset_content_hash,
            self.provenance,
        ]
        parts += [f"{k}={v}" for k, v in self.payload]
        return hashlib.sha256(
            "|".join(parts).encode("utf-8"),
        ).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "family": self.family,
            "route": self.route,
            "kind": self.kind,
            "payload": [list(p) for p in self.payload],
            "dataset_version": self.dataset_version,
            "dataset_content_hash": self.dataset_content_hash,
            "provenance": self.provenance,
        }


def _freeze(item: dict) -> tuple[tuple[str, str], ...]:
    skip = {"task_id", "branch_id", "kind"}
    return tuple(
        (k, str(item[k])) for k in sorted(item) if k not in skip
    )


def normalize_dataset(ds: Dataset, family: str) -> tuple[NormalizedTask, ...]:
    route = route_for(family)
    out: list[NormalizedTask] = []
    for item in ds.items():
        tid = str(item.get("task_id") or item.get("branch_id"))
        kind = str(item.get("kind", route))
        out.append(NormalizedTask(
            task_id=tid,
            family=family,
            route=route,
            kind=kind,
            payload=_freeze(item),
            dataset_version=ds.version,
            dataset_content_hash=ds.content_hash,
            provenance=ds.provenance,
        ))
    return tuple(out)


def normalized_tasks(family: str) -> tuple[NormalizedTask, ...]:
    return normalize_dataset(dataset_for(family), family)


def all_normalized_tasks() -> tuple[NormalizedTask, ...]:
    out: list[NormalizedTask] = []
    for family in dataset_families():
        out.extend(normalized_tasks(family))
    return tuple(out)


def task_normalization_integrity() -> float:
    tasks = all_normalized_tasks()
    if not tasks:
        return 0.0
    ok = sum(1 for t in tasks if t.is_complete())
    return round(ok / len(tasks), 6)


__all__ = [
    "NormalizedTask",
    "all_normalized_tasks",
    "normalize_dataset",
    "normalized_tasks",
    "task_normalization_integrity",
]
