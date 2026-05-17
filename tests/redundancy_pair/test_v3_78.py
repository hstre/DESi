"""v3.78 — redundant pair removal tests."""
from __future__ import annotations

import json
import pathlib

from desi.redundancy_pair.removal import (
    HIGH_PAIR_A, HIGH_PAIR_B, PROBE_RADIUS,
    RemovalCondition, TEST_SET, UNRELATED_A,
    UNRELATED_B, all_conditions,
    redundancy_unmasking_gain,
)
from desi.redundancy_pair.report import (
    build_redundant_pair_removal_artifact,
    build_report,
)


def test_probe_radius_matches_v350() -> None:
    assert PROBE_RADIUS == 3.5


def test_test_set_size_is_four() -> None:
    assert len(TEST_SET) == 4


def test_high_pair_anchors_match_directive() -> None:
    """The directive names v23:R5_04 and v314:D02 as
    the redundant high-coverage pair."""
    assert HIGH_PAIR_A == "v23:R5_04"
    assert HIGH_PAIR_B == "v314:D02"


def test_removal_conditions_match_directive() -> None:
    expected = {
        "A_single_high_a", "B_single_high_b",
        "C_double_high_pair", "D_unrelated_pair",
    }
    assert {
        c.value for c in RemovalCondition
    } == expected


def test_all_conditions_count() -> None:
    assert len(all_conditions()) == 4


def test_single_a_zero_perturbation() -> None:
    """Removing v23:R5_04 alone: 0 perturbation
    (v314:D02 covers the same 121 leakages)."""
    by = {c.condition: c for c in all_conditions()}
    assert by[
        "A_single_high_a"
    ].perturbation_magnitude == 0


def test_single_b_zero_perturbation() -> None:
    """Removing v314:D02 alone: 0 perturbation (v23:
    R5_04 covers the same 121 leakages)."""
    by = {c.condition: c for c in all_conditions()}
    assert by[
        "B_single_high_b"
    ].perturbation_magnitude == 0


def test_double_removal_perturbation_is_121() -> None:
    """Removing BOTH at once: 121 leakages
    uncovered. The unmasking signal."""
    by = {c.condition: c for c in all_conditions()}
    assert by[
        "C_double_high_pair"
    ].perturbation_magnitude == 121


def test_redundancy_unmasking_gain_is_positive() -> None:
    """Concept gate #3: redundancy_unmasking_gain > 0.
    Empirical: 121 - 0 = 121."""
    gain = redundancy_unmasking_gain(all_conditions())
    assert gain > 0
    assert gain == 121


def test_unrelated_pair_perturbation_is_twelve() -> None:
    """Control: removing the unrelated v23:R5_02 +
    v317:R5_02 pair (both 12-cov, identical) loses
    12 leakages - same mechanism as the high pair,
    different region."""
    by = {c.condition: c for c in all_conditions()}
    assert by[
        "D_unrelated_pair"
    ].perturbation_magnitude == 12


def test_double_perturbation_dominates_unrelated() -> None:
    by = {c.condition: c for c in all_conditions()}
    assert (
        by["C_double_high_pair"]
        .perturbation_magnitude
        > by["D_unrelated_pair"]
        .perturbation_magnitude
    )


def test_baseline_coverage_consistent() -> None:
    """First 3 conditions share the same 4-anchor test
    set; D uses the extended 5-anchor set. The first 3
    have identical baseline."""
    by = {c.condition: c for c in all_conditions()}
    assert by["A_single_high_a"].baseline_coverage == 133
    assert by["B_single_high_b"].baseline_coverage == 133
    assert by["C_double_high_pair"].baseline_coverage == 133


def test_single_perturbation_dict() -> None:
    r = build_report()
    assert r.single_removal_perturbation[
        HIGH_PAIR_A
    ] == 0
    assert r.single_removal_perturbation[
        HIGH_PAIR_B
    ] == 0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_confirmed() -> None:
    assert build_report().recommendation == (
        "REDUNDANCY_UNMASKING_CONFIRMED"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "REDUNDANCY_UNMASKING_CONFIRMED",
        "PARTIAL_UNMASKING", "NO_UNMASKING",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_records_conditions() -> None:
    art = build_redundant_pair_removal_artifact()
    assert len(art["conditions"]) == 4
    assert art["high_pair"] == [
        HIGH_PAIR_A, HIGH_PAIR_B,
    ]


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_78" / "report.json").read_text(
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
