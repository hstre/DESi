"""v3.83 — cross-corpus doppelganger tests."""
from __future__ import annotations

import json
import pathlib

from desi.cross_corpus.corpus_loader import (
    CorpusKind,
)
from desi.cross_corpus_doppelgaenger.corpus_clustering import (
    corpus_clusters, intra_corpus_classes,
    joint_anchors, joint_clusters,
    per_corpus_summaries,
)
from desi.cross_corpus_doppelgaenger.report import (
    build_cross_corpus_doppelgaenger_artifact,
    build_report,
)
from desi.cross_corpus_doppelgaenger.transfer import (
    class_stability, cross_corpus_classes,
    restricted_classes,
    total_cross_corpus_pairs,
    transfer_accuracy,
)


def test_four_corpora_summarised() -> None:
    summaries = per_corpus_summaries()
    assert len(summaries) == 4
    assert {s.corpus for s in summaries} == {
        k.value for k in CorpusKind
    }


def test_joint_anchor_count_is_eleven() -> None:
    """v23 (6) + v314 (3) + v315 (1) + v316 (1)
    = 11 plateau anchors across the 4 closed
    corpora."""
    assert len(joint_anchors()) == 11


def test_intra_corpus_classes() -> None:
    """v23 splits into 3 clusters, v314 into 2,
    v315 and v316 into 1 each."""
    assert intra_corpus_classes() == (3, 2, 1, 1)


def test_joint_clustering_recovers_three_classes() -> None:
    assert len(joint_clusters()) == 3


def test_joint_clustering_sizes() -> None:
    sizes = sorted(
        (len(c.members) for c in joint_clusters()),
        reverse=True,
    )
    assert sizes == [5, 4, 2]


def test_cross_corpus_classes_is_two() -> None:
    """Class 0 spans 4 corpora; Class 2 spans 2
    corpora; Class 1 stays inside v23."""
    assert cross_corpus_classes() == 2


def test_total_cross_corpus_pairs_is_ten() -> None:
    """Class 0 (5 members across 4 corpora) -> 9
    cross-corpus pairs (10 total - 1 v314-v314).
    Class 2 (2 members in 2 corpora) -> 1 pair.
    Class 1 (all v23) -> 0 pairs."""
    assert total_cross_corpus_pairs() == 10


def test_transfer_accuracy_is_one() -> None:
    """Killerfrage: alle bekannten Cross-Corpus
    Doppelganger werden im Joint-Clustering
    wiedergefunden."""
    assert transfer_accuracy() == 1.0


def test_class_stability_is_one() -> None:
    """Pro-Corpus Cluster sind eine Verfeinerung
    der Joint-Cluster."""
    assert class_stability() == 1.0


def test_restricted_classes_drop_non_closed_corpora() -> None:
    """v317 / v317-h members are not part of the
    closed corpora, so they must not appear in the
    restricted v3.79 classes."""
    for members in restricted_classes():
        for m in members:
            head = m.split(":", 1)[0].split("-", 1)[0]
            assert head in {
                "v23", "v314", "v315", "v316",
            }


def test_v314_anchors_form_two_clusters() -> None:
    """D02 + D05 join (cov 121); C02 stands alone
    (cov 0)."""
    cs = corpus_clusters("v314")
    assert len(cs) == 2
    sizes = sorted(
        (len(c.members) for c in cs),
        reverse=True,
    )
    assert sizes == [2, 1]


def test_single_anchor_corpus_collapses_to_one() -> None:
    for corpus in ("v315", "v316"):
        cs = corpus_clusters(corpus)
        assert len(cs) == 1
        assert len(cs[0].members) == 1


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_detected() -> None:
    assert build_report().recommendation == (
        "CROSS_CORPUS_DOPPELGAENGER_DETECTED"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "CROSS_CORPUS_DOPPELGAENGER_DETECTED",
        "CROSS_CORPUS_DOPPELGAENGER_UNSTABLE",
        "CROSS_CORPUS_HYPOTHESIS_WEAK",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_records_four_corpora() -> None:
    art = build_cross_corpus_doppelgaenger_artifact()
    assert len(art["per_corpus_summaries"]) == 4


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_83" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
