"""v3.46 — GAP_DETECTED census tests."""
from __future__ import annotations

import json
import pathlib

from desi.epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from desi.epistemic_trajectory.state import StateVector
from desi.gap_detected.extractor import (
    collect_gap_cases, gap_cases_outside_non_rescued,
    source_corpus_distribution, terminal_gap_cases,
    transient_gap_cases,
)
from desi.gap_detected.report import (
    build_gap_inventory_artifact, build_report,
)
from desi.gap_detected.state import (
    GAP_DETECTED_STATE, GapPattern,
    PAPER10_TERMINAL_GAP_COUNT, classify_gap,
)


def _sv(support: float) -> StateVector:
    return StateVector(
        frame_id=0.0, contradiction_load=0.0,
        anchor_density=0.0, source_quality=0.0,
        novelty=0.0, confidence=0.5, branch_cost=1.0,
        support_state=support, routing_state=0.0,
    )


def test_gap_detected_state_anchor() -> None:
    assert GAP_DETECTED_STATE == 1.0


def test_paper10_terminal_gap_count_constant() -> None:
    assert PAPER10_TERMINAL_GAP_COUNT == 2


def test_classify_no_gap() -> None:
    assert classify_gap(
        (_sv(4.0), _sv(4.0), _sv(2.0)),
    ) == GapPattern.NO_GAP


def test_classify_terminal_gap_single_visit() -> None:
    """A single 1.0 at the final state with no
    preceding 1.0 is TERMINAL_GAP."""
    assert classify_gap(
        (_sv(4.0), _sv(4.0), _sv(1.0)),
    ) == GapPattern.TERMINAL_GAP


def test_classify_transient_gap() -> None:
    assert classify_gap(
        (_sv(4.0), _sv(1.0), _sv(4.0)),
    ) == GapPattern.TRANSIENT_GAP


def test_classify_mid_run_gap() -> None:
    """Two consecutive 1.0 entries that include the
    final state."""
    assert classify_gap(
        (_sv(4.0), _sv(4.0), _sv(1.0), _sv(1.0)),
    ) == GapPattern.MID_RUN_GAP


def test_gap_detected_count_is_two() -> None:
    assert build_report().gap_detected_count == 2


def test_terminal_gap_count_is_two() -> None:
    """Concept Gate #1: terminal_gap_count >= 2."""
    assert build_report().terminal_gap_count == (
        PAPER10_TERMINAL_GAP_COUNT
    )


def test_transient_gap_count_is_zero() -> None:
    assert build_report().transient_gap_count == 0


def test_gap_outside_non_rescued_is_zero() -> None:
    """Both GAP cases are in the v3.30 controller's
    non-rescued set; no GAP is "outside" Paper 10."""
    assert build_report().gap_outside_non_rescued == 0


def test_source_corpus_distribution_is_sample() -> None:
    assert build_report().source_corpus_distribution == (
        {"sample": 2}
    )


def test_terminal_gap_ids() -> None:
    ids = {c.trajectory_id for c in terminal_gap_cases()}
    assert ids == {
        "sample:n03_darwin", "sample:n03_mozart",
    }


def test_terminal_cases_marked_in_non_rescued() -> None:
    for c in terminal_gap_cases():
        assert c.in_v330_non_rescued is True


def test_gap_indices_recorded() -> None:
    for c in terminal_gap_cases():
        # final state index = trajectory_length - 1
        assert c.gap_index_last == (
            c.trajectory_length - 1
        )


def test_gap_replay_stability_is_one() -> None:
    """Concept Gate #2: replay_stability == 1.0."""
    assert build_report().gap_replay_stability == 1.0


def test_matches_paper10_flag() -> None:
    assert build_report().matches_paper10 is True


def test_recommendation_is_matches_paper10() -> None:
    assert build_report().recommendation == (
        "GAP_CENSUS_MATCHES_PAPER10"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "GAP_CENSUS_MATCHES_PAPER10",
        "GAP_CENSUS_EXCEEDS_NON_RESCUED",
        "GAP_CENSUS_EXCEEDS_PAPER10",
        "HALT_TERMINAL_GAP_BELOW_PAPER10",
    }
    assert build_report().recommendation in allowed


def test_inventory_artifact_count_matches() -> None:
    art = build_gap_inventory_artifact()
    assert art["case_count"] == 2
    assert len(art["cases"]) == 2


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_46" / "report.json").read_text(
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
