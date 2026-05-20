"""v3.120b - bootstrap stability tests."""
from __future__ import annotations

import json
import pathlib

from desi.pre_t10_bootstrap.bootstrap import (
    BOOTSTRAP_SEEDS,
    all_bootstrap_draws,
)
from desi.pre_t10_bootstrap.report import (
    DRIFT_CEILING,
    build_pre_t10_bootstrap_artifact,
    build_report,
)
from desi.pre_t10_bootstrap.stability import (
    seed_invariance,
    threshold_ci,
    threshold_drift,
    threshold_mean,
)


def test_seed_count_meets_minimum() -> None:
    assert len(BOOTSTRAP_SEEDS) >= 10


def test_all_draws_recorded() -> None:
    draws = all_bootstrap_draws()
    assert len(draws) == len(BOOTSTRAP_SEEDS)


def test_threshold_mean_positive() -> None:
    assert threshold_mean() > 0.0


def test_threshold_ci_increasing() -> None:
    lo, hi = threshold_ci()
    assert lo <= hi


def test_threshold_drift_in_unit_interval() -> None:
    assert 0.0 <= threshold_drift() <= 1.0


def test_threshold_drift_fails_strict_gate() -> None:
    """Honest finding: bootstrap reveals that the
    threshold drifts beyond the 0.05 ceiling when
    the smallest rescuable pool is not sampled."""
    assert threshold_drift() > DRIFT_CEILING


def test_seed_invariance_in_unit_interval() -> None:
    assert 0.0 <= seed_invariance() <= 1.0


def test_seed_invariance_above_half() -> None:
    """The modal threshold dominates: over half
    of bootstrap draws agree."""
    assert seed_invariance() >= 0.50


def test_draws_are_deterministic() -> None:
    a = all_bootstrap_draws()
    b = all_bootstrap_draws()
    assert a == b


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "THRESHOLD_STABLE",
        "THRESHOLD_MODE_STABLE",
        "THRESHOLD_DRIFTS",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_acknowledges_drift() -> None:
    """Killerfrage: ist der Threshold real - oder
    Zufall? The modal threshold is real but the
    tail drifts substantially when sub-samples
    miss the lowest-variance rescuable pool."""
    r = build_report()
    if r.threshold_drift > DRIFT_CEILING:
        assert r.recommendation in {
            "THRESHOLD_MODE_STABLE",
            "THRESHOLD_DRIFTS",
        }


def test_artifact_lists_all_draws() -> None:
    art = build_pre_t10_bootstrap_artifact()
    assert len(art["bootstrap_draws"]) == (
        len(BOOTSTRAP_SEEDS)
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_120b" / "report.json").read_text(
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
