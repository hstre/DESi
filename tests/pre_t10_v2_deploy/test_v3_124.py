"""v3.124 - pre-T10 v2 go/no-go tests."""
from __future__ import annotations

import json
import pathlib

from desi.pre_t10_v2_deploy.decision import (
    STRATEGIES, Strategy, all_strategy_metrics,
    best_strategy, disqualified_strategies,
    metrics_multi_signal, metrics_no_precheck,
    metrics_single_threshold,
)
from desi.pre_t10_v2_deploy.report import (
    build_pre_t10_v2_go_no_go_artifact,
    build_report,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "v3_124"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_strategies_is_closed_set() -> None:
    assert STRATEGIES == tuple(
        s.value for s in Strategy
    )
    assert len(STRATEGIES) == 3


def test_all_strategy_metrics_count() -> None:
    assert len(all_strategy_metrics()) == 3


def test_no_precheck_far_is_baseline() -> None:
    m = metrics_no_precheck()
    assert m.rule_complexity == 0
    assert m.true_case_recall == 1.0
    assert m.false_activation_rate > 0.5


def test_single_threshold_fails_far() -> None:
    """Honest finding: v3.120 leaks 2 FPs which
    exceeds the 0.10 FAR ceiling."""
    m = metrics_single_threshold()
    assert m.rule_complexity == 1
    assert m.true_case_recall == 1.0
    assert m.false_activation_rate > 0.10
    assert not m.qualifies


def test_multi_signal_qualifies() -> None:
    m = metrics_multi_signal()
    assert m.rule_complexity == 2
    assert m.true_case_recall == 1.0
    assert m.false_activation_rate == 0.0
    assert m.qualifies


def test_best_strategy_is_multi_signal() -> None:
    assert best_strategy() == (
        Strategy.MULTI_SIGNAL.value
    )


def test_disqualified_includes_both_others() -> (
    None
):
    disq = set(disqualified_strategies())
    assert disq == {
        Strategy.NO_PRECHECK.value,
        Strategy.SINGLE_THRESHOLD.value,
    }


def test_single_threshold_has_higher_roi() -> None:
    """Honest tradeoff: single_threshold has the
    higher per-complexity FAR-reduction, but
    fails the FAR ceiling. The picker gates on
    qualification BEFORE ROI."""
    s = metrics_single_threshold()
    m = metrics_multi_signal()
    assert (
        s.architecture_roi
        > m.architecture_roi
    )
    assert best_strategy() == m.strategy


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DEPLOY_MULTI_SIGNAL",
        "DEPLOY_SINGLE_THRESHOLD",
        "DEPLOY_NO_PRECHECK",
        "DEPLOY_NONE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_deploy_multi() -> None:
    """Killerfrage: welche Variante geht in
    Produktion? Multi-signal."""
    assert build_report().recommendation == (
        "DEPLOY_MULTI_SIGNAL"
    )


def test_report_far_matches_chosen_strategy() -> (
    None
):
    r = build_report()
    m = metrics_multi_signal()
    assert r.false_activation_rate == (
        m.false_activation_rate
    )
    assert r.true_case_recall == (
        m.true_case_recall
    )
    assert r.architecture_roi == (
        m.architecture_roi
    )
    assert r.rule_complexity == m.rule_complexity


def test_draws_are_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_report_present() -> None:
    art = _load("report.json")
    assert art["best_strategy"] == (
        "multi_signal"
    )
    assert art["recommendation"] == (
        "DEPLOY_MULTI_SIGNAL"
    )


def test_artifact_go_no_go_present() -> None:
    art = _load("pre_t10_v2_go_no_go.json")
    assert art["schema_version"] == (
        "v3_124_pre_t10_v2_go_no_go"
    )
    assert len(art["metrics"]) == 3
    assert art["best_strategy"] == (
        "multi_signal"
    )


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("report.json")
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


def test_artifact_go_no_go_matches_live() -> None:
    art = _load("pre_t10_v2_go_no_go.json")
    live = build_pre_t10_v2_go_no_go_artifact()
    assert art == live


def test_decision_document_present() -> None:
    doc = (
        _ARTIFACT_ROOT
        / "pre_t10_v2_go_no_go.md"
    ).read_text(encoding="utf-8")
    assert "DEPLOY_MULTI_SIGNAL" in doc
    assert "members_per_family" in doc
    assert "best_strategy" in doc
    assert "replay_stability" in doc
