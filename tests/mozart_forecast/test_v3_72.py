"""v3.72 — Mozart forecast tests."""
from __future__ import annotations

import json
import pathlib

from desi.mozart_forecast.forecast import (
    run_forecast,
)
from desi.mozart_forecast.predict import (
    forecast_score, max_novelty_at_zero,
    state0_novelty,
)
from desi.mozart_forecast.report import (
    build_mozart_forecast_artifact, build_report,
)


def test_max_novelty_at_zero_is_twelve() -> None:
    """Mozart's state[0].novelty = 12.0 is the corpus
    maximum at the initial state."""
    assert max_novelty_at_zero() == 12.0


def test_mozart_forecast_score_is_one() -> None:
    """Mozart sets the maximum; forecast_score = 1.0."""
    r = build_report()
    assert r.mozart_forecast_score == 1.0


def test_darwin_forecast_score_near_one() -> None:
    """Darwin's state[0].novelty = 11.0; score
    = 11 / 12 = 0.917."""
    r = build_report()
    assert (
        0.91
        <= r.historical_forecast_scores[
            "sample:n03_darwin"
        ]
        <= 0.92
    )


def test_kant_forecast_score_is_zero() -> None:
    """Missing trajectory; defaults to 0.0."""
    r = build_report()
    assert r.historical_forecast_scores[
        "sample:n03_kant"
    ] == 0.0


def test_all_control_scores_are_zero() -> None:
    """Random controls have state[0].novelty = 0."""
    r = build_report()
    for cid, score in (
        r.control_forecast_scores.items()
    ):
        assert score == 0.0


def test_forecast_margin_positive() -> None:
    """Paper-11 historical gate #4:
    forecast_margin > 0."""
    assert build_report().forecast_margin > 0


def test_forecast_margin_is_one() -> None:
    """Empirical: 1.00 (mozart score minus best
    control)."""
    assert build_report().forecast_margin == 1.0


def test_calibration_error_zero() -> None:
    """Mozart's forecast (1.00) matches its actual
    coverage_percentile (1.00 from v3.69)."""
    assert build_report().calibration_error == 0.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_forecastable() -> None:
    assert build_report().recommendation == (
        "MOZART_FORECASTABLE"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "MOZART_FORECASTABLE",
        "MOZART_FORECAST_TIED",
        "MOZART_NOT_FORECASTABLE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_forecast_score_helper() -> None:
    from desi.epistemic_trajectory.extractor import (
        extract_all_trajectories,
    )
    moz = next(
        t for t in extract_all_trajectories()
        if t.trajectory_id == "sample:n03_mozart"
    )
    assert forecast_score(moz) == 1.0
    assert state0_novelty(moz) == 12.0


def test_artifact_summary_present() -> None:
    art = build_mozart_forecast_artifact()
    assert art["max_novelty_at_zero"] == 12.0
    assert "summary" in art


def test_paper11_historical_gate_summary() -> None:
    """All five Mozart probe historical gates
    evaluated end-to-end."""
    from desi.mozart_coverage_source.report import (
        build_report as v371,
    )
    from desi.mozart_counterfactual.report import (
        build_report as v370,
    )
    from desi.mozart_probe.report import (
        MOZART_PERCENTILE_FLOOR,
        build_report as v369,
    )
    r69 = v369()
    r70 = v370()
    r71 = v371()
    r72 = build_report()
    # Gate 1: mozart coverage_percentile >= 0.90
    assert r69.mozart_coverage_percentile >= (
        MOZART_PERCENTILE_FLOOR
    )
    # Gate 2: input_specificity > 0
    assert r70.input_specificity > 0
    # Gate 3: new_regions > 0
    assert r71.new_regions > 0
    # Gate 4: forecast_margin > 0
    assert r72.forecast_margin > 0
    # Gate 5: replay stability across all sprints
    assert r69.replay_stability == 1.0
    assert r70.replay_stability == 1.0
    assert r71.replay_stability == 1.0
    assert r72.replay_stability == 1.0


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_72" / "report.json").read_text(
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
