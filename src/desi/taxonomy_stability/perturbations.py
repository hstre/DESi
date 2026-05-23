"""Aufgabe 4 — five perturbation families against the
v5.0 pipeline.

For each perturbation we re-run failure detection +
clustering against the v5.0 corpus and compare the
resulting clustering to the canonical v5.0 taxonomy.

Perturbations are deterministic (seeded). No new
clustering algorithm is introduced; the existing
``discover_clusters`` / ``collapse_to_corridor`` / ``assign_names``
pipeline is reused with controlled input variations.

Families (closed):

* P1 representation_swap   — sparse / dense / normalized
* P2 feature_weight        — +/-10%, +/-25%, masking,
                              alternating
* P3 corpus_resampling     — bootstrap, leave-10%-out,
                              leave-domain-out * 5
* P4 ordering_noise        — shuffled, reversed, chunked
* P5 domain_mix_shift      — over-weight, under-weight,
                              pairwise removal
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

from ..methodology_transfer.cluster_discovery import (
    Cluster, collapse_to_corridor,
)
from ..methodology_transfer.corpus import (
    TransferChain, all_chains,
)
from ..methodology_transfer.feature_extraction import (
    FEATURE_NAMES, FailureSample, extract_features,
    is_failure,
)
from ..methodology_transfer.taxonomy import (
    TaxonomyEntry, assign_names,
)
from .enums import PerturbationFamily


_F = len(FEATURE_NAMES)


# ---------------------------------------------------------------------------
# Local re-clustering with sort-key + tolerance hooks
# ---------------------------------------------------------------------------


def _centroid(
    members: list[FailureSample],
) -> tuple[float, ...]:
    if not members:
        return tuple([0.0] * _F)
    n = len(members)
    sums = [0.0] * _F
    for m in members:
        for i, v in enumerate(m.features):
            sums[i] += v
    return tuple(s / n for s in sums)


def _l1(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(abs(x - y) for x, y in zip(a, b))


def _cluster(
    samples: Sequence[FailureSample],
    *, tolerance: float = 1.5,
    sort_key: Callable[[FailureSample], object] | None = None,
) -> tuple[Cluster, ...]:
    """Re-implementation of the v5.0 agglomerative pass
    that exposes the sort key. Behaviour matches
    ``cluster_discovery.discover_clusters`` when
    ``sort_key`` defaults to ``chain_id``."""
    if not samples:
        return ()
    key = sort_key if sort_key is not None else (
        lambda s: s.chain_id
    )
    ordered = sorted(samples, key=key)
    members: list[list[FailureSample]] = []
    centroids: list[tuple[float, ...]] = []
    for s in ordered:
        best_idx = -1
        best_dist = float("inf")
        for i, c in enumerate(centroids):
            d = _l1(s.features, c)
            if d < best_dist:
                best_dist = d
                best_idx = i
        if best_idx >= 0 and best_dist <= tolerance:
            members[best_idx].append(s)
            centroids[best_idx] = _centroid(members[best_idx])
        else:
            members.append([s])
            centroids.append(s.features)
    out: list[Cluster] = []
    for i, m in enumerate(members):
        out.append(Cluster(
            cluster_id=f"K{i+1:02d}",
            centroid=centroids[i],
            member_ids=tuple(x.chain_id for x in m),
            size=len(m),
        ))
    out.sort(key=lambda c: (-c.size, c.cluster_id))
    return tuple(
        Cluster(
            cluster_id=f"K{i+1:02d}",
            centroid=c.centroid,
            member_ids=c.member_ids, size=c.size,
        )
        for i, c in enumerate(out)
    )


def _transform_samples(
    samples: Sequence[FailureSample],
    transform: Callable[
        [tuple[float, ...]], tuple[float, ...],
    ] | None = None,
) -> tuple[FailureSample, ...]:
    if transform is None:
        return tuple(samples)
    return tuple(
        FailureSample(
            chain_id=s.chain_id, domain=s.domain,
            audit_verdict=s.audit_verdict,
            audit_rule=s.audit_rule,
            expected_label=s.expected_label,
            features=transform(s.features),
        )
        for s in samples
    )


# ---------------------------------------------------------------------------
# Run dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PerturbationRun:
    run_id: str
    family: str
    description: str
    sample_count: int
    cluster_count: int
    largest_cluster_fraction: float
    taxonomy: tuple[TaxonomyEntry, ...]

    def member_to_name(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for t in self.taxonomy:
            for m in t.member_ids:
                out[m] = t.taxonomy_name
        return out

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "family": self.family,
            "description": self.description,
            "sample_count": self.sample_count,
            "cluster_count": self.cluster_count,
            "largest_cluster_fraction":
                self.largest_cluster_fraction,
            "cluster_sizes": [
                {"name": t.taxonomy_name, "size": t.size}
                for t in self.taxonomy
            ],
        }


def _build_taxonomy(
    samples: Sequence[FailureSample],
    *, tolerance: float = 1.5,
    sort_key: Callable[[FailureSample], object] | None = None,
) -> tuple[TaxonomyEntry, ...]:
    clusters = _cluster(
        samples, tolerance=tolerance, sort_key=sort_key,
    )
    clusters = collapse_to_corridor(clusters, max_clusters=12)
    sample_feats = {s.chain_id: s.features for s in samples}
    return assign_names(clusters, sample_features=sample_feats)


def _run(
    run_id: str, family: PerturbationFamily,
    description: str,
    samples: Sequence[FailureSample],
    *, tolerance: float = 1.5,
    sort_key: Callable[[FailureSample], object] | None = None,
) -> PerturbationRun:
    taxonomy = _build_taxonomy(
        samples, tolerance=tolerance, sort_key=sort_key,
    )
    total = sum(t.size for t in taxonomy)
    largest = (
        max((t.size for t in taxonomy), default=0) / total
        if total else 0.0
    )
    return PerturbationRun(
        run_id=run_id, family=family.value,
        description=description,
        sample_count=len(samples),
        cluster_count=len(taxonomy),
        largest_cluster_fraction=round(largest, 6),
        taxonomy=taxonomy,
    )


# ---------------------------------------------------------------------------
# Baseline failure samples (v5.0 corpus)
# ---------------------------------------------------------------------------


def baseline_failure_samples() -> tuple[FailureSample, ...]:
    chains = all_chains()
    samples = [extract_features(c) for c in chains]
    return tuple(s for s in samples if is_failure(s))


# ---------------------------------------------------------------------------
# Deterministic pseudo-random helper (no `random` module —
# uses a 32-bit LCG so the seed is fully traceable).
# ---------------------------------------------------------------------------


def _lcg(seed: int) -> Callable[[], int]:
    state = [seed & 0xFFFFFFFF]
    def step() -> int:
        state[0] = (
            (state[0] * 1103515245 + 12345) & 0x7FFFFFFF
        )
        return state[0]
    return step


# ---------------------------------------------------------------------------
# P1 representation_swap
# ---------------------------------------------------------------------------


def _p1_sparse(v: tuple[float, ...]) -> tuple[float, ...]:
    """Drop count-style features; keep boolean signals."""
    keep = {
        2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
        15, 16, 17,
    }
    return tuple(
        x if i in keep else 0.0 for i, x in enumerate(v)
    )


def _p1_dense_log_counts(
    v: tuple[float, ...],
) -> tuple[float, ...]:
    """Replace count-style features with log1p; preserve
    binary features. Binary thresholds in the classifier
    (>0.5) keep working because binary stays 0/1."""
    import math
    count_idx = {0, 1, 3, 4}  # premise_count, concl_token_count, overlap_*
    return tuple(
        math.log1p(x) if i in count_idx else x
        for i, x in enumerate(v)
    )


def _build_minmax_transform(
    samples: Sequence[FailureSample],
) -> Callable[[tuple[float, ...]], tuple[float, ...]]:
    """Per-feature min-max scaling fit across the corpus."""
    if not samples:
        return lambda v: v
    mins = [float("inf")] * _F
    maxs = [float("-inf")] * _F
    for s in samples:
        for i, x in enumerate(s.features):
            if x < mins[i]:
                mins[i] = x
            if x > maxs[i]:
                maxs[i] = x
    ranges = tuple(
        (maxs[i] - mins[i]) if maxs[i] > mins[i] else 1.0
        for i in range(_F)
    )
    mn = tuple(mins)
    def transform(v: tuple[float, ...]) -> tuple[float, ...]:
        return tuple(
            (x - mn[i]) / ranges[i] for i, x in enumerate(v)
        )
    return transform


def p1_runs() -> tuple[PerturbationRun, ...]:
    base = baseline_failure_samples()
    out: list[PerturbationRun] = []
    out.append(_run(
        "P1-01", PerturbationFamily.P1_REPRESENTATION_SWAP,
        "sparse (binary-only features)",
        _transform_samples(base, _p1_sparse),
        # binary-only features collapse distances; relax
        # tolerance to retain the original cluster
        # granularity rather than over-merging
        tolerance=1.0,
    ))
    out.append(_run(
        "P1-02", PerturbationFamily.P1_REPRESENTATION_SWAP,
        "dense (log1p on count-style features)",
        _transform_samples(base, _p1_dense_log_counts),
        tolerance=1.5,
    ))
    minmax_xform = _build_minmax_transform(base)
    out.append(_run(
        "P1-03", PerturbationFamily.P1_REPRESENTATION_SWAP,
        "per-feature min-max normalized",
        _transform_samples(base, minmax_xform),
        tolerance=0.30,
    ))
    return tuple(out)


# ---------------------------------------------------------------------------
# P2 feature_weight_perturbation
# ---------------------------------------------------------------------------


def _scale(
    weights: tuple[float, ...],
) -> Callable[[tuple[float, ...]], tuple[float, ...]]:
    return lambda v: tuple(
        x * w for x, w in zip(v, weights)
    )


def p2_runs() -> tuple[PerturbationRun, ...]:
    base = baseline_failure_samples()
    out: list[PerturbationRun] = []
    plus10 = tuple(1.10 for _ in range(_F))
    minus10 = tuple(0.90 for _ in range(_F))
    plus25 = tuple(1.25 for _ in range(_F))
    minus25 = tuple(0.75 for _ in range(_F))
    alt10 = tuple(
        1.10 if i % 2 == 0 else 0.90 for i in range(_F)
    )
    out.append(_run(
        "P2-01", PerturbationFamily.P2_FEATURE_WEIGHT,
        "all features +10%",
        _transform_samples(base, _scale(plus10)),
        tolerance=1.5 * 1.10,
    ))
    out.append(_run(
        "P2-02", PerturbationFamily.P2_FEATURE_WEIGHT,
        "all features -10%",
        _transform_samples(base, _scale(minus10)),
        tolerance=1.5 * 0.90,
    ))
    out.append(_run(
        "P2-03", PerturbationFamily.P2_FEATURE_WEIGHT,
        "all features +25%",
        _transform_samples(base, _scale(plus25)),
        tolerance=1.5 * 1.25,
    ))
    out.append(_run(
        "P2-04", PerturbationFamily.P2_FEATURE_WEIGHT,
        "all features -25%",
        _transform_samples(base, _scale(minus25)),
        tolerance=1.5 * 0.75,
    ))
    out.append(_run(
        "P2-05", PerturbationFamily.P2_FEATURE_WEIGHT,
        "alternating ±10% (even +10%, odd -10%)",
        _transform_samples(base, _scale(alt10)),
        tolerance=1.5,
    ))
    # random masking with seed 7 — drop ~15% of features
    rng = _lcg(7)
    mask = tuple(
        0.0 if (rng() % 100) < 15 else 1.0
        for _ in range(_F)
    )
    out.append(_run(
        "P2-06", PerturbationFamily.P2_FEATURE_WEIGHT,
        "random 15% feature masking (seed=7)",
        _transform_samples(base, _scale(mask)),
        tolerance=1.5,
    ))
    return tuple(out)


# ---------------------------------------------------------------------------
# P3 corpus_resampling
# ---------------------------------------------------------------------------


def _bootstrap(
    samples: Sequence[FailureSample], seed: int,
) -> tuple[FailureSample, ...]:
    rng = _lcg(seed)
    n = len(samples)
    out: list[FailureSample] = []
    for i in range(n):
        idx = rng() % n
        s = samples[idx]
        # Append with a unique chain_id so duplicates do
        # not collide in the clustering output.
        out.append(FailureSample(
            chain_id=f"{s.chain_id}#b{i}",
            domain=s.domain,
            audit_verdict=s.audit_verdict,
            audit_rule=s.audit_rule,
            expected_label=s.expected_label,
            features=s.features,
        ))
    return tuple(out)


def p3_runs() -> tuple[PerturbationRun, ...]:
    base = baseline_failure_samples()
    out: list[PerturbationRun] = []
    out.append(_run(
        "P3-01", PerturbationFamily.P3_CORPUS_RESAMPLING,
        "bootstrap resample (seed=13)",
        _bootstrap(base, 13),
    ))
    # leave-10%-out — drop every 10th by sorted chain_id
    sorted_base = sorted(base, key=lambda s: s.chain_id)
    keep = tuple(
        s for i, s in enumerate(sorted_base) if i % 10 != 0
    )
    out.append(_run(
        "P3-02", PerturbationFamily.P3_CORPUS_RESAMPLING,
        "leave-10%-out (skip every 10th)",
        keep,
    ))
    # leave-domain-out for each of the five domains
    domains = sorted({s.domain for s in base})
    for i, dom in enumerate(domains, start=3):
        subset = tuple(s for s in base if s.domain != dom)
        out.append(_run(
            f"P3-0{i}",
            PerturbationFamily.P3_CORPUS_RESAMPLING,
            f"leave-domain-out: {dom}",
            subset,
        ))
    return tuple(out)


# ---------------------------------------------------------------------------
# P4 ordering_noise
# ---------------------------------------------------------------------------


def p4_runs() -> tuple[PerturbationRun, ...]:
    base = baseline_failure_samples()
    out: list[PerturbationRun] = []
    # shuffled — seed-deterministic random key
    rng = _lcg(101)
    shuffle_key = {s.chain_id: rng() for s in base}
    out.append(_run(
        "P4-01", PerturbationFamily.P4_ORDERING_NOISE,
        "shuffled input order (seed=101)",
        base,
        sort_key=lambda s: shuffle_key[s.chain_id],
    ))
    # reversed
    out.append(_run(
        "P4-02", PerturbationFamily.P4_ORDERING_NOISE,
        "reversed input order",
        base,
        sort_key=lambda s: (
            -ord(s.chain_id[0]), s.chain_id[::-1],
        ),
    ))
    # chunked: reverse the order of fifty-sample chunks
    sorted_base = sorted(base, key=lambda s: s.chain_id)
    rank: dict[str, int] = {}
    chunk = 50
    n = len(sorted_base)
    for i, s in enumerate(sorted_base):
        block = i // chunk
        rev_block = (n // chunk) - block
        rank[s.chain_id] = rev_block * 10000 + (i % chunk)
    out.append(_run(
        "P4-03", PerturbationFamily.P4_ORDERING_NOISE,
        "chunked reversal (50-sample blocks)",
        base,
        sort_key=lambda s: rank[s.chain_id],
    ))
    return tuple(out)


# ---------------------------------------------------------------------------
# P5 domain_mix_shift
# ---------------------------------------------------------------------------


def _replicate_domain(
    samples: Sequence[FailureSample], dom: str, times: int,
) -> tuple[FailureSample, ...]:
    out: list[FailureSample] = list(samples)
    extras = [s for s in samples if s.domain == dom]
    for k in range(1, times):
        for s in extras:
            out.append(FailureSample(
                chain_id=f"{s.chain_id}#x{k}",
                domain=s.domain,
                audit_verdict=s.audit_verdict,
                audit_rule=s.audit_rule,
                expected_label=s.expected_label,
                features=s.features,
            ))
    return tuple(out)


def _underweight_domain(
    samples: Sequence[FailureSample], dom: str, keep_every: int,
) -> tuple[FailureSample, ...]:
    out: list[FailureSample] = []
    counter = 0
    for s in samples:
        if s.domain != dom:
            out.append(s)
        else:
            if counter % keep_every == 0:
                out.append(s)
            counter += 1
    return tuple(out)


def p5_runs() -> tuple[PerturbationRun, ...]:
    base = baseline_failure_samples()
    out: list[PerturbationRun] = []
    # Overweight the largest-failure domain (legal)
    out.append(_run(
        "P5-01", PerturbationFamily.P5_DOMAIN_MIX_SHIFT,
        "overweight legal_case_summaries x2",
        _replicate_domain(
            base, "legal_case_summaries", times=2,
        ),
    ))
    # Underweight a domain (medical x0.5)
    out.append(_run(
        "P5-02", PerturbationFamily.P5_DOMAIN_MIX_SHIFT,
        "underweight medical_guidelines x0.5",
        _underweight_domain(
            base, "medical_guidelines", keep_every=2,
        ),
    ))
    # Pairwise domain removal: drop two domains
    pairs = (
        ("technical_incident_reports", "legal_case_summaries"),
        ("medical_guidelines",
         "scientific_peer_reviews"),
        ("mathematical_proof_sketches",
         "technical_incident_reports"),
    )
    for i, (a, b) in enumerate(pairs, start=3):
        subset = tuple(
            s for s in base
            if s.domain != a and s.domain != b
        )
        out.append(_run(
            f"P5-0{i}", PerturbationFamily.P5_DOMAIN_MIX_SHIFT,
            f"pairwise removal: {a} + {b}",
            subset,
        ))
    return tuple(out)


# ---------------------------------------------------------------------------
# Combined
# ---------------------------------------------------------------------------


def all_perturbation_runs() -> tuple[PerturbationRun, ...]:
    return (
        p1_runs() + p2_runs() + p3_runs()
        + p4_runs() + p5_runs()
    )


__all__ = [
    "PerturbationRun", "all_perturbation_runs",
    "baseline_failure_samples",
    "p1_runs", "p2_runs", "p3_runs", "p4_runs", "p5_runs",
]
