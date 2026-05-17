"""v3.54 — cross-corpus pair resonance tests."""
from __future__ import annotations

import json
import pathlib

from desi.cross_corpus.corpus_loader import (
    corpus_plateau_anchors,
)
from desi.cross_corpus_resonance.matrix import (
    all_corpora_pair_matrices,
    per_corpus_pair_matrix,
)
from desi.cross_corpus_resonance.pair_transfer import (
    MIN_ANCHORS_FOR_PAIRS, PROBE_RADIUS,
    eligible_corpora, ineligible_corpora,
    per_corpus_control_summary,
    per_corpus_plateau_summary, triple_max_extra,
)
from desi.cross_corpus_resonance.report import (
    PAPER11_TRANSFER_FLOOR,
    build_cross_corpus_resonance_artifact,
    build_report,
)


def test_probe_radius_is_three_point_five() -> None:
    """Same probe radius as v3.50."""
    assert PROBE_RADIUS == 3.5


def test_min_anchors_for_pairs_is_two() -> None:
    assert MIN_ANCHORS_FOR_PAIRS == 2


def test_eligible_corpora_match_pair_threshold() -> None:
    """v23 (6 anchors) and v314 (3 anchors) are
    eligible. v315/v316 each have only 1 plateau
    anchor and cannot form a pair."""
    assert eligible_corpora() == ("v23", "v314")


def test_ineligible_corpora_match_pair_threshold() -> None:
    assert ineligible_corpora() == ("v315", "v316")


def test_per_corpus_plateau_summary_v23() -> None:
    s = per_corpus_plateau_summary("v23")
    assert s.cohort == "plateau"
    assert s.anchor_count == 6
    assert s.leakage_count == 12
    assert s.pair_count == 15  # C(6, 2)


def test_per_corpus_plateau_summary_v314() -> None:
    s = per_corpus_plateau_summary("v314")
    assert s.anchor_count == 3
    assert s.leakage_count == 30
    assert s.pair_count == 3  # C(3, 2)


def test_per_corpus_resonant_pairs_are_zero() -> None:
    """Honest empirical finding: per-corpus plateau
    anchors are either coverage-equivalent or one
    is empty, so no pair satisfies the strict
    proper-set-independence definition."""
    for c in eligible_corpora():
        s = per_corpus_plateau_summary(c)
        assert s.resonant_pair_count == 0


def test_per_corpus_subadditivity_nonzero() -> None:
    """Anchors overlap when they cover the same
    leakages; the subadditivity is non-zero even
    though no pair is resonant."""
    for c in eligible_corpora():
        s = per_corpus_plateau_summary(c)
        assert s.subadditivity_score > 0


def test_triple_max_extra_zero_per_corpus() -> None:
    """Empirical: even when 3+ anchors exist, triples
    do not add anything beyond pairs."""
    for c in eligible_corpora():
        assert triple_max_extra(c) == 0


def test_control_summary_per_corpus() -> None:
    for c in eligible_corpora():
        s = per_corpus_control_summary(c)
        assert s.cohort == "control"
        # control gets MIN_ANCHORS_FOR_PAIRS anchors
        # OR the plateau count, whichever is larger
        plats = corpus_plateau_anchors(c)
        assert s.anchor_count >= MIN_ANCHORS_FOR_PAIRS
        assert s.anchor_count <= max(
            MIN_ANCHORS_FOR_PAIRS, len(plats),
        )


def test_per_corpus_pair_matrix_dimensions() -> None:
    for c in eligible_corpora():
        m = per_corpus_pair_matrix(c)
        n = len(corpus_plateau_anchors(c))
        assert len(m) == n
        for row in m.values():
            assert len(row) == n


def test_pair_transfer_rate_is_zero() -> None:
    """Honest finding: 0/2 eligible corpora have
    resonance_pair_count > control_pair_count.
    The v3.50 effect was a cross-corpus aggregate."""
    assert build_report().pair_transfer_rate == 0.0


def test_pair_transfer_rate_below_gate() -> None:
    """Paper-11 v2 gate #2 FAILS empirically."""
    assert build_report().pair_transfer_rate < (
        PAPER11_TRANSFER_FLOOR
    )


def test_recommendation_is_local() -> None:
    assert build_report().recommendation == (
        "PAIR_RESONANCE_LOCAL"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PAIR_RESONANCE_TRANSFERS",
        "PAIR_RESONANCE_PARTIAL",
        "PAIR_RESONANCE_LOCAL",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_replay_stability_is_one() -> None:
    """Paper-11 v2 gate #5."""
    assert build_report().replay_stability == 1.0


def test_all_corpora_pair_matrices_keys() -> None:
    matrices = all_corpora_pair_matrices()
    assert set(matrices.keys()) == {
        "v23", "v314", "v315", "v316",
    }


def test_single_anchor_matrix_dimensions() -> None:
    """v315 and v316 each have 1 plateau anchor, so
    their matrix is 1x1."""
    for c in ("v315", "v316"):
        m = per_corpus_pair_matrix(c)
        assert len(m) == 1


def test_artifact_records_eligibility() -> None:
    art = build_cross_corpus_resonance_artifact()
    assert art["eligible_corpora"] == ["v23", "v314"]
    assert art["ineligible_corpora"] == [
        "v315", "v316",
    ]


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_54" / "report.json").read_text(
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
