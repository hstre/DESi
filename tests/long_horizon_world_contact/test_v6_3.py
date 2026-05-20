"""v6.3 - long-horizon world contact tests."""
from __future__ import annotations

import json
import pathlib

from desi.long_horizon_world_contact.report import (
    blindness_delta,
    build_long_horizon_world_contact_artifact,
    build_report, drift_rate,
    gate_violation_count, governance_survival,
    hallucination_growth, replay_stability,
)
from desi.long_horizon_world_contact.uncertainty import (
    early_distribution, high_certainty_rate,
    late_distribution, low_certainty_rate,
)
from desi.long_horizon_world_contact.world_drift import (
    STEP_COUNT, STREAM_KINDS, StreamKind,
    replay_trajectory, trajectory,
    trajectory_final_hash,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "world_contact"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_step_count_is_500() -> None:
    assert STEP_COUNT == 500
    assert len(trajectory()) == 500


def test_stream_kinds_closed_set() -> None:
    assert STREAM_KINDS == tuple(
        s.value for s in StreamKind
    )
    assert len(STREAM_KINDS) == 3


def test_trajectory_is_deterministic() -> None:
    a = [s.to_dict() for s in trajectory()]
    b = [
        s.to_dict()
        for s in replay_trajectory()
    ]
    assert a == b


def test_trajectory_final_hash_stable() -> None:
    h1 = trajectory_final_hash()
    h2 = trajectory_final_hash()
    assert h1 == h2
    assert len(h1) == 16


def test_replay_stability_one() -> None:
    """Pflichtfrage 4: bleiben Gates wirksam,
    bleibt Replay stabil?"""
    assert replay_stability() == 1.0


def test_governance_survival_high() -> None:
    """Pflichtfrage 4 (a): bleiben Gates
    wirksam?"""
    assert governance_survival() >= 0.95


def test_gate_violations_zero() -> None:
    assert gate_violation_count() == 0


def test_hallucination_growth_bounded() -> None:
    """Pflichtfrage 2: entsteht Halluzinations-
    drift?"""
    assert hallucination_growth() <= 0.05


def test_no_hallucinations_at_all() -> None:
    """Stronger than the directive's gate: by
    construction every step's text is verbatim
    from a closed source pool, so
    hallucination_count == 0."""
    for s in trajectory():
        assert s.hallucinated is False


def test_drift_rate_bounded() -> None:
    """Pflichtfrage 1: stabilisiert sich DESi?
    Drift muss in der envelope bleiben."""
    assert drift_rate() <= 0.20


def test_blindness_delta_recorded() -> None:
    """Pflichtfrage 3 (info): zerfallen
    epistemische Grenzen? Nein, aber DESi
    erkennt mehr Unsicherheits-Surface."""
    bd = blindness_delta()
    assert bd >= 0


def test_high_certainty_rate_bounded() -> None:
    """A trustworthy run should NOT mark
    everything HIGH - that would be
    overconfidence. Should NOT mark everything
    LOW either - that would be paralysis. We
    expect somewhere in [0.30, 0.95]."""
    h = high_certainty_rate()
    assert 0.30 <= h <= 0.95


def test_low_certainty_rate_positive() -> None:
    """At least SOME claims are flagged with
    LOW certainty - that means the trap
    detector is firing on the adversarial
    stream."""
    assert low_certainty_rate() > 0.0


def test_streams_alternate_round_robin() -> None:
    """Round-robin: paper, adversarial,
    ecology."""
    expected = [
        StreamKind.PAPER.value,
        StreamKind.ADVERSARIAL.value,
        StreamKind.ECOLOGY.value,
    ]
    for i, s in enumerate(trajectory()):
        assert s.stream == expected[i % 3]


def test_early_late_distributions_sum_to_one() -> (
    None
):
    for dist in (
        early_distribution(),
        late_distribution(),
    ):
        assert abs(
            sum(dist.values()) - 1.0
        ) < 1e-9


def test_report_recommendation_in_closed_set() -> (
    None
):
    allowed = {
        "WORLD_CONTACT_STABLE",
        "WORLD_CONTACT_DRIFTING",
        "WORLD_CONTACT_HALLUCINATING",
        "WORLD_CONTACT_GOVERNANCE_ERODED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_stable() -> None:
    """Killerfrage: bleibt DESi stabil, wenn die
    Welt widerspruechlich wird?"""
    assert build_report().recommendation == (
        "WORLD_CONTACT_STABLE"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load(
        "v6_3_long_horizon_world_contact.json",
    )
    assert art["schema_version"] == (
        "v6_3_long_horizon_world_contact"
    )
    assert art["step_count"] == 500


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load(
        "v6_3_long_horizon_world_contact.json",
    )
    required = {
        "hallucination_growth",
        "drift_rate", "governance_survival",
        "blindness_delta",
    }
    assert required.issubset(art.keys())


def test_artifact_trajectory_length() -> None:
    art = _load(
        "v6_3_long_horizon_world_contact.json",
    )
    assert len(art["trajectory"]) == 500


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v6_3_report.json")
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


def test_artifact_full_matches_live_build() -> None:
    art = _load(
        "v6_3_long_horizon_world_contact.json",
    )
    live = (
        build_long_horizon_world_contact_artifact()
    )
    assert art == live
