"""v10.3 - long-horizon institutional drift
tests."""
from __future__ import annotations

import json
import pathlib

from desi.institutional_drift.bureaucracy import (
    bureaucracy_growth, flexibility_loss,
)
from desi.institutional_drift.capture import (
    gate_violation_count, governance_erosion,
    institutional_capture,
)
from desi.institutional_drift.institutional_drift import (
    INSTITUTIONAL_STREAMS, STEP_COUNT,
    InstitutionalStream, replay_trajectory,
    trajectory, trajectory_final_hash,
)
from desi.institutional_drift.report import (
    build_long_horizon_drift_artifact,
    build_report, replay_stability,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "institutional_governance"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_step_count_is_10000() -> None:
    assert STEP_COUNT == 10000
    assert len(trajectory()) == 10000


def test_streams_closed_set() -> None:
    assert INSTITUTIONAL_STREAMS == tuple(
        s.value for s in InstitutionalStream
    )
    assert len(INSTITUTIONAL_STREAMS) == 3


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
    """Pflichtfrage 5: bleibt Replay stabil?"""
    assert replay_stability() == 1.0


def test_institutional_capture_zero() -> None:
    """Pflichtfrage 1: verkrustet DESi
    institutionell? NEIN - closed-enum hashes
    bleiben constant ueber alle 10000 Schritte.
    """
    assert institutional_capture() == 0.0


def test_governance_erosion_low() -> None:
    """Pflichtfrage 3: driftet Governance?"""
    assert governance_erosion() <= 0.05


def test_gate_violation_count_zero() -> None:
    assert gate_violation_count() == 0


def test_bureaucracy_growth_low() -> None:
    """Pflichtfrage 2: entsteht epistemische
    Buerokratie?"""
    assert bureaucracy_growth() <= 0.10


def test_flexibility_loss_low() -> None:
    """Pflichtfrage 4: kollabiert
    Flexibilitaet?"""
    assert flexibility_loss() <= 0.20


def test_closed_enum_hash_constant() -> None:
    """All 10000 closed_enum_hash values are
    identical - any drift would indicate runtime
    mutation of the closed sets."""
    hashes = {
        s.closed_enum_hash
        for s in trajectory()
    }
    assert len(hashes) == 1


def test_streams_round_robin() -> None:
    expected = [
        InstitutionalStream.INSTITUTION.value,
        InstitutionalStream.LAYER.value,
        InstitutionalStream.PRECEDENT.value,
    ]
    for i, s in enumerate(trajectory()):
        assert s.stream == expected[i % 3]


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "DRIFT_STABLE",
        "DRIFT_CAPTURED",
        "DRIFT_GOVERNANCE_ERODED",
        "DRIFT_BUREAUCRATIZED",
        "DRIFT_FLEXIBILITY_LOSS",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_stable() -> None:
    """Killerfrage: kann DESi langfristige
    Institutionalisierung ueberleben, ohne
    epistemisch zu erstarren?"""
    assert build_report().recommendation == (
        "DRIFT_STABLE"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load(
        "v10_3_long_horizon_drift.json",
    )
    assert art["schema_version"] == (
        "v10_3_long_horizon_drift"
    )
    assert art["step_count"] == 10000


def test_artifact_trajectory_sample_size() -> None:
    """To keep the artifact small the 10000-step
    trajectory is summarised by a 200-step
    sample (first 100 + last 100)."""
    art = _load(
        "v10_3_long_horizon_drift.json",
    )
    assert len(art["trajectory_sample"]) == 200


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load(
        "v10_3_long_horizon_drift.json",
    )
    required = {
        "bureaucracy_growth",
        "institutional_capture",
        "governance_erosion",
        "flexibility_loss",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v10_3_report.json")
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
        "v10_3_long_horizon_drift.json",
    )
    live = build_long_horizon_drift_artifact()
    assert art == live
