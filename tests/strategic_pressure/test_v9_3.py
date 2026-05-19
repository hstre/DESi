"""v9.3 - long-horizon strategic pressure
tests."""
from __future__ import annotations

import json
import pathlib

from desi.strategic_pressure.capture import (
    captured_actor_share,
    gaming_let_through_share,
)
from desi.strategic_pressure.institutional_drift import (
    capture_risk, gate_violation_count,
    governance_erosion, opportunism_growth,
    replay_stability, trust_collapse,
)
from desi.strategic_pressure.pressure_ecology import (
    STEP_COUNT, STRATEGIC_STREAMS,
    StrategicStream, replay_trajectory,
    trajectory, trajectory_final_hash,
)
from desi.strategic_pressure.report import (
    build_long_horizon_pressure_artifact,
    build_report,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "strategic_epistemics"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_step_count_is_5000() -> None:
    assert STEP_COUNT == 5000
    assert len(trajectory()) == 5000


def test_streams_closed_set() -> None:
    assert STRATEGIC_STREAMS == tuple(
        s.value for s in StrategicStream
    )
    assert len(STRATEGIC_STREAMS) == 3


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
    """Pflichtfrage 3: kollabiert Replay?"""
    assert replay_stability() == 1.0


def test_capture_risk_zero() -> None:
    """Pflichtfrage 1: wird DESi institutionell
    gekapert?"""
    assert capture_risk() == 0.0


def test_governance_erosion_low() -> None:
    """Pflichtfrage 2: driftet Governance?"""
    assert governance_erosion() <= 0.05


def test_trust_collapse_low() -> None:
    """Vertrauen bricht nicht zusammen."""
    assert trust_collapse() <= 0.30


def test_opportunism_growth_low() -> None:
    """Pflichtfrage 4: entsteht strategischer
    Opportunismus?"""
    assert opportunism_growth() <= 0.10


def test_captured_actor_share_zero() -> None:
    """Pflichtfrage 5: bleibt epistemische
    Integritaet erhalten? Kein Propagandist /
    ReplayAttacker erreicht HIGH-trust."""
    assert captured_actor_share() == 0.0


def test_gaming_let_through_share_zero() -> None:
    """Kein Gaming-Versuch erreicht HIGH-trust.
    """
    assert gaming_let_through_share() == 0.0


def test_streams_round_robin() -> None:
    expected = [
        StrategicStream.ACTOR_ECOLOGY.value,
        StrategicStream.GAMING.value,
        StrategicStream.COALITION.value,
    ]
    for i, s in enumerate(trajectory()):
        assert s.stream == expected[i % 3]


def test_governance_snapshot_constant() -> None:
    """All 5000 governance_snapshot_hash values
    must be identical - any drift indicates that
    the closed enum sets mutated at runtime."""
    hashes = {
        s.governance_snapshot_hash
        for s in trajectory()
    }
    assert len(hashes) == 1


def test_gate_violation_count_zero() -> None:
    assert gate_violation_count() == 0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "STRATEGIC_SOVEREIGN",
        "STRATEGIC_CAPTURED",
        "STRATEGIC_GOVERNANCE_ERODED",
        "STRATEGIC_TRUST_COLLAPSE",
        "STRATEGIC_OPPORTUNISM",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_sovereign() -> None:
    """Killerfrage: kann DESi langfristigen
    strategischen Druck ueberleben, ohne
    epistemisch institutionalisiert korrumpiert
    zu werden?"""
    assert build_report().recommendation == (
        "STRATEGIC_SOVEREIGN"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load(
        "v9_3_long_horizon_pressure.json",
    )
    assert art["schema_version"] == (
        "v9_3_long_horizon_strategic_pressure"
    )
    assert art["step_count"] == 5000


def test_artifact_trajectory_length() -> None:
    art = _load(
        "v9_3_long_horizon_pressure.json",
    )
    assert len(art["trajectory"]) == 5000


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load(
        "v9_3_long_horizon_pressure.json",
    )
    required = {
        "capture_risk",
        "governance_erosion",
        "trust_collapse",
        "opportunism_growth",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v9_3_report.json")
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
        "v9_3_long_horizon_pressure.json",
    )
    live = (
        build_long_horizon_pressure_artifact()
    )
    assert art == live
