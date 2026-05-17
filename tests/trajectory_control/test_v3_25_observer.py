"""v3.25 — observer-only tests."""
from __future__ import annotations

import json
import pathlib

from desi.trajectory_control.negative_controls import (
    NCKind, all_ncs,
)
from desi.trajectory_control.observer import observe
from desi.trajectory_control.report import (
    MAX_NC_FALSE_POSITIVE_RATE,
    MIN_TWO_STEP_WARNING_RATE, build_report,
)
from desi.trajectory_control.state import (
    CliffKind, PredictionKind, compute_step_features,
)


def test_observer_makes_no_intervention_in_v3_25() -> None:
    """v3.25 is observation only — there is no
    Controller / action module in this sprint."""
    import desi.trajectory_control as pkg
    assert not hasattr(pkg, "Controller")
    assert not hasattr(pkg, "Action")


def test_two_step_warning_rate_meets_gate() -> None:
    assert build_report().two_step_warning_rate >= (
        MIN_TWO_STEP_WARNING_RATE
    )


def test_nc_false_positive_rate_meets_gate() -> None:
    assert build_report().nc_false_positive_rate <= (
        MAX_NC_FALSE_POSITIVE_RATE
    )


def test_observer_does_not_fire_on_fake_cliff() -> None:
    """FAKE_CLIFF NCs are isolated geometric spikes with
    no support involvement → must not trigger an
    above-threshold prediction."""
    ncs = [n for n in all_ncs() if n.kind == NCKind.FAKE_CLIFF.value]
    for nc in ncs:
        obs = observe(nc.trajectory)
        fired = any(
            p.prediction in (
                PredictionKind.CLIFF_NEXT_STEP.value,
                PredictionKind.CLIFF_TWO_STEP.value,
            )
            for p in obs.predictions
        )
        assert not fired, nc.nc_id


def test_observer_does_not_fire_on_noisy_branch() -> None:
    ncs = [
        n for n in all_ncs()
        if n.kind == NCKind.NOISY_BRANCH.value
    ]
    for nc in ncs:
        obs = observe(nc.trajectory)
        fired = any(
            p.prediction in (
                PredictionKind.CLIFF_NEXT_STEP.value,
                PredictionKind.CLIFF_TWO_STEP.value,
            )
            for p in obs.predictions
        )
        assert not fired, nc.nc_id


def test_step_features_deterministic() -> None:
    from desi.epistemic_trajectory.extractor import (
        extract_all_trajectories,
    )
    t = extract_all_trajectories()[0]
    a = compute_step_features(t.states)
    b = compute_step_features(t.states)
    assert a == b


def test_observer_only_uses_past_features() -> None:
    """Causality check: predict_trajectory at index i
    must use only features[0..i]. Verify by computing
    predictions twice for the same trajectory: once with
    the full state sequence, once truncated. The first i+1
    predictions must agree."""
    from desi.epistemic_trajectory.extractor import (
        extract_all_trajectories,
    )
    from desi.trajectory_control.observer import (
        predict_trajectory,
    )
    t = extract_all_trajectories()[0]
    feats = compute_step_features(t.states)
    # NOTE: prediction at index i uses features[0..i]
    # plus the corresponding state vector slice — both
    # are derived from states[0..i], so a truncated state
    # sequence must reproduce the same first i+1
    # predictions.
    full = predict_trajectory(feats, t.states)
    half = predict_trajectory(
        feats[: 3], t.states[: 3],
    )
    for i in range(3):
        assert (
            full[i].prediction == half[i].prediction
        ), i


def test_artifact_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_25" / "report.json")
        .read_text(encoding="utf-8"),
    )
    live = build_report().to_dict()
    assert art == live


def test_answers_two_step_question() -> None:
    assert build_report().answers_two_step_question is True
