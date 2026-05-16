"""v5.2 — frozen canonical reference."""
from __future__ import annotations

from desi.taxonomy_generalization.canonical import (
    load_canonical_reference,
)


def test_canonical_classes_size_is_eight() -> None:
    assert len(load_canonical_reference().classes) == 8


def test_canonical_classes_all_mt_prefix() -> None:
    for c in load_canonical_reference().classes:
        assert c.name.startswith("MT_"), c.name


def test_canonical_centroids_length_eighteen() -> None:
    for c in load_canonical_reference().classes:
        assert len(c.centroid) == 18


def test_canonical_dominant_is_ambiguity_decisiveness() -> None:
    ref = load_canonical_reference()
    assert ref.dominant_name == "MT_AMBIGUITY_DECISIVENESS"


def test_largest_cluster_fraction_unchanged() -> None:
    ref = load_canonical_reference()
    assert ref.largest_cluster_fraction == 0.563584


def test_class_names_are_exact_v50_set() -> None:
    expected = {
        "MT_AMBIGUITY_DECISIVENESS",
        "MT_AUDIT_OVER_BLOCK",
        "MT_AUDIT_OVER_SUPPORT",
        "MT_MODAL_ASYMMETRY",
        "MT_NEGATION_ASYMMETRY",
        "MT_NOVEL_ENTITY",
        "MT_OVERLAP_LOOP",
        "MT_UNIVERSAL_LEAP",
    }
    assert set(
        load_canonical_reference().class_names
    ) == expected


def test_canonical_reference_loads_v51_stability_matrix() -> None:
    """Aufgabe 3 freeze: v5.2 must read v5.1's matrix
    artifact."""
    ref = load_canonical_reference()
    assert ref.stability_presence
    for name in ref.class_names:
        assert name in ref.stability_presence
