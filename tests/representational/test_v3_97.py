"""v3.97 - semantic loss audit tests."""
from __future__ import annotations

import json
import pathlib

from desi.representational.divergence import (
    ConceptKind,
    all_concept_assignments,
    classify_text,
    concept_distribution_by_family,
    concept_divergence,
    dominant_concept_per_family,
)
from desi.representational.report import (
    SEMANTIC_DISTANCE_THRESHOLD,
    build_report,
    build_semantic_loss_audit_artifact,
)
from desi.representational.semantic_loss import (
    ENTANGLED_FAMILY_IDS,
    family_token_stats,
    family_uniqueness,
    jaccard_bigrams, jaccard_unigrams,
    semantic_distance, semantic_overlap,
)


def test_entangled_family_ids_are_g_and_e() -> None:
    assert ENTANGLED_FAMILY_IDS == (
        "G_v316susp", "E_v317h",
    )


def test_classify_circular_pattern() -> None:
    text = (
        "The argument rests on the lemma. "
        "The lemma rests on the argument. "
        "Therefore the conclusion stands firm."
    )
    assert classify_text(text) == (
        ConceptKind.CIRCULAR_REASONING.value
    )


def test_classify_universal_syllogism() -> None:
    text = (
        "All crowing roosters precede sunrise. "
        "A rooster crowed. "
        "Therefore the rooster caused dawn."
    )
    assert classify_text(text) == (
        ConceptKind.UNIVERSAL_SYLLOGISM.value
    )


def test_classify_post_hoc_narrative() -> None:
    text = (
        "The kitten purred contentedly. "
        "The kitten napped in sunshine. "
        "Therefore the kitten enjoyed an afternoon."
    )
    assert classify_text(text) == (
        ConceptKind.POST_HOC_NARRATIVE.value
    )


def test_classify_unclassified_without_therefore() -> None:
    """Sentences without 'Therefore' fall through
    every classifier branch."""
    text = "The kitten purred. The kitten napped."
    assert classify_text(text) == (
        ConceptKind.UNCLASSIFIED.value
    )


def test_concept_assignments_cover_all_nineteen() -> None:
    assert len(all_concept_assignments()) == 19


def test_g_family_all_circular() -> None:
    dist = concept_distribution_by_family()
    g = dist["G_v316susp"]
    assert g[ConceptKind.CIRCULAR_REASONING.value] == 9
    assert sum(g.values()) == 9


def test_e_family_no_circular() -> None:
    dist = concept_distribution_by_family()
    e = dist["E_v317h"]
    assert e[ConceptKind.CIRCULAR_REASONING.value] == 0
    assert sum(e.values()) == 10


def test_dominant_concept_per_family() -> None:
    """Killerfrage: sind sie wirklich semantisch
    verschieden? Yes - each family has a
    different dominant concept."""
    dom = dominant_concept_per_family()
    assert dom["G_v316susp"] == (
        ConceptKind.CIRCULAR_REASONING.value
    )
    assert dom["E_v317h"] != (
        ConceptKind.CIRCULAR_REASONING.value
    )


def test_concept_divergence_is_one() -> None:
    """Total-variation distance between concept
    distributions is maximal."""
    assert concept_divergence() == 1.0


def test_jaccard_unigrams_low() -> None:
    """Vocabulary overlap is small."""
    assert jaccard_unigrams() < 0.10


def test_jaccard_bigrams_lower_than_unigrams() -> None:
    assert jaccard_bigrams() <= jaccard_unigrams()


def test_semantic_distance_above_threshold() -> None:
    """Concept Gate condition #1:
    semantic_distance > 0; threshold 0.50."""
    assert (
        semantic_distance()
        > SEMANTIC_DISTANCE_THRESHOLD
    )


def test_semantic_overlap_is_complement_of_distance() -> None:
    s = semantic_distance() + semantic_overlap()
    assert abs(s - 1.0) < 1e-3


def test_family_uniqueness_above_ninety_percent() -> None:
    """Both families have > 90% unique-to-family
    vocabulary."""
    fu = family_uniqueness()
    for fid in ENTANGLED_FAMILY_IDS:
        assert fu[fid] > 0.90


def test_family_token_stats_count() -> None:
    stats = family_token_stats()
    assert len(stats) == 2
    by_fid = {s.family_id: s for s in stats}
    assert by_fid["G_v316susp"].member_count == 9
    assert by_fid["E_v317h"].member_count == 10


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_distinct() -> None:
    assert build_report().recommendation == (
        "FAMILIES_SEMANTICALLY_DISTINCT"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "FAMILIES_SEMANTICALLY_DISTINCT",
        "VOCABULARY_DISTINCT_CONCEPT_SHARED",
        "CONCEPT_DISTINCT_VOCABULARY_SHARED",
        "FAMILIES_SEMANTICALLY_SIMILAR",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_has_all_concept_assignments() -> None:
    art = build_semantic_loss_audit_artifact()
    assert len(art["concept_assignments"]) == 19


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_97" / "report.json").read_text(
            encoding="utf-8",
        )
    )
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
