"""v3.119 - T10 scope boundary tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_boundary.boundary import (
    all_pool_recoverability,
    blindness_prediction_auc,
    false_negative_rate,
    false_positive_rate,
    recoverability_threshold,
    rescuable_pool_count,
    unrescuable_pool_count,
)
from desi.t10_boundary.report import (
    AUC_THRESHOLD,
    build_report,
    build_t10_scope_boundary_artifact,
)


def test_pool_recoverability_count_matches_v3117() -> None:
    from desi.state_blindness.detect import (
        blindness_pool_count,
    )
    assert len(
        all_pool_recoverability(),
    ) == blindness_pool_count()


def test_rescuable_plus_unrescuable_equals_total() -> None:
    assert (
        rescuable_pool_count()
        + unrescuable_pool_count()
        == len(all_pool_recoverability())
    )


def test_recoverability_threshold_in_unit_interval() -> None:
    rt = recoverability_threshold()
    assert 0.0 <= rt <= 1.0


def test_blindness_prediction_auc_above_gate() -> None:
    """Concept Gate condition #3:
    blindness_prediction_auc >= 0.70 PASSES."""
    assert blindness_prediction_auc() >= (
        AUC_THRESHOLD
    )


def test_blindness_prediction_auc_near_perfect() -> None:
    """text_variance separates rescuable from
    unrescuable almost cleanly."""
    assert blindness_prediction_auc() >= 0.90


def test_false_positive_rate_low() -> None:
    """Few unrescuable pools sit above the
    threshold."""
    assert false_positive_rate() <= 0.10


def test_false_negative_rate_low() -> None:
    """Few rescuable pools sit below the
    threshold."""
    assert false_negative_rate() <= 0.10


def test_at_least_one_rescuable_pool() -> None:
    """Killerfrage: wann darf T10 aktiviert
    werden? When the pool is rescuable -
    at least one such pool exists in this
    corpus."""
    assert rescuable_pool_count() >= 1


def test_at_least_one_unrescuable_pool() -> None:
    """And at least one pool is genuinely
    blind - T10 must NOT be activated for
    these."""
    assert unrescuable_pool_count() >= 1


def test_state_variance_is_zero_for_every_pool() -> None:
    """By construction every pool member shares
    the canonical state signature."""
    for o in all_pool_recoverability():
        assert o.state_variance == 0.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "BOUNDARY_PREDICTABLE",
        "BOUNDARY_WEAK_SIGNAL",
        "BOUNDARY_UNPREDICTABLE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_predictable() -> None:
    assert build_report().recommendation == (
        "BOUNDARY_PREDICTABLE"
    )


def test_artifact_lists_all_pools() -> None:
    art = build_t10_scope_boundary_artifact()
    assert len(art["pool_recoverability"]) == (
        len(all_pool_recoverability())
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_119" / "report.json").read_text(
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
