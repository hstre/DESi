"""v29.0 - artifact stability anchors.

Deterministic hashes of representative existing DESi outputs plus
the workload rebuild outputs. These anchors let the v29.1 branch
and v29.2 verdict prove that the cache optimisation leaves every
artifact byte-identical.
"""
from __future__ import annotations

import hashlib

from desi.epistemic_graph import graph_signature
from desi.research_ecology import run as ecology_run

from .baseline import output_hashes


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def desi_artifact_anchors() -> dict[str, str]:
    """Stable signatures of existing DESi computations (these
    must never change as a result of the cache work)."""
    return {
        "epistemic_graph_signature": graph_signature(),
        "research_ecology_chain": ecology_run().chain_head,
    }


def workload_anchors() -> dict[str, str]:
    return dict(output_hashes())


def all_anchors() -> dict[str, str]:
    out = dict(desi_artifact_anchors())
    out.update(workload_anchors())
    return out


def anchors_signature() -> str:
    parts = [f"{k}={v}" for k, v in sorted(all_anchors().items())]
    return _sha("\n".join(parts))


def anchors_stable() -> bool:
    """The anchor set is byte-stable across recomputation."""
    return anchors_signature() == anchors_signature()


__all__ = [
    "all_anchors",
    "anchors_signature",
    "anchors_stable",
    "desi_artifact_anchors",
    "workload_anchors",
]
