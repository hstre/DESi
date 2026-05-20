"""Aufgabe 3 — freeze the v5.0 canonical baseline.

This module reads ``artifacts/v5_0/taxonomy.json`` and
``artifacts/v5_0/report.json`` as the canonical reference.
The 565 chains and 8 ``MT_*`` classes are frozen here; no
class renaming, no taxonomy edits.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import pathlib


_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
_V50_DIR = _REPO_ROOT / "artifacts" / "v5_0"


@dataclass(frozen=True)
class CanonicalCluster:
    name: str
    size: int
    member_ids: tuple[str, ...]


@dataclass(frozen=True)
class CanonicalBaseline:
    chain_count: int
    failure_count: int
    cluster_count: int
    largest_cluster_fraction: float
    clusters: tuple[CanonicalCluster, ...]
    member_to_cluster: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return {
            "chain_count": self.chain_count,
            "failure_count": self.failure_count,
            "cluster_count": self.cluster_count,
            "largest_cluster_fraction":
                self.largest_cluster_fraction,
            "clusters": [
                {
                    "name": c.name,
                    "size": c.size,
                    "member_ids": list(c.member_ids),
                }
                for c in self.clusters
            ],
        }


def _load_taxonomy_json() -> dict[str, object]:
    p = _V50_DIR / "taxonomy.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _load_report_json() -> dict[str, object]:
    p = _V50_DIR / "report.json"
    return json.loads(p.read_text(encoding="utf-8"))


def load_canonical_baseline() -> CanonicalBaseline:
    tax = _load_taxonomy_json()
    rep = _load_report_json()
    clusters: list[CanonicalCluster] = []
    member_to_cluster: dict[str, str] = {}
    for entry in tax["taxonomy"]:
        name = entry["taxonomy_name"]
        members = tuple(entry["member_ids"])
        clusters.append(CanonicalCluster(
            name=name, size=entry["size"],
            member_ids=members,
        ))
        for m in members:
            member_to_cluster[m] = name
    return CanonicalBaseline(
        chain_count=int(rep["corpus_size"]),
        failure_count=int(tax["failure_count"]),
        cluster_count=int(tax["cluster_count"]),
        largest_cluster_fraction=float(
            tax["largest_cluster_fraction"]
        ),
        clusters=tuple(clusters),
        member_to_cluster=member_to_cluster,
    )


__all__ = [
    "CanonicalBaseline", "CanonicalCluster",
    "load_canonical_baseline",
]
