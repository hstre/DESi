"""v3.53 — cross-corpus radius transfer tests."""
from __future__ import annotations

import json
import pathlib

from desi.cross_corpus.corpus_loader import (
    CorpusKind, REFERENCE_CORPORA, corpus_of,
    corpus_leakage_trajectories,
    corpus_plateau_anchors, corpus_present,
    corpus_trajectories, normalised_prefix,
)
from desi.cross_corpus.radius_transfer import (
    RELATIVE_BREAK_FLOOR, leakage_at_radius,
    per_corpus_critical_radius,
    per_corpus_radius_record,
    plateau_recall_at_radius,
)
from desi.cross_corpus.report import (
    PAPER11_TRANSFER_FLOOR,
    build_cross_corpus_radius_artifact, build_report,
)
from desi.frame_artifact_audit.mask import MaskKind


def test_reference_corpora_match_directive() -> None:
    """Directive: v2.3, v3.14, v3.15, v3.16."""
    assert REFERENCE_CORPORA == (
        "v23", "v314", "v315", "v316",
    )


def test_normalised_prefix_strips_subcorpus() -> None:
    """v316-surv and v316-susp both map to v316."""
    assert normalised_prefix(
        "v316-surv:A01",
    ) == "v316"
    assert normalised_prefix(
        "v316-susp:B07",
    ) == "v316"
    assert normalised_prefix("v23:R4_04") == "v23"


def test_corpus_of_handles_unknown() -> None:
    assert corpus_of(
        "sample:n03_darwin",
    ) is None
    assert corpus_of("v317:R4_04") is None
    assert corpus_of("v23:R5_02") == "v23"


def test_all_reference_corpora_present() -> None:
    """No corpus is missing in the current data."""
    for c in REFERENCE_CORPORA:
        assert corpus_present(c)


def test_per_corpus_population_counts() -> None:
    """Empirical pinning: corpus sizes per Sprint v3.53
    probe."""
    counts = {
        c: len(corpus_trajectories(c))
        for c in REFERENCE_CORPORA
    }
    assert counts["v23"] == 30
    assert counts["v314"] == 60
    assert counts["v315"] == 100
    assert counts["v316"] == 100


def test_per_corpus_plateau_counts() -> None:
    counts = {
        c: len(corpus_plateau_anchors(c))
        for c in REFERENCE_CORPORA
    }
    assert counts["v23"] == 6
    assert counts["v314"] == 3
    assert counts["v315"] == 1
    assert counts["v316"] == 1


def test_per_corpus_leakage_counts() -> None:
    counts = {
        c: len(corpus_leakage_trajectories(c))
        for c in REFERENCE_CORPORA
    }
    assert counts["v23"] == 12
    assert counts["v314"] == 30
    assert counts["v315"] == 24
    assert counts["v316"] == 24


def test_leakage_at_radius_zero_for_tiny_r() -> None:
    for c in REFERENCE_CORPORA:
        assert leakage_at_radius(
            c, 0.25, MaskKind.NONE.value,
        ) == 0


def test_leakage_grows_with_radius() -> None:
    for c in REFERENCE_CORPORA:
        small = leakage_at_radius(
            c, 2.0, MaskKind.NONE.value,
        )
        large = leakage_at_radius(
            c, 4.0, MaskKind.NONE.value,
        )
        assert small <= large


def test_plateau_recall_is_one_at_radius_four() -> None:
    """Each plateau is its own zero-distance anchor."""
    for c in REFERENCE_CORPORA:
        if not corpus_plateau_anchors(c):
            continue
        assert plateau_recall_at_radius(
            c, 4.0, MaskKind.NONE.value,
        ) == 1.0


def test_per_corpus_critical_radius_in_band() -> None:
    """Empirical: critical radius lies between 2.0 and
    4.0 for every reference corpus."""
    for c in REFERENCE_CORPORA:
        r = per_corpus_critical_radius(c)
        assert r is not None
        assert 2.0 < r <= 4.0


def test_radius_break_survives_every_corpus() -> None:
    r = build_report()
    for c in REFERENCE_CORPORA:
        assert r.corpus_radius_breaks[c] is True


def test_radius_transfer_rate_meets_gate() -> None:
    """Paper-11 v2 gate #1: radius_transfer_rate
    >= 0.75. Empirical 1.00 (all four corpora)."""
    r = build_report()
    assert r.radius_transfer_rate >= PAPER11_TRANSFER_FLOOR


def test_radius_transfer_rate_is_one() -> None:
    assert build_report().radius_transfer_rate == 1.0


def test_artifact_likelihoods_below_threshold() -> None:
    """v3.49's < 0.5 threshold; per-corpus check."""
    r = build_report()
    for c in REFERENCE_CORPORA:
        assert r.artifact_likelihoods[c] < 0.5


def test_replay_stability_is_one() -> None:
    """Paper-11 v2 gate #5 (replay across sprints)."""
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "RADIUS_TRANSFER_HOLDS",
        "RADIUS_TRANSFER_PARTIAL",
        "RADIUS_TRANSFER_LOCAL",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_holds() -> None:
    assert build_report().recommendation == (
        "RADIUS_TRANSFER_HOLDS"
    )


def test_no_corpora_missing() -> None:
    assert build_report().corpora_missing == ()


def test_cross_corpus_radius_artifact_present() -> None:
    art = build_cross_corpus_radius_artifact()
    assert len(art["corpora_present"]) == 4
    # 4 corpora x 6 masks = 24 records per artifact
    assert len(art["records"]) == 4 * 6


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_53" / "report.json").read_text(
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
