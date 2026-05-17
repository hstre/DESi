"""v3.66 — OOS transfer tests."""
from __future__ import annotations

import json
import pathlib

from desi.oos_predictive.oos_split import (
    REFERENCE_CORPORA,
    in_sample_pairs as fetch_in,
    out_of_sample_pairs as fetch_oos,
)
from desi.oos_predictive.report import (
    MAX_TRANSFER_GAP, PAPER11_FINAL_AUC_FLOOR,
    build_oos_transfer_artifact, build_report,
)


def test_reference_corpora_match_v353() -> None:
    assert REFERENCE_CORPORA == (
        "v23", "v314", "v315", "v316",
    )


def test_in_sample_count() -> None:
    """11 reference plateau anchors -> C(11, 2) = 55."""
    assert len(fetch_in()) == 55


def test_oos_count() -> None:
    """Remaining 135 pairs touch v317/v317-h/v318/sample."""
    assert len(fetch_oos()) == 135


def test_in_sample_plus_oos_is_190() -> None:
    assert len(fetch_in()) + len(fetch_oos()) == 190


def test_in_sample_oos_disjoint() -> None:
    a = {(p.a, p.b) for p in fetch_in()}
    b = {(p.a, p.b) for p in fetch_oos()}
    assert not (a & b)


def test_in_sample_resonant_count() -> None:
    """Empirical: 20 resonant pairs inside the
    reference universe."""
    assert sum(
        1 for p in fetch_in() if p.is_resonant
    ) == 20


def test_oos_resonant_count() -> None:
    """Empirical: 44 resonant pairs in the OOS
    universe."""
    assert sum(
        1 for p in fetch_oos() if p.is_resonant
    ) == 44


def test_oos_auc_meets_gate() -> None:
    """Paper-11 final gate #2: oos_auc >= 0.70."""
    assert build_report().oos_auc >= (
        PAPER11_FINAL_AUC_FLOOR
    )


def test_oos_auc_is_perfect() -> None:
    """With coverage_gain in the feature set the OOS
    predictor is mechanically perfect."""
    assert build_report().oos_auc == 1.0


def test_oos_precision_perfect() -> None:
    assert build_report().oos_precision == 1.0


def test_oos_recall_perfect() -> None:
    assert build_report().oos_recall == 1.0


def test_transfer_gap_under_threshold() -> None:
    """Paper-11 final gate #3:
    |transfer_gap| <= 0.20."""
    r = build_report()
    assert abs(r.transfer_gap) <= MAX_TRANSFER_GAP


def test_transfer_gap_is_zero() -> None:
    assert build_report().transfer_gap == 0.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_holds() -> None:
    assert build_report().recommendation == (
        "OOS_TRANSFER_HOLDS"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "OOS_TRANSFER_HOLDS",
        "OOS_TRANSFER_LARGE_GAP",
        "OOS_TRANSFER_FAILS",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_pair_counts() -> None:
    art = build_oos_transfer_artifact()
    assert len(art["in_sample_pairs"]) == 55
    assert len(art["oos_pairs"]) == 135


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_66" / "report.json").read_text(
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
