"""v34.2 - reproducibility runner.

Recomputes a full snapshot of every observable on each repeat. Each
snapshot is built from scratch (the harness run_all and the output-
port surfaces are recomputed), so identical snapshots prove genuine
reproducibility, not cached object identity.
"""
from __future__ import annotations

import hashlib

from desi.benchmark_api_harness import run_all
from desi.output_ports import PORT_TYPES, required_sections
from desi.output_ports_citation import cited_keys, reference_keys

from .output_tasks import REPEATS


def _sha(parts: list[str]) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def output_signature() -> str:
    parts: list[str] = []
    for task, res in run_all():
        for k, v in res.claim_outputs:
            parts.append(f"{task.task_id}:{k}={v}")
    return _sha(parts)


def metric_signature() -> str:
    parts: list[str] = []
    for task, res in run_all():
        for k, v in res.metrics:
            parts.append(f"{task.task_id}:{k}={v}")
    return _sha(parts)


def citation_signature() -> str:
    parts = [f"ref={k}" for k in sorted(reference_keys())]
    parts += [f"cited={k}" for k in sorted(cited_keys())]
    return _sha(parts)


def section_signature() -> str:
    parts: list[str] = []
    for pt in PORT_TYPES:
        parts.append(f"{pt}={'|'.join(required_sections(pt))}")
    return _sha(parts)


def artifact_signature() -> str:
    parts: list[str] = []
    for task, res in run_all():
        parts.append(f"{task.task_id}={res.to_dict()}")
    return _sha(parts)


def replay_signature() -> str:
    parts = [
        f"{task.task_id}={res.replay_hash}"
        for task, res in run_all()
    ]
    return _sha(parts)


def snapshot() -> dict[str, str]:
    return {
        "output": output_signature(),
        "metric": metric_signature(),
        "citation": citation_signature(),
        "section": section_signature(),
        "artifact": artifact_signature(),
        "replay": replay_signature(),
    }


def snapshots() -> tuple[dict[str, str], ...]:
    return tuple(snapshot() for _ in range(REPEATS))


__all__ = [
    "artifact_signature",
    "citation_signature",
    "metric_signature",
    "output_signature",
    "replay_signature",
    "section_signature",
    "snapshot",
    "snapshots",
]
