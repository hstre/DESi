"""Aufgabe 9 — 100+ NCs for the stability classifier.

Five closed NC kinds (``NCKind``):

* RANDOM_CLUSTERS     — random per-chain assignment
* PERMUTED_LABELS     — canonical labels cyclically shifted
* BLENDED_CLUSTERS    — two canonical clusters merged
* DUPLICATED_FEATURES — clustering identical to canonical
* COLLAPSED_EMBEDDING — all chains pushed into one cluster

For each NC we build a synthetic clustering result and ask
the stability anomaly classifier to identify which NC kind
it represents. Accuracy = fraction correctly classified.

The classifier uses surface signals only:
``cluster_count``, ``label_overlap``, ``merge_count``,
``survivors``. No manual lookup.
"""
from __future__ import annotations

from dataclasses import dataclass

from .baseline import (
    CanonicalBaseline, load_canonical_baseline,
)
from .enums import NCKind


# ---------------------------------------------------------------------------
# Deterministic pseudo-random
# ---------------------------------------------------------------------------


def _lcg(seed: int):
    state = [seed & 0xFFFFFFFF]
    def step() -> int:
        state[0] = (
            (state[0] * 1103515245 + 12345) & 0x7FFFFFFF
        )
        return state[0]
    return step


# ---------------------------------------------------------------------------
# NC fixture
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StabilityNC:
    nc_id: str
    kind: str  # NCKind value
    description: str
    # cluster_assignments: list of (cluster_name, [chain_ids])
    clusters: tuple[tuple[str, tuple[str, ...]], ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "nc_id": self.nc_id,
            "kind": self.kind,
            "description": self.description,
            "clusters": [
                {"name": n, "size": len(ids)}
                for n, ids in self.clusters
            ],
        }


# ---------------------------------------------------------------------------
# Synthetic-clustering generators
# ---------------------------------------------------------------------------


def _make_collapsed(
    baseline: CanonicalBaseline, idx: int,
) -> StabilityNC:
    all_ids: list[str] = []
    for c in baseline.clusters:
        all_ids.extend(c.member_ids)
    return StabilityNC(
        nc_id=f"NC-CO-{idx:03d}",
        kind=NCKind.COLLAPSED_EMBEDDING.value,
        description=(
            "all chains collapsed into one cluster"
        ),
        clusters=(("MT_COLLAPSED", tuple(all_ids)),),
    )


def _make_duplicated(
    baseline: CanonicalBaseline, idx: int,
) -> StabilityNC:
    return StabilityNC(
        nc_id=f"NC-DU-{idx:03d}",
        kind=NCKind.DUPLICATED_FEATURES.value,
        description="clustering identical to canonical",
        clusters=tuple(
            (c.name, c.member_ids) for c in baseline.clusters
        ),
    )


def _make_blended(
    baseline: CanonicalBaseline, idx: int, pair_offset: int,
) -> StabilityNC:
    cs = list(baseline.clusters)
    i = pair_offset % (len(cs) - 1)
    a, b = cs[i], cs[i + 1]
    blended_members = a.member_ids + b.member_ids
    others = [
        (c.name, c.member_ids)
        for c in cs if c.name not in (a.name, b.name)
    ]
    return StabilityNC(
        nc_id=f"NC-BL-{idx:03d}",
        kind=NCKind.BLENDED_CLUSTERS.value,
        description=f"merge {a.name} + {b.name}",
        clusters=tuple(
            others + [
                (f"MT_BLEND_{i}", blended_members),
            ],
        ),
    )


def _make_random(
    baseline: CanonicalBaseline, idx: int, seed: int,
) -> StabilityNC:
    rng = _lcg(seed)
    all_ids: list[str] = []
    for c in baseline.clusters:
        all_ids.extend(c.member_ids)
    n_clusters = baseline.cluster_count
    buckets: list[list[str]] = [
        [] for _ in range(n_clusters)
    ]
    for cid in all_ids:
        buckets[rng() % n_clusters].append(cid)
    return StabilityNC(
        nc_id=f"NC-RA-{idx:03d}",
        kind=NCKind.RANDOM_CLUSTERS.value,
        description=f"random assignment (seed={seed})",
        clusters=tuple(
            (f"MT_RAND_{i}", tuple(ms))
            for i, ms in enumerate(buckets)
        ),
    )


def _make_permuted(
    baseline: CanonicalBaseline, idx: int, shift: int,
) -> StabilityNC:
    cs = list(baseline.clusters)
    n = len(cs)
    out: list[tuple[str, tuple[str, ...]]] = []
    for i, c in enumerate(cs):
        new_name = cs[(i + shift) % n].name
        out.append((new_name, c.member_ids))
    return StabilityNC(
        nc_id=f"NC-PE-{idx:03d}",
        kind=NCKind.PERMUTED_LABELS.value,
        description=f"labels cyclically shifted by {shift}",
        clusters=tuple(out),
    )


def all_stability_ncs() -> tuple[StabilityNC, ...]:
    base = load_canonical_baseline()
    out: list[StabilityNC] = []
    # 20 each = 100 total
    for i in range(1, 21):
        out.append(_make_collapsed(base, i))
    for i in range(1, 21):
        out.append(_make_duplicated(base, i))
    for i in range(1, 21):
        out.append(_make_blended(base, i, pair_offset=i))
    for i in range(1, 21):
        out.append(_make_random(base, i, seed=1000 + i))
    for i in range(1, 21):
        # shift in [1, 7] so permutation is never identity
        shift = ((i - 1) % 7) + 1
        out.append(_make_permuted(base, i, shift=shift))
    return tuple(out)


# ---------------------------------------------------------------------------
# Stability anomaly classifier
# ---------------------------------------------------------------------------


def _label_overlap(
    clusters: tuple[tuple[str, tuple[str, ...]], ...],
    baseline: CanonicalBaseline,
) -> float:
    """Same-cluster agreement vs canonical."""
    canonical_names = {c.name for c in baseline.clusters}
    num = 0
    den = 0
    for name, members in clusters:
        is_canonical_name = name in canonical_names
        for cid in members:
            canonical = baseline.member_to_cluster.get(cid)
            if canonical is None:
                continue
            den += 1
            if is_canonical_name and name == canonical:
                num += 1
    return num / den if den else 0.0


def _merge_count(
    clusters: tuple[tuple[str, tuple[str, ...]], ...],
    baseline: CanonicalBaseline,
) -> int:
    out = 0
    for _name, members in clusters:
        labels: set[str] = set()
        for cid in members:
            c = baseline.member_to_cluster.get(cid)
            if c is not None:
                labels.add(c)
        if len(labels) >= 2:
            out += 1
    return out


def _survivors(
    clusters: tuple[tuple[str, tuple[str, ...]], ...],
    baseline: CanonicalBaseline,
) -> int:
    canonical_names = {c.name for c in baseline.clusters}
    hit: set[str] = set()
    for name, _ in clusters:
        if name in canonical_names:
            hit.add(name)
    return len(hit)


def classify_nc(
    nc: StabilityNC,
    baseline: CanonicalBaseline | None = None,
) -> str:
    """Anomaly-kind classifier — closed cascade on surface
    signals only."""
    base = baseline if baseline is not None else (
        load_canonical_baseline()
    )
    n_clusters = len(nc.clusters)
    overlap = _label_overlap(nc.clusters, base)
    merge = _merge_count(nc.clusters, base)
    surv = _survivors(nc.clusters, base)

    # 1) Single bucket -> COLLAPSED_EMBEDDING
    if n_clusters <= 1:
        return NCKind.COLLAPSED_EMBEDDING.value
    # 2) Perfect-name overlap -> DUPLICATED_FEATURES
    if overlap >= 0.999 and surv == base.cluster_count:
        return NCKind.DUPLICATED_FEATURES.value
    # 3) Most buckets mix multiple canonicals -> RANDOM.
    #    Random assignment yields high merge_fraction
    #    (typically ~1.0); blending two canonical classes
    #    yields exactly one mixed bucket among many pure
    #    ones (merge_fraction <= ~1/7).
    merge_fraction = merge / n_clusters
    if merge_fraction > 0.50:
        return NCKind.RANDOM_CLUSTERS.value
    # 4) Exactly one mixed bucket among otherwise pure
    #    canonical-aligned ones -> BLENDED.
    if merge >= 1:
        return NCKind.BLENDED_CLUSTERS.value
    # 5) All canonical names present but content mismatched
    #    -> PERMUTED_LABELS (cycle relabel preserves names
    #    but reassigns chains).
    if surv == base.cluster_count and overlap < 0.50:
        return NCKind.PERMUTED_LABELS.value
    return NCKind.RANDOM_CLUSTERS.value


def classification_accuracy() -> float:
    ncs = all_stability_ncs()
    base = load_canonical_baseline()
    correct = sum(
        1 for nc in ncs if classify_nc(nc, base) == nc.kind
    )
    return round(correct / len(ncs), 6)


__all__ = [
    "StabilityNC", "all_stability_ncs",
    "classification_accuracy", "classify_nc",
]
