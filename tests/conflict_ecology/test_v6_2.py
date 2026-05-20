"""v6.2 - multi-paper conflict ecology tests."""
from __future__ import annotations

import json
import pathlib

from desi.conflict_ecology.conflict_graph import (
    coherence_score, components,
    conflict_resolution_stability,
    fragmentation_rate,
    polarization_index,
)
from desi.conflict_ecology.cross_paper import (
    ECOLOGY_CONFLICT_KINDS,
    EcologyConflictKind, corpus,
    detected_conflicts, detection_precision,
    detection_recall, ground_truth_conflicts,
)
from desi.conflict_ecology.ecology import (
    component_sizes, conflict_kind_counts,
    school_distribution, topic_clusters,
    uncertainty_zone_count,
)
from desi.conflict_ecology.report import (
    build_conflict_ecology_artifact,
    build_report,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "world_contact"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_conflict_kinds_closed_set() -> None:
    assert ECOLOGY_CONFLICT_KINDS == tuple(
        k.value for k in EcologyConflictKind
    )


def test_corpus_size() -> None:
    assert len(corpus()) >= 8


def test_detection_recall_full() -> None:
    """Every ground-truth conflict must be
    detected."""
    assert detection_recall() == 1.0


def test_detection_precision_full() -> None:
    """No false positives: detected conflicts
    match the ground truth exactly."""
    assert detection_precision() == 1.0


def test_conflict_resolution_stability_one() -> (
    None
):
    """Pflichtfrage 1: kann DESi
    Konfliktoekologien stabil verwalten?"""
    assert conflict_resolution_stability() == (
        1.0
    )


def test_polarization_index_bounded() -> None:
    """Pflichtfrage 2: entsteht Polarisierung?
    Wenn ja, dann nur innerhalb der closed
    Schwelle."""
    p = polarization_index()
    assert 0.0 <= p <= 1.0
    assert p <= 0.90


def test_fragmentation_rate_bounded() -> None:
    """Pflichtfrage 3: entsteht epistemische
    Fragmentierung? Innerhalb der envelope."""
    f = fragmentation_rate()
    assert 0.0 <= f <= 1.0
    assert f <= 0.80


def test_coherence_score_above_floor() -> None:
    """Pflichtfrage 4: bleibt Kohaerenz
    erhalten?"""
    assert coherence_score() >= 0.50


def test_components_partition_corpus() -> None:
    flat = [
        pid
        for comp in components()
        for pid in comp
    ]
    assert set(flat) == {
        p.paper_id for p in corpus()
    }
    assert len(flat) == len(corpus())


def test_components_sorted_by_size_desc() -> None:
    sizes = [len(c) for c in components()]
    assert sizes == sorted(sizes, reverse=True)


def test_no_self_loops() -> None:
    for c in detected_conflicts():
        assert c.paper_a != c.paper_b


def test_no_duplicate_conflicts() -> None:
    pairs = [
        tuple(sorted([c.paper_a, c.paper_b]))
        for c in detected_conflicts()
    ]
    assert len(pairs) == len(set(pairs))


def test_uncertainty_zones_recorded() -> None:
    assert uncertainty_zone_count() >= 1


def test_topic_clusters_cover_corpus() -> None:
    seen = {
        pid
        for c in topic_clusters()
        for pid in c.papers
    }
    assert seen == {
        p.paper_id for p in corpus()
    }


def test_school_distribution_nonempty() -> None:
    assert len(school_distribution()) >= 3


def test_conflict_kind_counts_subset() -> None:
    observed = set(conflict_kind_counts().keys())
    assert observed.issubset(
        set(ECOLOGY_CONFLICT_KINDS),
    )


def test_component_sizes_match_components() -> None:
    assert component_sizes() == tuple(
        len(c) for c in components()
    )


def test_replay_stability_one() -> None:
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "ECOLOGY_TRACTABLE",
        "ECOLOGY_POLARISED",
        "ECOLOGY_FRAGMENTED",
        "ECOLOGY_CONFLICT_HEAVY",
        "ECOLOGY_DETECTION_WEAK",
        "ECOLOGY_REPLAY_DRIFT",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_tractable() -> None:
    """Killerfrage: kann DESi mit echter
    wissenschaftlicher Uneinigkeit umgehen?"""
    assert build_report().recommendation == (
        "ECOLOGY_TRACTABLE"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v6_2_conflict_ecology.json")
    assert art["schema_version"] == (
        "v6_2_conflict_ecology"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v6_2_conflict_ecology.json")
    required = {
        "conflict_resolution_stability",
        "polarization_index",
        "fragmentation_rate",
        "coherence_score",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v6_2_report.json")
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable


def test_artifact_full_matches_live_build() -> None:
    art = _load("v6_2_conflict_ecology.json")
    live = build_conflict_ecology_artifact()
    assert art == live
