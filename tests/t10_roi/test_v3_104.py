"""v3.104 - T10 recovery vs complexity tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_roi.complexity import (
    compression_delta,
    overfitting_risk,
    state_dim_cost,
    tail_vector_cost,
)
from desi.t10_roi.report import (
    build_report,
    build_t10_recovery_vs_complexity_artifact,
)
from desi.t10_roi.tradeoff import (
    architecture_roi,
    complexity_cost,
    recovery_gain,
)


def test_state_dim_cost_is_one_tenth() -> None:
    """9 -> 10 dimensions ⇒ 1/10."""
    assert state_dim_cost() == 0.1


def test_tail_vector_cost_positive() -> None:
    assert tail_vector_cost() > 0.0


def test_compression_delta_positive() -> None:
    """Adding a dim splits collapsed points, so
    the v3.100 compression_gain shrinks."""
    assert compression_delta() > 0.0


def test_overfitting_risk_is_zero() -> None:
    """contradiction_type is binary; the
    19-anchor pool splits into 9 + 10 buckets,
    so no anchor has a unique value."""
    assert overfitting_risk() == 0.0


def test_recovery_gain_positive() -> None:
    """Sum of beneficial deltas across the v3.94 /
    v3.96 / v3.100 rescue targets must be > 0."""
    assert recovery_gain() > 0.0


def test_recovery_gain_large() -> None:
    """The beneficial deltas are substantial -
    purity 0.526 -> 1.000 (twice) and AUC
    0.506 -> 1.000."""
    assert recovery_gain() > 1.0


def test_complexity_cost_in_unit_interval() -> None:
    assert 0.0 <= complexity_cost() <= 1.0


def test_architecture_roi_far_above_one() -> None:
    """Killerfrage: ist die verlorene
    Information die zusaetzliche Komplexitaet
    wert? Yes - ROI is well above 1."""
    assert architecture_roi() > 1.0


def test_architecture_roi_above_ten() -> None:
    """Closed sanity bound: recovery dominates
    cost by more than an order of magnitude."""
    assert architecture_roi() > 10.0


def test_recovery_exceeds_compression_delta() -> None:
    """The compression we lose is dwarfed by the
    purity/AUC we gain."""
    assert recovery_gain() > compression_delta()


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_worth_it() -> None:
    assert build_report().recommendation == (
        "ARCHITECTURE_EXPANSION_WORTH_IT"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "ARCHITECTURE_EXPANSION_WORTH_IT",
        "ARCHITECTURE_EXPANSION_MARGINAL",
        "ARCHITECTURE_EXPANSION_NOT_WORTH",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_has_all_metrics() -> None:
    art = build_t10_recovery_vs_complexity_artifact()
    keys = {
        "base_state_dim_count",
        "state_dim_cost", "tail_vector_cost",
        "compression_delta",
        "overfitting_risk",
        "recovery_gain", "complexity_cost",
        "architecture_roi",
    }
    assert keys <= set(art.keys())


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_104" / "report.json").read_text(
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
