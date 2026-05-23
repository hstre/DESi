"""v3.120a - threshold sweep tests."""
from __future__ import annotations

import json
import pathlib

from desi.pre_t10_calibration.report import (
    build_pre_t10_threshold_sweep_artifact,
    build_report,
)
from desi.pre_t10_calibration.sweep import (
    best_far_at_full_tpr,
    best_tpr_at_zero_far,
    feasible_cells,
    optimal_threshold,
    threshold_window,
    window_width,
)
from desi.pre_t10_calibration.threshold import (
    SWEEP_END,
    SWEEP_START,
    SWEEP_STEP,
    all_sweep_cells,
)


def test_sweep_span_meets_directive() -> None:
    """Directive § v3.120a: threshold +-20%
    around 0.542 ⇒ 0.43..0.65."""
    assert SWEEP_START == 0.43
    assert SWEEP_END == 0.65


def test_sweep_step_is_fine() -> None:
    assert SWEEP_STEP <= 0.01 + 1e-9


def test_sweep_cell_count_at_least_twenty() -> None:
    assert len(all_sweep_cells()) >= 20


def test_no_feasible_calibration_window() -> None:
    """Killerfrage: war das nur 0.011
    Kalibrierungsfehler? NEIN. No single
    threshold simultaneously satisfies
    FAR <= 0.10 AND TPR == 1.0."""
    assert len(feasible_cells()) == 0


def test_threshold_window_is_sentinel() -> None:
    """Empty window is encoded as (-1.0, -1.0)."""
    assert threshold_window() == (-1.0, -1.0)


def test_window_width_is_zero() -> None:
    assert window_width() == 0.0


def test_best_far_at_full_tpr_matches_v3120() -> None:
    """The lowest FAR achievable at TPR=1.0 is
    exactly the v3.120 false_activation_rate."""
    assert abs(
        best_far_at_full_tpr() - 0.111111,
    ) < 1e-3


def test_best_tpr_at_zero_far_below_one() -> None:
    """At FAR=0, TPR drops below 1.0 - confirms
    the rules are mutually unsatisfiable."""
    assert best_tpr_at_zero_far() < 1.0


def test_optimal_threshold_is_within_sweep() -> None:
    """The chosen optimum sits inside the swept
    range (or is the sentinel -1)."""
    opt = optimal_threshold()
    if opt >= 0:
        assert (
            SWEEP_START - 1e-6
            <= opt
            <= SWEEP_END + 1e-6
        )


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "CALIBRATION_WINDOW_FOUND",
        "NO_CALIBRATION_WINDOW",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_no_window() -> None:
    assert build_report().recommendation == (
        "NO_CALIBRATION_WINDOW"
    )


def test_artifact_lists_all_cells() -> None:
    art = build_pre_t10_threshold_sweep_artifact()
    assert len(art["sweep_cells"]) == len(
        all_sweep_cells(),
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_120a" / "report.json").read_text(
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
