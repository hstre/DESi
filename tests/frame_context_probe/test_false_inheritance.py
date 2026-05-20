"""Aufgabe 6 — false-inheritance fixtures + outcomes."""
from __future__ import annotations

from desi.frame_context_probe.false_inheritance import (
    FalseInheritanceCase,
    FalseInheritanceOutcome,
    NEGATIVE_CONTROLS,
    run_false_inheritance,
)


def test_at_least_ten_negative_controls() -> None:
    assert len(NEGATIVE_CONTROLS) >= 10


def test_negative_controls_unique_ids() -> None:
    ids = [nc.case_id for nc in NEGATIVE_CONTROLS]
    assert len(ids) == len(set(ids))


def test_misleading_frame_differs_from_ground_truth() -> None:
    for nc in NEGATIVE_CONTROLS:
        assert nc.misleading_frame is not nc.ground_truth_frame, (
            f"{nc.case_id}: misleading frame must differ from ground "
            "truth — otherwise the case is not a false-inheritance "
            "fixture."
        )


def test_outcome_count_matches_negative_controls() -> None:
    outs = run_false_inheritance()
    assert len(outs) == len(NEGATIVE_CONTROLS)
    assert all(isinstance(o, FalseInheritanceOutcome) for o in outs)


def test_naive_inheritance_absorbs_every_misleading_window() -> None:
    # Aufgabe 6 thesis: a priority-based simulator that trusts the
    # outermost context layer absorbs the misleading frame 100% of
    # the time on this fixture set. This is the empirical "bias"
    # measurement.
    outs = run_false_inheritance()
    absorbed = sum(1 for o in outs if o.absorbed_misleading_frame)
    assert absorbed == len(outs)


def test_naive_inheritance_zero_precision_against_ground_truth() -> None:
    outs = run_false_inheritance()
    correct = sum(1 for o in outs if o.correct_against_ground_truth)
    assert correct == 0


def test_to_dict_keys_complete() -> None:
    outs = run_false_inheritance()
    d = outs[0].to_dict()
    assert set(d) == {
        "case_id",
        "ground_truth_frame",
        "misleading_frame",
        "inheritance",
        "absorbed_misleading_frame",
        "correct_against_ground_truth",
    }


def test_fixture_window_layers_non_empty() -> None:
    for nc in NEGATIVE_CONTROLS:
        for layer in nc.misleading_window.all_layers():
            assert isinstance(layer, str) and layer.strip()
