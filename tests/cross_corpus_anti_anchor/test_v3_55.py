"""v3.55 — cross-corpus anti-anchor transfer tests."""
from __future__ import annotations

import json
import pathlib

from desi.cross_corpus.corpus_loader import (
    REFERENCE_CORPORA,
)
from desi.cross_corpus_anti_anchor.anti_anchor_transfer import (
    MIN_SUPPRESSION, MIN_TARGET_RECALL,
    transfer_rate, transfers_at,
)
from desi.cross_corpus_anti_anchor.report import (
    PAPER11_TRANSFER_FLOOR,
    build_cross_corpus_anti_anchor_artifact,
    build_report,
)
from desi.cross_corpus_anti_anchor.suppression import (
    ANTI_COUNT, ANTI_RADIUS, PLATEAU_RADIUS,
    all_corpus_suppression_records,
    per_corpus_anti_ids, per_corpus_suppression,
)


def test_radii_match_v351_anchors() -> None:
    assert PLATEAU_RADIUS == 4.0
    assert ANTI_RADIUS == 2.5
    assert ANTI_COUNT == 5


def test_recall_target_anchor() -> None:
    assert MIN_TARGET_RECALL == 0.90
    assert MIN_SUPPRESSION == 0.80


def test_per_corpus_anti_ids_deterministic() -> None:
    for c in REFERENCE_CORPORA:
        a = per_corpus_anti_ids(c)
        b = per_corpus_anti_ids(c)
        assert a == b


def test_per_corpus_anti_ids_count() -> None:
    """Every reference corpus has >= ANTI_COUNT
    leakage trajectories."""
    for c in REFERENCE_CORPORA:
        ids = per_corpus_anti_ids(c)
        assert len(ids) == ANTI_COUNT


def test_per_corpus_suppression_v23() -> None:
    r = per_corpus_suppression("v23")
    assert r.plateau_count == 6
    assert r.leakage_count == 12
    assert r.baseline_leakage == 12
    assert r.leakage_after_anti == 0
    assert r.suppression_fraction == 1.0
    assert r.plateau_recall == 1.0


def test_per_corpus_suppression_v314() -> None:
    r = per_corpus_suppression("v314")
    assert r.suppression_fraction == 1.0
    assert r.plateau_recall == 1.0


def test_per_corpus_suppression_v315_v316() -> None:
    for c in ("v315", "v316"):
        r = per_corpus_suppression(c)
        assert r.suppression_fraction == 1.0
        assert r.plateau_recall == 1.0


def test_all_records_count() -> None:
    assert len(
        all_corpus_suppression_records()
    ) == len(REFERENCE_CORPORA)


def test_transfers_at_all_corpora() -> None:
    for r in all_corpus_suppression_records():
        assert transfers_at(r) is True


def test_anti_anchor_transfer_rate_is_one() -> None:
    """Paper-11 v2 gate #3: every corpus meets both
    the recall and suppression thresholds. The
    mechanism is universal in this reference set."""
    assert build_report().anti_anchor_transfer_rate == 1.0


def test_transfer_rate_meets_gate() -> None:
    assert build_report().anti_anchor_transfer_rate >= (
        PAPER11_TRANSFER_FLOOR
    )


def test_suppression_per_corpus_uniform() -> None:
    r = build_report()
    for c in REFERENCE_CORPORA:
        assert r.suppression_per_corpus[c] == 1.0


def test_recall_per_corpus_uniform() -> None:
    r = build_report()
    for c in REFERENCE_CORPORA:
        assert r.recall_per_corpus[c] == 1.0


def test_repulsion_per_corpus_matches_baseline() -> None:
    """Every leakage trajectory in each corpus is
    repelled by the anti-anchor at this radius."""
    r = build_report()
    expected = {
        "v23": 12, "v314": 30, "v315": 24, "v316": 24,
    }
    assert r.repulsion_per_corpus == expected


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_universal() -> None:
    assert build_report().recommendation == (
        "ANTI_ANCHOR_UNIVERSAL"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "ANTI_ANCHOR_UNIVERSAL",
        "ANTI_ANCHOR_PARTIAL",
        "ANTI_ANCHOR_LOCAL", "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_records_per_corpus() -> None:
    art = build_cross_corpus_anti_anchor_artifact()
    assert len(art["records"]) == len(REFERENCE_CORPORA)


def test_transfer_rate_callable_with_records() -> None:
    """The helper handles empty inputs gracefully."""
    assert transfer_rate(()) == 0.0


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_55" / "report.json").read_text(
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
