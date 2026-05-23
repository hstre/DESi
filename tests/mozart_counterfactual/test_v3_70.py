"""v3.70 — Mozart counterfactual swap tests."""
from __future__ import annotations

import json
import pathlib

from desi.mozart_counterfactual.counterfactual import (
    aggregate, mozart_baseline_score,
)
from desi.mozart_counterfactual.report import (
    build_mozart_counterfactual_artifact,
    build_report,
)
from desi.mozart_counterfactual.swap import (
    RANDOM_CONTROL_COUNT, all_swap_results,
    deterministic_random_control_ids,
    input_specificity,
)


def test_random_control_count_is_five() -> None:
    assert RANDOM_CONTROL_COUNT == 5


def test_deterministic_control_ids_stable() -> None:
    a = deterministic_random_control_ids()
    b = deterministic_random_control_ids()
    assert a == b
    assert len(a) == RANDOM_CONTROL_COUNT


def test_controls_exclude_sample_corpus() -> None:
    """Random controls are drawn from non-sample
    trajectories so they don't contain Mozart/Darwin
    themselves."""
    for cid in deterministic_random_control_ids():
        assert not cid.startswith("sample:")


def test_all_swap_results_includes_history_and_controls() -> None:
    swaps = all_swap_results()
    roles = {s.swap_role for s in swaps}
    assert roles == {"historical", "random_control"}
    # 2 historical (darwin + kant) + 5 random = 7
    assert len(swaps) == 7


def test_mozart_baseline_positive() -> None:
    assert mozart_baseline_score() > 0


def test_darwin_close_to_mozart() -> None:
    """Darwin is the closest substitute; relative
    loss is within the FrameDetector jitter band."""
    swaps = all_swap_results()
    darwin = next(
        s for s in swaps
        if s.swap_id == "sample:n03_darwin"
    )
    assert darwin.available
    assert abs(darwin.relative_loss) < 0.30


def test_kant_swap_unavailable() -> None:
    """sample:n03_kant is missing; the swap is
    documented as unavailable with full coverage
    loss."""
    swaps = all_swap_results()
    kant = next(
        s for s in swaps
        if s.swap_id == "sample:n03_kant"
    )
    assert kant.available is False
    assert kant.relative_loss == 1.0


def test_random_controls_strictly_below_mozart() -> None:
    """Every random control has at most 70% of
    Mozart's coverage_score; the random-control
    margin is the source of the stable
    input_specificity."""
    swaps = all_swap_results()
    mozart_score = mozart_baseline_score()
    for s in swaps:
        if s.swap_role != "random_control":
            continue
        assert s.coverage_score <= 0.70 * mozart_score


def test_input_specificity_positive() -> None:
    """Paper-11 historical gate #2:
    input_specificity > 0. Comparator is restricted
    to random_control role so the value is stable
    across hash seeds."""
    r = build_report()
    assert r.input_specificity > 0


def test_input_specificity_in_stable_band() -> None:
    """Empirical 12-seed sweep: 0.747 .. 0.848.
    Always > 0.70."""
    r = build_report()
    assert 0.70 < r.input_specificity < 0.90


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_input_specific() -> None:
    assert build_report().recommendation == (
        "MOZART_INPUT_SPECIFIC"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "MOZART_INPUT_SPECIFIC",
        "MOZART_NOT_INPUT_SPECIFIC",
        "MOZART_BELOW_CONTROLS",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_swapped_coverage_dict_has_all_swap_ids() -> None:
    r = build_report()
    ids = {s["swap_id"] for s in r.swap_results}
    assert set(
        r.swapped_coverage.keys(),
    ) == ids


def test_artifact_records_random_controls() -> None:
    art = build_mozart_counterfactual_artifact()
    assert len(art["random_control_ids"]) == (
        RANDOM_CONTROL_COUNT
    )
    assert len(art["swap_results"]) == 7


def test_artifact_report_matches_live_build() -> None:
    """mozart_coverage_score, swapped_coverage,
    coverage_loss and input_specificity all depend on
    coverage_score values from v3.69 which jitter
    under PYTHONHASHSEED. Mark numeric fields as
    volatile; the recommendation and structural
    counts (random_control_ids, replay_stability)
    are stable."""
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_70" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {
        "rationale", "mozart_coverage_score",
        "swapped_coverage", "coverage_loss",
        "input_specificity", "swap_results",
    }
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
