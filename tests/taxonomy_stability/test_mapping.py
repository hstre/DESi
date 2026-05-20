"""v5.1 — best-overlap cluster mapping."""
from __future__ import annotations

from desi.taxonomy_stability.baseline import (
    load_canonical_baseline,
)
from desi.taxonomy_stability.cluster_mapper import (
    build_cluster_mapping_matrix, map_run_to_canonical,
)
from desi.taxonomy_stability.perturbations import (
    all_perturbation_runs,
)


def test_mapping_total_or_novel_for_every_perturb_cluster() -> None:
    b = load_canonical_baseline()
    for r in all_perturbation_runs():
        m = map_run_to_canonical(r, b)
        assert len(m.mappings) == r.cluster_count


def test_mapping_overlap_count_nonnegative() -> None:
    b = load_canonical_baseline()
    for r in all_perturbation_runs():
        m = map_run_to_canonical(r, b)
        for pm in m.mappings:
            assert pm.overlap_count >= 0
            assert pm.overlap_count <= pm.perturb_size


def test_mapping_novel_iff_zero_overlap() -> None:
    b = load_canonical_baseline()
    for r in all_perturbation_runs():
        m = map_run_to_canonical(r, b)
        for pm in m.mappings:
            assert pm.is_novel == (pm.overlap_count == 0)


def test_mapping_target_in_baseline_or_none() -> None:
    b = load_canonical_baseline()
    canonical_names = {c.name for c in b.clusters}
    for r in all_perturbation_runs():
        m = map_run_to_canonical(r, b)
        for pm in m.mappings:
            assert (
                pm.canonical_target is None
                or pm.canonical_target in canonical_names
            )


def test_cluster_mapping_matrix_covers_all_canonical() -> None:
    matrix = build_cluster_mapping_matrix(
        all_perturbation_runs(), load_canonical_baseline(),
    )
    cells = matrix["canonical_presence_matrix"]
    expected = {
        c.name for c in load_canonical_baseline().clusters
    }
    assert set(cells.keys()) == expected


def test_dominant_cluster_appears_in_every_run() -> None:
    """MT_AMBIGUITY_DECISIVENESS must survive every run."""
    matrix = build_cluster_mapping_matrix(
        all_perturbation_runs(), load_canonical_baseline(),
    )
    cells = matrix["canonical_presence_matrix"]
    dom = cells["MT_AMBIGUITY_DECISIVENESS"]
    assert all(v for v in dom.values())
