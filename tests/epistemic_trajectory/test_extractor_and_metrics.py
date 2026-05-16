"""Aufgaben 1 + 3 — trajectory extraction + geometric metrics."""
from __future__ import annotations

from desi.epistemic_trajectory import (
    ALL_NC_TRAJECTORIES,
    DIMENSION_NAMES,
    NCShape,
    StateVector,
    TrajectorySource,
    compute_centroid,
    compute_metrics,
    extract_all_trajectories,
)


def test_state_vector_has_nine_dimensions() -> None:
    assert len(DIMENSION_NAMES) == 9
    v = StateVector(*(0.0,) * 9)
    assert len(v.to_tuple()) == 9


def test_trajectory_count_meets_minimum() -> None:
    trajectories = extract_all_trajectories()
    # The probe also adds 50 synthetic NCs in the report layer,
    # so the input corpora alone should exceed 395.
    assert len(trajectories) >= 395


def test_transition_count_meets_minimum() -> None:
    trajectories = extract_all_trajectories()
    total = sum(
        max(0, len(t.states) - 1) for t in trajectories
    )
    assert total + sum(
        max(0, len(nc.states) - 1) for nc in ALL_NC_TRAJECTORIES
    ) >= 1500


def test_all_six_input_sources_present() -> None:
    seen = {t.source for t in extract_all_trajectories()}
    for s in (
        TrajectorySource.SAMPLE,
        TrajectorySource.V23_MULTISTEP,
        TrajectorySource.V314_HELDOUT,
        TrajectorySource.V315_ADVERSARIAL,
        TrajectorySource.V316_SURVIVING,
        TrajectorySource.V318_WMF,
    ):
        assert s in seen, s.value


def test_extraction_is_deterministic() -> None:
    a = [t.to_dict() for t in extract_all_trajectories()]
    b = [t.to_dict() for t in extract_all_trajectories()]
    assert a == b


def test_compute_metrics_smoothness_zero_for_constant_chain() -> None:
    v = StateVector(*(1.0,) * 9)
    m = compute_metrics(
        "const", (v, v, v, v, v),
        valid_centroid=(1.0,) * 9,
    )
    assert m.smoothness == 0.0
    assert m.curvature == 0.0
    assert m.jerk == 0.0


def test_negative_control_count() -> None:
    assert len(ALL_NC_TRAJECTORIES) >= 50


def test_negative_control_shapes_complete() -> None:
    shapes = {nc.shape for nc in ALL_NC_TRAJECTORIES}
    assert shapes == {s for s in NCShape}


def test_centroid_dimension_matches_state_vector() -> None:
    centroid = compute_centroid(extract_all_trajectories())
    assert len(centroid) == len(DIMENSION_NAMES)
