"""v36.1 - SciFact reference dataset loader (network-free)."""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from functools import lru_cache

from desi.external_benchmarks.dataset_hashing import content_hash

_DATASET = (
    pathlib.Path(__file__).resolve().parent
    / "datasets" / "scifact_ref.json"
)


@dataclass(frozen=True)
class SciFactTask:
    claim_id: str
    claim: str
    evidence: tuple[tuple[str, str], ...]
    cited_evidence: tuple[str, ...]
    label: str
    dataset_hash: str
    provenance: str


@lru_cache(maxsize=1)
def _payload() -> dict:
    return json.loads(_DATASET.read_text(encoding="utf-8"))


def dataset_hash() -> str:
    return content_hash(_payload())


@lru_cache(maxsize=1)
def scifact_tasks() -> tuple[SciFactTask, ...]:
    p = _payload()
    dh = dataset_hash()
    out = []
    for t in p["tasks"]:
        out.append(SciFactTask(
            claim_id=t["claim_id"],
            claim=t["claim"],
            evidence=tuple(
                (e["id"], e["stance"]) for e in t["evidence"]
            ),
            cited_evidence=tuple(t["cited_evidence"]),
            label=t["label"],
            dataset_hash=dh,
            provenance=p["provenance"],
        ))
    return tuple(out)


__all__ = ["SciFactTask", "dataset_hash", "scifact_tasks"]
