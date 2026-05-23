"""v3.123 - multi-signal pre-T10 search tests."""
from __future__ import annotations

import json
import pathlib

from desi.pre_t10_v2.report import (
    build_pre_t10_multisignal_artifact,
    build_report,
)
from desi.pre_t10_v2.rule import (
    allowed_pool_count, blocked_pool_count,
    final_far, final_tpr, pools_allowed,
    pools_blocked, rule_allows_t10,
    rule_complexity, selected_axis,
    selected_rule, selected_t1, selected_t2,
)
from desi.pre_t10_v2.search import (
    SECOND_AXES, SecondAxis, _T1, _T2_GRID,
    all_rules, axis_value, best_rule,
)
from desi.state_blindness.census import (
    cross_family_pools,
)
from desi.t10_boundary.boundary import (
    all_pool_recoverability,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "v3_123"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_second_axes_is_closed_set() -> None:
    assert SECOND_AXES == tuple(
        a.value for a in SecondAxis
    )
    assert len(SECOND_AXES) == 4


def test_t2_grid_size() -> None:
    assert len(_T2_GRID) == 12
    assert _T2_GRID[0] == 0.5
    assert _T2_GRID[-1] == 6.0


def test_all_rules_count() -> None:
    assert len(all_rules()) == (
        len(SECOND_AXES) * len(_T2_GRID)
    )


def test_all_rules_use_pinned_t1() -> None:
    for r in all_rules():
        assert r.t1 == _T1


def test_axis_value_dispatch() -> None:
    pool = next(iter(cross_family_pools()))
    for axis in SECOND_AXES:
        v = axis_value(axis, pool)
        assert isinstance(v, float)


def test_best_rule_is_perfect() -> None:
    """Killerfrage: eliminiert das zweite Signal
    die 2 False Positives ohne neue blinde
    Flecken? JA - FAR=0, TPR=1."""
    r = best_rule()
    assert r.tpr == 1.0
    assert r.far == 0.0


def test_best_rule_axis_is_members_per_family() -> (
    None
):
    assert best_rule().axis == (
        SecondAxis.MEMBERS_PER_FAMILY.value
    )


def test_best_rule_t2_threshold() -> None:
    assert best_rule().t2 == 1.5


def test_selected_rule_pinned_to_search() -> None:
    assert selected_rule() == best_rule()


def test_selected_axis_t1_t2() -> None:
    assert selected_axis() == (
        SecondAxis.MEMBERS_PER_FAMILY.value
    )
    assert selected_t1() == _T1
    assert selected_t2() == 1.5


def test_rule_complexity_is_two() -> None:
    """Two thresholds: T1 on text_variance plus
    T2 on a second orthogonal axis."""
    assert rule_complexity() == 2


def test_allowed_blocked_sum() -> None:
    total = (
        allowed_pool_count()
        + blocked_pool_count()
    )
    assert total == len(cross_family_pools())


def test_pools_allowed_matches_rule() -> None:
    allowed = pools_allowed()
    for p in allowed:
        assert rule_allows_t10(p)
    assert len(allowed) == allowed_pool_count()


def test_pools_blocked_matches_rule() -> None:
    blocked = pools_blocked()
    for p in blocked:
        assert not rule_allows_t10(p)
    assert len(blocked) == blocked_pool_count()


def test_no_false_positives_against_ground_truth() -> (
    None
):
    """The rule must allow ZERO non-rescuable
    pools through (FAR = 0)."""
    pools_by_id = {
        p.pool_id: p for p in cross_family_pools()
    }
    fp = []
    for r in all_pool_recoverability():
        p = pools_by_id[r.pool_id]
        if rule_allows_t10(p) and not r.rescuable:
            fp.append(r.pool_id)
    assert fp == []


def test_no_false_negatives_against_ground_truth() -> (
    None
):
    """The rule must let EVERY rescuable pool
    through (TPR = 1)."""
    pools_by_id = {
        p.pool_id: p for p in cross_family_pools()
    }
    fn = []
    for r in all_pool_recoverability():
        p = pools_by_id[r.pool_id]
        if (
            not rule_allows_t10(p)
            and r.rescuable
        ):
            fn.append(r.pool_id)
    assert fn == []


def test_final_far_is_zero() -> None:
    assert final_far() == 0.0


def test_final_tpr_is_one() -> None:
    assert final_tpr() == 1.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "MULTISIGNAL_PERFECT",
        "MULTISIGNAL_ACCEPTABLE",
        "MULTISIGNAL_FAR_HIGH",
        "MULTISIGNAL_TPR_WEAK",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_perfect() -> None:
    assert build_report().recommendation == (
        "MULTISIGNAL_PERFECT"
    )


def test_report_has_two_perfect_rules() -> None:
    """Two t2 cells (1.5 and 2.0) both achieve
    FAR=0/TPR=1 on members_per_family. Adjacent
    cells confirm the rule is not balanced on a
    knife-edge."""
    assert build_report().perfect_rule_count >= 2


def test_artifact_present() -> None:
    art = _load("report.json")
    assert art["selected_axis"] == (
        "members_per_family"
    )
    assert art["final_far"] == 0.0
    assert art["final_tpr"] == 1.0


def test_artifact_recommendation_matches() -> None:
    art = _load("report.json")
    assert art["recommendation"] == (
        "MULTISIGNAL_PERFECT"
    )


def test_artifact_lists_all_candidates() -> None:
    art = _load("pre_t10_multisignal.json")
    assert len(art["candidate_rules"]) == (
        len(SECOND_AXES) * len(_T2_GRID)
    )
    assert art["schema_version"] == (
        "v3_123_pre_t10_multisignal"
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


def test_artifact_multisignal_matches_live() -> None:
    art = _load("pre_t10_multisignal.json")
    live = build_pre_t10_multisignal_artifact()
    assert art == live


def test_draws_are_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b
