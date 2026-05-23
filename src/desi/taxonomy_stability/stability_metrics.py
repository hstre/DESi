"""Aufgabe 6 / 7 / 8 — stability metrics + dominant-cluster
audit + novel-cluster tracking.

All metrics are computed from the deterministic
perturbation runs and the v5.0 canonical baseline. No
manual relabeling.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math

from .baseline import CanonicalBaseline
from .cluster_mapper import (
    RunMapping, map_run_to_canonical,
)
from .perturbations import PerturbationRun


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_suffix(chain_id: str) -> str:
    for sep in ("#b", "#x"):
        if sep in chain_id:
            return chain_id.split(sep, 1)[0]
    return chain_id


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _variance(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def _entropy(sizes: list[int]) -> float:
    total = sum(sizes)
    if total == 0:
        return 0.0
    out = 0.0
    for s in sizes:
        if s == 0:
            continue
        p = s / total
        out -= p * math.log(p, 2)
    return out


# ---------------------------------------------------------------------------
# Per-run characterisation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunCharacterisation:
    run_id: str
    family: str
    cluster_count: int
    largest_fraction: float
    entropy: float
    survivors: int
    split_count: int        # canonical classes hit by >1 perturb cluster
    merge_count: int        # perturb clusters whose members span >1 canonical
    novel_count: int        # perturb clusters with zero canonical overlap
    label_overlap: float    # fraction of chains assigned to same canonical
    dominant_rank: int      # 1-indexed rank of canonical dominant in this run

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "family": self.family,
            "cluster_count": self.cluster_count,
            "largest_fraction": self.largest_fraction,
            "entropy": self.entropy,
            "survivors": self.survivors,
            "split_count": self.split_count,
            "merge_count": self.merge_count,
            "novel_count": self.novel_count,
            "label_overlap": self.label_overlap,
            "dominant_rank": self.dominant_rank,
        }


def characterise_run(
    run: PerturbationRun,
    run_mapping: RunMapping,
    baseline: CanonicalBaseline,
    *, dominant_name: str,
) -> RunCharacterisation:
    canonical_members = {
        c.name: set(c.member_ids) for c in baseline.clusters
    }
    canonical_count = len(canonical_members)

    # split: canonical hit by >1 perturb cluster
    canonical_hit_counter: Counter[str] = Counter()
    for m in run_mapping.mappings:
        if m.canonical_target is not None:
            canonical_hit_counter[m.canonical_target] += 1
    split_count = sum(
        1 for v in canonical_hit_counter.values() if v >= 2
    )

    # merge: perturb cluster whose stripped members span >1
    # canonical class (purity < 1).
    merge_count = 0
    for entry in run.taxonomy:
        stripped = {
            _strip_suffix(m) for m in entry.member_ids
        }
        labels = {
            baseline.member_to_cluster.get(m)
            for m in stripped
            if m in baseline.member_to_cluster
        }
        labels.discard(None)
        if len(labels) >= 2:
            merge_count += 1

    novel_count = sum(
        1 for m in run_mapping.mappings if m.is_novel
    )

    # label overlap: for each baseline-known chain in this
    # run, was it assigned to the same canonical class?
    overlap_num = 0
    overlap_den = 0
    chain_to_perturb_target: dict[str, str] = {}
    for entry in run.taxonomy:
        # which canonical did this perturb cluster map to?
        mapping = next(
            (m for m in run_mapping.mappings
             if m.perturb_cluster_name == entry.taxonomy_name),
            None,
        )
        target = mapping.canonical_target if mapping else None
        for cm in entry.member_ids:
            orig = _strip_suffix(cm)
            chain_to_perturb_target[orig] = target or "_novel"
    for orig, target in chain_to_perturb_target.items():
        canonical_label = baseline.member_to_cluster.get(orig)
        if canonical_label is None:
            continue
        overlap_den += 1
        if target == canonical_label:
            overlap_num += 1
    label_overlap = (
        _round(overlap_num / overlap_den)
        if overlap_den else 0.0
    )

    # dominant rank
    ranked = sorted(
        run.taxonomy, key=lambda t: (-t.size, t.taxonomy_name),
    )
    dominant_rank = canonical_count + 1  # worst-case
    for i, entry in enumerate(ranked, start=1):
        mapping = next(
            (m for m in run_mapping.mappings
             if m.perturb_cluster_name == entry.taxonomy_name),
            None,
        )
        target = mapping.canonical_target if mapping else None
        if target == dominant_name:
            dominant_rank = i
            break

    return RunCharacterisation(
        run_id=run.run_id, family=run.family,
        cluster_count=run.cluster_count,
        largest_fraction=run.largest_cluster_fraction,
        entropy=_round(_entropy(
            [t.size for t in run.taxonomy]
        )),
        survivors=len(run_mapping.canonical_survivors),
        split_count=split_count,
        merge_count=merge_count,
        novel_count=novel_count,
        label_overlap=label_overlap,
        dominant_rank=dominant_rank,
    )


# ---------------------------------------------------------------------------
# Aggregate metrics
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StabilityMetrics:
    perturbation_count: int
    cluster_survival_rate: float
    cluster_split_rate: float
    cluster_merge_rate: float
    largest_cluster_variance: float
    taxonomy_entropy_variance: float
    label_overlap_score: float
    cross_run_agreement: float
    dominant_cluster_rank_stability: float
    dominant_cluster_size_variance: float
    novel_cluster_fraction: float

    def to_dict(self) -> dict[str, object]:
        return {
            "perturbation_count": self.perturbation_count,
            "cluster_survival_rate":
                self.cluster_survival_rate,
            "cluster_split_rate": self.cluster_split_rate,
            "cluster_merge_rate": self.cluster_merge_rate,
            "largest_cluster_variance":
                self.largest_cluster_variance,
            "taxonomy_entropy_variance":
                self.taxonomy_entropy_variance,
            "label_overlap_score":
                self.label_overlap_score,
            "cross_run_agreement":
                self.cross_run_agreement,
            "dominant_cluster_rank_stability":
                self.dominant_cluster_rank_stability,
            "dominant_cluster_size_variance":
                self.dominant_cluster_size_variance,
            "novel_cluster_fraction":
                self.novel_cluster_fraction,
        }


def _cross_run_agreement(
    runs: tuple[PerturbationRun, ...],
    mappings: tuple[RunMapping, ...],
    baseline: CanonicalBaseline,
) -> float:
    """For each pair of runs, count canonical-known chains
    that mapped to the same canonical class in both, divide
    by the number of such chains in the intersection.
    Average across pairs."""
    per_run_assign: list[dict[str, str]] = []
    for run, mp in zip(runs, mappings):
        assign: dict[str, str] = {}
        target_by_name = {
            m.perturb_cluster_name:
                m.canonical_target or "_novel"
            for m in mp.mappings
        }
        for entry in run.taxonomy:
            target = target_by_name.get(
                entry.taxonomy_name, "_novel",
            )
            for cm in entry.member_ids:
                orig = _strip_suffix(cm)
                if orig in baseline.member_to_cluster:
                    assign[orig] = target
        per_run_assign.append(assign)
    if len(per_run_assign) < 2:
        return 1.0
    agreements: list[float] = []
    n = len(per_run_assign)
    for i in range(n):
        for j in range(i + 1, n):
            a = per_run_assign[i]
            b = per_run_assign[j]
            common = set(a) & set(b)
            if not common:
                continue
            agree = sum(
                1 for k in common if a[k] == b[k]
            )
            agreements.append(agree / len(common))
    return (
        _round(sum(agreements) / len(agreements))
        if agreements else 1.0
    )


def compute_stability(
    runs: tuple[PerturbationRun, ...],
    baseline: CanonicalBaseline,
    *, dominant_name: str,
) -> tuple[StabilityMetrics, tuple[RunCharacterisation, ...]]:
    if not runs:
        empty = StabilityMetrics(
            perturbation_count=0,
            cluster_survival_rate=0.0,
            cluster_split_rate=0.0,
            cluster_merge_rate=0.0,
            largest_cluster_variance=0.0,
            taxonomy_entropy_variance=0.0,
            label_overlap_score=0.0,
            cross_run_agreement=0.0,
            dominant_cluster_rank_stability=0.0,
            dominant_cluster_size_variance=0.0,
            novel_cluster_fraction=0.0,
        )
        return empty, ()
    mappings = tuple(
        map_run_to_canonical(r, baseline) for r in runs
    )
    chars = tuple(
        characterise_run(
            r, m, baseline, dominant_name=dominant_name,
        )
        for r, m in zip(runs, mappings)
    )
    canonical_count = baseline.cluster_count
    survival_rates = [
        c.survivors / canonical_count for c in chars
    ]
    split_rates = [
        c.split_count / canonical_count for c in chars
    ]
    merge_rates = [
        c.merge_count / max(1, c.cluster_count)
        for c in chars
    ]
    novel_totals = sum(c.novel_count for c in chars)
    perturb_totals = sum(c.cluster_count for c in chars)
    largest_var = _variance(
        [c.largest_fraction for c in chars]
    )
    entropy_var = _variance(
        [c.entropy for c in chars]
    )
    label_overlap = _round(
        sum(c.label_overlap for c in chars) / len(chars)
    )
    cross_agree = _cross_run_agreement(
        runs, mappings, baseline,
    )
    dom_rank_stable = _round(
        sum(1 for c in chars if c.dominant_rank == 1)
        / len(chars)
    )
    # dominant cluster size variance: fraction of run mapped
    # back to dominant target.
    dom_fractions: list[float] = []
    for run, mp in zip(runs, mappings):
        total = sum(t.size for t in run.taxonomy)
        if total == 0:
            continue
        dom_share = 0
        for entry in run.taxonomy:
            mp_entry = next(
                (m for m in mp.mappings
                 if m.perturb_cluster_name == entry.taxonomy_name),
                None,
            )
            if (
                mp_entry is not None
                and mp_entry.canonical_target == dominant_name
            ):
                dom_share += entry.size
        dom_fractions.append(dom_share / total)
    dom_size_var = _variance(dom_fractions)

    metrics = StabilityMetrics(
        perturbation_count=len(runs),
        cluster_survival_rate=_round(
            sum(survival_rates) / len(survival_rates)
        ),
        cluster_split_rate=_round(
            sum(split_rates) / len(split_rates)
        ),
        cluster_merge_rate=_round(
            sum(merge_rates) / len(merge_rates)
        ),
        largest_cluster_variance=_round(largest_var),
        taxonomy_entropy_variance=_round(entropy_var),
        label_overlap_score=label_overlap,
        cross_run_agreement=cross_agree,
        dominant_cluster_rank_stability=dom_rank_stable,
        dominant_cluster_size_variance=_round(dom_size_var),
        novel_cluster_fraction=_round(
            novel_totals / perturb_totals
            if perturb_totals else 0.0
        ),
    )
    return metrics, chars


__all__ = [
    "RunCharacterisation", "StabilityMetrics",
    "characterise_run", "compute_stability",
]
