"""v3.104d - T10 final re-decision tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_redecision.decision import (
    final_complexity_cost,
    final_recovery_gain,
    final_roi,
    t10_directional_decision,
    t10_directional_go,
)
from desi.t10_redecision.report import (
    build_report,
    build_t10_final_redecision_artifact,
)


def test_t10_directional_go_is_true() -> None:
    """Killerfrage: war T10 durch ein falsches
    Gate blockiert? Yes - the directional gate
    accepts T10 cleanly."""
    assert t10_directional_go() is True


def test_decision_has_no_failing_conditions() -> None:
    dec = t10_directional_decision()
    assert dec["passed"] is True
    assert dec["failing_conditions"] == []


def test_final_roi_matches_v3104() -> None:
    """ROI is unchanged from v3.104."""
    from desi.t10_roi.tradeoff import (
        architecture_roi as v3104_roi,
    )
    assert final_roi() == v3104_roi()


def test_final_recovery_matches_v3104() -> None:
    from desi.t10_roi.tradeoff import (
        recovery_gain as v3104_rg,
    )
    assert final_recovery_gain() == v3104_rg()


def test_final_complexity_matches_v3104() -> None:
    from desi.t10_roi.tradeoff import (
        complexity_cost as v3104_cc,
    )
    assert final_complexity_cost() == v3104_cc()


def test_final_roi_far_above_one() -> None:
    assert final_roi() > 10.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_activated() -> None:
    assert build_report().recommendation == (
        "T10_DIRECTIONALLY_ACTIVATED"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "T10_DIRECTIONALLY_ACTIVATED",
        "T10_STILL_BLOCKED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_has_all_metrics() -> None:
    art = build_t10_final_redecision_artifact()
    keys = {
        "t10_directional_go",
        "adverse_auc_delta",
        "beneficial_auc_delta",
        "adverse_flip_count",
        "beneficial_flip_count",
        "final_recovery_gain",
        "final_complexity_cost",
        "final_roi",
        "decision",
    }
    assert keys <= set(art.keys())


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_104d" / "report.json").read_text(
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
