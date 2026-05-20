"""Aufgabe 5 — best-overlap mapping from perturbation
clusters to canonical v5.0 clusters.

Deterministic, no manual mapping. For each perturbation
cluster we measure overlap with every canonical cluster
and assign the canonical with the largest member
intersection. Ties broken alphabetically on canonical
name.

A perturbation cluster whose best overlap is zero is
considered *novel* (no canonical anchor).
"""
from __future__ import annotations

from dataclasses import dataclass

from .baseline import CanonicalBaseline
from .perturbations import PerturbationRun


def _strip_suffix(chain_id: str) -> str:
    """Strip the ``#b<idx>`` / ``#x<idx>`` suffix that
    bootstrap / domain-overweight perturbations append, so
    overlap is measured against the *original* canonical
    chain ids."""
    for sep in ("#b", "#x"):
        if sep in chain_id:
            return chain_id.split(sep, 1)[0]
    return chain_id


@dataclass(frozen=True)
class PerturbClusterMapping:
    perturb_cluster_name: str
    canonical_target: str | None  # None when novel
    overlap_count: int
    perturb_size: int
    is_novel: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "perturb_cluster_name":
                self.perturb_cluster_name,
            "canonical_target": self.canonical_target,
            "overlap_count": self.overlap_count,
            "perturb_size": self.perturb_size,
            "is_novel": self.is_novel,
        }


@dataclass(frozen=True)
class RunMapping:
    run_id: str
    family: str
    canonical_targets: tuple[str, ...]   # the canonical names hit
    canonical_survivors: tuple[str, ...]
    canonical_missing: tuple[str, ...]
    novel_clusters: tuple[str, ...]
    mappings: tuple[PerturbClusterMapping, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "family": self.family,
            "canonical_targets": list(self.canonical_targets),
            "canonical_survivors":
                list(self.canonical_survivors),
            "canonical_missing":
                list(self.canonical_missing),
            "novel_clusters": list(self.novel_clusters),
            "mappings": [m.to_dict() for m in self.mappings],
        }


def map_run_to_canonical(
    run: PerturbationRun, baseline: CanonicalBaseline,
) -> RunMapping:
    canonical_members = {
        c.name: set(c.member_ids) for c in baseline.clusters
    }
    canonical_names = tuple(sorted(canonical_members))
    mappings: list[PerturbClusterMapping] = []
    targets: list[str] = []
    novels: list[str] = []
    for entry in run.taxonomy:
        members = {
            _strip_suffix(m) for m in entry.member_ids
        }
        best_name: str | None = None
        best_overlap = 0
        for cname in canonical_names:
            ov = len(members & canonical_members[cname])
            if ov > best_overlap or (
                ov == best_overlap and best_name is not None
                and cname < best_name and ov > 0
            ):
                best_overlap = ov
                best_name = cname
        is_novel = best_overlap == 0
        target = None if is_novel else best_name
        if target is not None:
            targets.append(target)
        else:
            novels.append(entry.taxonomy_name)
        mappings.append(PerturbClusterMapping(
            perturb_cluster_name=entry.taxonomy_name,
            canonical_target=target,
            overlap_count=best_overlap,
            perturb_size=entry.size,
            is_novel=is_novel,
        ))
    survivors = tuple(sorted(set(targets)))
    missing = tuple(
        n for n in canonical_names if n not in set(targets)
    )
    return RunMapping(
        run_id=run.run_id, family=run.family,
        canonical_targets=tuple(targets),
        canonical_survivors=survivors,
        canonical_missing=missing,
        novel_clusters=tuple(novels),
        mappings=tuple(mappings),
    )


def build_cluster_mapping_matrix(
    runs: tuple[PerturbationRun, ...],
    baseline: CanonicalBaseline,
) -> dict[str, object]:
    """Per-run mappings + matrix of canonical-name presence.

    The matrix is a dict[canonical_name -> dict[run_id -> bool]]
    indicating whether that canonical class was hit at all
    in that run.
    """
    run_mappings = tuple(
        map_run_to_canonical(r, baseline) for r in runs
    )
    matrix: dict[str, dict[str, bool]] = {}
    for c in baseline.clusters:
        matrix[c.name] = {}
    for rm in run_mappings:
        hit = set(rm.canonical_targets)
        for c in baseline.clusters:
            matrix[c.name][rm.run_id] = c.name in hit
    return {
        "run_mappings": [rm.to_dict() for rm in run_mappings],
        "canonical_presence_matrix": {
            name: dict(cells) for name, cells in matrix.items()
        },
    }


__all__ = [
    "PerturbClusterMapping", "RunMapping",
    "build_cluster_mapping_matrix",
    "map_run_to_canonical",
]
