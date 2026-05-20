"""v5.1 — five perturbation families, ≥20 runs total."""
from __future__ import annotations

from collections import Counter

from desi.taxonomy_stability.enums import PerturbationFamily
from desi.taxonomy_stability.perturbations import (
    all_perturbation_runs, baseline_failure_samples,
    p1_runs, p2_runs, p3_runs, p4_runs, p5_runs,
)


def test_total_runs_meets_directive_floor() -> None:
    assert len(all_perturbation_runs()) >= 20


def test_each_perturbation_family_runs_at_least_three() -> None:
    counts = Counter(
        r.family for r in all_perturbation_runs()
    )
    for fam in PerturbationFamily:
        assert counts[fam.value] >= 3, fam.value


def test_all_five_families_represented() -> None:
    families = {r.family for r in all_perturbation_runs()}
    expected = {f.value for f in PerturbationFamily}
    assert families == expected


def test_run_ids_unique() -> None:
    ids = [r.run_id for r in all_perturbation_runs()]
    assert len(set(ids)) == len(ids)


def test_each_run_produces_at_least_three_clusters() -> None:
    for r in all_perturbation_runs():
        assert r.cluster_count >= 3, r.run_id


def test_perturbations_are_deterministic() -> None:
    a = tuple(
        (r.run_id, r.cluster_count, r.largest_cluster_fraction)
        for r in all_perturbation_runs()
    )
    b = tuple(
        (r.run_id, r.cluster_count, r.largest_cluster_fraction)
        for r in all_perturbation_runs()
    )
    assert a == b


def test_each_family_call_returns_at_least_three_runs() -> None:
    assert len(p1_runs()) >= 3
    assert len(p2_runs()) >= 3
    assert len(p3_runs()) >= 3
    assert len(p4_runs()) >= 3
    assert len(p5_runs()) >= 3


def test_baseline_failure_samples_is_346() -> None:
    assert len(baseline_failure_samples()) == 346
