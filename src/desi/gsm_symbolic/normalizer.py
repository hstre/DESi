"""GSM-Symbolic G0 - task normalisation.

Turns each loaded instance into a canonical :class:`NormalizedGsmTask`
that downstream runners (G1+) consume. Every normalised task is bound to
its dataset's provenance, version and content hash, and preserves both
``template_id`` and ``instance_id`` so that paraphrase/template groups
can be reconstructed deterministically for the frame-invariance metrics.

Mirrors ``external_benchmarks.task_normalizer`` (sha256 ``replay_key``,
frozen task) without importing it, to keep this package self-contained.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .loader import GsmDataset, GsmInstance, load_all, load_dataset


@dataclass(frozen=True)
class NormalizedGsmTask:
    task_id: str
    family: str
    variant: str
    template_id: str
    instance_id: str
    question: str
    answer: str
    answer_type: str
    clause_role: str
    dataset_version: str
    dataset_content_hash: str
    provenance: str

    def is_complete(self) -> bool:
        return all((
            self.task_id,
            self.family,
            self.variant,
            self.template_id,
            self.instance_id,
            self.question,
            self.answer,
            self.answer_type,
            self.dataset_version,
            self.dataset_content_hash,
            self.provenance,
        ))

    def replay_key(self) -> str:
        parts = [
            self.task_id, self.family, self.variant,
            self.template_id, self.instance_id,
            self.question, self.answer, self.answer_type,
            self.clause_role, self.dataset_version,
            self.dataset_content_hash, self.provenance,
        ]
        return hashlib.sha256(
            "|".join(parts).encode("utf-8"),
        ).hexdigest()

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "family": self.family,
            "variant": self.variant,
            "template_id": self.template_id,
            "instance_id": self.instance_id,
            "question": self.question,
            "answer": self.answer,
            "answer_type": self.answer_type,
            "clause_role": self.clause_role,
            "dataset_version": self.dataset_version,
            "dataset_content_hash": self.dataset_content_hash,
            "provenance": self.provenance,
        }


def _normalize_instance(
    ds: GsmDataset, inst: GsmInstance,
) -> NormalizedGsmTask:
    return NormalizedGsmTask(
        task_id=inst.instance_id,
        family=ds.family,
        variant=ds.variant,
        template_id=inst.template_id,
        instance_id=inst.instance_id,
        question=inst.question,
        answer=inst.answer,
        answer_type=inst.answer_type,
        clause_role=inst.clause_role,
        dataset_version=ds.version,
        dataset_content_hash=ds.content_hash,
        provenance=ds.provenance,
    )


def normalize_dataset(ds: GsmDataset) -> tuple[NormalizedGsmTask, ...]:
    return tuple(
        _normalize_instance(ds, inst) for inst in ds.instances()
    )


def normalized_tasks(name: str) -> tuple[NormalizedGsmTask, ...]:
    return normalize_dataset(load_dataset(name))


def all_normalized_tasks() -> tuple[NormalizedGsmTask, ...]:
    out: list[NormalizedGsmTask] = []
    for ds in load_all():
        out.extend(normalize_dataset(ds))
    return tuple(out)


def task_normalization_integrity() -> float:
    tasks = all_normalized_tasks()
    if not tasks:
        return 0.0
    ok = sum(1 for t in tasks if t.is_complete())
    return round(ok / len(tasks), 6)


__all__ = [
    "NormalizedGsmTask",
    "all_normalized_tasks",
    "normalize_dataset",
    "normalized_tasks",
    "task_normalization_integrity",
]
