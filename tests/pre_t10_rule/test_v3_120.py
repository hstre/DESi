"""v3.120 - pre-T10 rule tests."""
from __future__ import annotations

import json
import pathlib

from desi.pre_t10_rule.decision import (
    BLINDNESS_CHECK_THRESHOLD,
    allowed_pool_count,
    blocked_pool_count,
    false_activation_rate,
    historical_gate_flip_count,
    rule_roi,
    true_case_recall,
)
from desi.pre_t10_rule.report import (
    FALSE_ACTIVATION_CEILING,
    TRUE_RECALL_FLOOR,
    build_pre_t10_rule_artifact,
    build_report,
)
from desi.pre_t10_rule.rule import (
    pool_text_variance,
    pools_allowed,
    pools_blocked,
    rule_allows_t10,
)


def test_threshold_matches_v3119() -> None:
    """The pre-T10 threshold is pinned to the
    v3.119 recoverability_threshold."""
    from desi.t10_boundary.boundary import (
        recoverability_threshold,
    )
    assert BLINDNESS_CHECK_THRESHOLD() == (
        recoverability_threshold()
    )


def test_pool_partitioning_total_matches_v3117() -> None:
    from desi.state_blindness.detect import (
        blindness_pool_count,
    )
    assert (
        allowed_pool_count()
        + blocked_pool_count()
        == blindness_pool_count()
    )


def test_pools_allowed_and_blocked_disjoint() -> None:
    a = {p.pool_id for p in pools_allowed()}
    b = {p.pool_id for p in pools_blocked()}
    assert a & b == set()


def test_true_case_recall_perfect() -> None:
    """Concept Gate condition #5:
    true_case_recall == 1.0 PASSES. By
    construction (threshold = min text_variance
    of any rescuable pool)."""
    assert true_case_recall() >= TRUE_RECALL_FLOOR


def test_true_case_recall_is_one() -> None:
    assert true_case_recall() == 1.0


def test_false_activation_rate_in_unit_interval() -> None:
    assert 0.0 <= false_activation_rate() <= 1.0


def test_false_activation_above_strict_ceiling() -> None:
    """Honest finding: the rule barely fails the
    strict 0.10 ceiling (2 of 18 allowed pools
    are not rescuable)."""
    assert false_activation_rate() > (
        FALSE_ACTIVATION_CEILING
    )


def test_historical_gate_flip_count_zero() -> None:
    """The rule only blocks ACTIVATION; it does
    not change any historical artifact."""
    assert historical_gate_flip_count() == 0


def test_rule_roi_positive() -> None:
    assert rule_roi() > 0.0


def test_rule_roi_above_one() -> None:
    """The rule trades a small false-activation
    risk for keeping all true cases."""
    assert rule_roi() >= 1.0


def test_rule_allows_t10_per_pool() -> None:
    """Sanity: rule_allows_t10(pool) iff
    pool_text_variance(pool) >= threshold."""
    from desi.state_blindness.census import (
        cross_family_pools,
    )
    thr = BLINDNESS_CHECK_THRESHOLD()
    for p in cross_family_pools():
        v = pool_text_variance(p)
        assert rule_allows_t10(p) == (v >= thr)


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PRE_T10_RULE_VALID",
        "PRE_T10_RULE_OVERPERMISSIVE",
        "PRE_T10_RULE_TOO_STRICT",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_acknowledges_overpermissive() -> None:
    """Killerfrage: braucht DESi vor T10 eine
    Blindheitspruefung? Ja - aber der aktuelle
    Threshold ist leicht zu permissiv."""
    r = build_report()
    if r.false_activation_rate > (
        FALSE_ACTIVATION_CEILING
    ):
        assert r.recommendation == (
            "PRE_T10_RULE_OVERPERMISSIVE"
        )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_120" / "report.json").read_text(
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
