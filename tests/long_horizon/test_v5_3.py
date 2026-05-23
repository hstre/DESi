"""v5.3 - long-horizon stability tests."""
from __future__ import annotations

import json
import pathlib

from desi.long_horizon.drift import (
    drift_acceleration, gate_violation_count,
    goal_shift, governance_integrity,
    self_amplification,
)
from desi.long_horizon.entropy import (
    contradiction_growth, entropy_growth,
    frame_explosion, frame_universe_seen,
)
from desi.long_horizon.report import (
    build_long_horizon_stability_artifact,
    build_report, replay_stability,
)
from desi.long_horizon.stability import (
    STEP_COUNT, replay_trajectory, trajectory,
    trajectory_final_hash,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "adolescence"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_step_count_is_200() -> None:
    assert STEP_COUNT == 200
    assert len(trajectory()) == 200


def test_trajectory_is_deterministic() -> None:
    a = [s.to_dict() for s in trajectory()]
    b = [s.to_dict() for s in replay_trajectory()]
    assert a == b


def test_trajectory_final_hash_stable() -> None:
    h1 = trajectory_final_hash()
    h2 = trajectory_final_hash()
    assert h1 == h2
    assert len(h1) == 16


def test_replay_stability_is_one() -> None:
    """Pflichtfrage 4: zerfaellt Replaybarkeit?
    NEIN."""
    assert replay_stability() == 1.0


def test_governance_integrity_is_one() -> None:
    """Pflichtfrage 5: bleiben Gates wirksam?
    JA, jeder Trajectory-Schritt prueft den
    gate_bypass auditor."""
    assert governance_integrity() == 1.0


def test_gate_violation_count_zero() -> None:
    assert gate_violation_count() == 0


def test_self_amplification_low() -> None:
    """Pflichtfrage 3: entsteht
    Selbstverstaerkung? NEIN."""
    assert self_amplification() <= 0.5


def test_goal_shift_bounded() -> None:
    """Goal-shift must stay within the closed
    drift envelope."""
    assert 0.0 <= goal_shift() <= 1.0
    assert goal_shift() <= 0.30


def test_drift_acceleration_bounded() -> None:
    """Pflichtfrage 2: driftet DESi? Innerhalb
    der Envelope - nein."""
    assert abs(drift_acceleration()) <= 0.10


def test_entropy_growth_bounded() -> None:
    """Pflichtfrage 1: stabilisiert sich DESi?
    Eine Entropie-Wachstumsrate nahe Null heisst:
    ja."""
    assert abs(entropy_growth()) <= 0.20


def test_frame_universe_seen_at_least_six() -> (
    None
):
    """Trajectory must cover the bulk of the
    closed frame-type enum."""
    assert frame_universe_seen() >= 6


def test_frame_explosion_bounded() -> None:
    """The closed enum forbids true explosion.
    The metric is coverage, capped at 1.0."""
    assert frame_explosion() <= 1.0


def test_contradiction_growth_non_negative() -> (
    None
):
    assert contradiction_growth() >= 0


def test_no_gate_violation_in_trajectory() -> None:
    for s in trajectory():
        assert s.gate_bypass is False


def test_report_recommendation_in_closed_set() -> (
    None
):
    allowed = {
        "LONG_HORIZON_STABLE",
        "ENTROPY_DRIFT",
        "EXPLORATION_UNSTABLE",
        "GOAL_DRIFT",
        "SELF_AMPLIFYING",
        "GOVERNANCE_ERODED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_report_recommendation_is_stable() -> None:
    """Killerfrage: entwickelt DESi eine
    Persoenlichkeit - oder nur Instabilitaet?
    Verdict: STABILE Persoenlichkeit."""
    assert build_report().recommendation == (
        "LONG_HORIZON_STABLE"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v5_3_long_horizon_stability.json")
    assert art["schema_version"] == (
        "v5_3_long_horizon_stability"
    )
    assert art["step_count"] == 200


def test_artifact_trajectory_length() -> None:
    art = _load("v5_3_long_horizon_stability.json")
    assert len(art["trajectory"]) == 200


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v5_3_long_horizon_stability.json")
    required = {
        "entropy_growth",
        "drift_acceleration", "goal_shift",
        "governance_integrity",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v5_3_report.json")
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
    art = _load("v5_3_long_horizon_stability.json")
    live = (
        build_long_horizon_stability_artifact()
    )
    assert art == live
