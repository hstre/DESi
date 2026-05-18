"""v3.114 - T10 single structural recovery tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_single_structural.inject import (
    proxy_dependence_count,
    selected_structural_candidate,
)
from desi.t10_single_structural.recover import (
    all_outcomes,
    structural_auc,
    structural_purity,
    structural_recovery,
)
from desi.t10_single_structural.report import (
    AUC_THRESHOLD,
    PURITY_THRESHOLD,
    RECOVERY_THRESHOLD,
    build_report,
    build_t10_single_structural_recovery_artifact,
)


def test_selected_candidate_matches_v3113() -> None:
    from desi.t10_deep.graph import top_candidate
    assert selected_structural_candidate() == (
        top_candidate().candidate
    )


def test_outcome_count_is_thirty_one() -> None:
    assert len(all_outcomes()) == 31


def test_proxy_dependence_is_zero() -> None:
    """Concept Gate condition #3:
    proxy_dependence == 0. PASSES because
    structural candidates use no metadata."""
    assert proxy_dependence_count() == 0


def test_structural_recovery_below_gate() -> None:
    """Concept Gate condition #2:
    structural_recovery >= 0.70 FAILS - a
    constant slot rescues nothing."""
    assert structural_recovery() < (
        RECOVERY_THRESHOLD
    )


def test_structural_recovery_is_zero() -> None:
    assert structural_recovery() == 0.0


def test_structural_auc_is_chance() -> None:
    """Adding a constant slot leaves pairwise
    distances unchanged."""
    assert structural_auc() == 0.5


def test_structural_auc_below_gate() -> None:
    assert structural_auc() < AUC_THRESHOLD


def test_structural_purity_below_gate() -> None:
    assert structural_purity() < PURITY_THRESHOLD


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "STRUCTURAL_RESCUES_ALONE",
        "STRUCTURAL_PARTIAL",
        "STRUCTURAL_INSUFFICIENT",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_insufficient() -> None:
    """Killerfrage: kann ein einziges echtes
    Strukturmerkmal die Proxies ersetzen?
    NEIN."""
    assert build_report().recommendation == (
        "STRUCTURAL_INSUFFICIENT"
    )


def test_artifact_lists_outcomes() -> None:
    art = build_t10_single_structural_recovery_artifact()
    assert len(art["outcomes"]) == 31


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_114" / "report.json").read_text(
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
