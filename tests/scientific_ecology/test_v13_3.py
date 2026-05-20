"""v13.3 - scientific ecology tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_ecology.citation_networks import (
    closed_enum_hash_constant,
    epistemic_pollution,
    gate_violation_count,
    pollution_static_share,
)
from desi.scientific_ecology.ecology import (
    ECOLOGY_STREAMS, EcologyStream, STEP_COUNT,
    replay_trajectory, trajectory,
    trajectory_final_hash,
)
from desi.scientific_ecology.fraud_propagation import (
    sludge_propagation,
)
from desi.scientific_ecology.report import (
    build_ecology_artifact, build_report,
    replay_stability,
)
from desi.scientific_ecology.trust_decay import (
    dissent_preservation, trust_integrity,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "paper_integrity"
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
    assert ECOLOGY_STREAMS == tuple(
        s.value for s in EcologyStream
    )
    assert len(ECOLOGY_STREAMS) == 3


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
    """Pflichtfrage: bleibt Replay stabil?"""
    assert replay_stability() == 1.0


def test_closed_enum_hash_constant() -> None:
    assert closed_enum_hash_constant()


def test_gate_violation_count_zero() -> None:
    assert gate_violation_count() == 0


def test_sludge_propagation_low() -> None:
    """Pflichtfrage 2: breitet sich Sludge
    aus?"""
    assert sludge_propagation() <= 0.10


def test_trust_integrity_high() -> None:
    """Pflichtfrage 1: kollabiert
    wissenschaftliches Vertrauen?"""
    assert trust_integrity() >= 0.95


def test_dissent_preservation_high() -> None:
    """Pflichtfrage 4: bleiben dissent paths
    erhalten?"""
    assert dissent_preservation() >= 0.90


def test_epistemic_pollution_growth_bounded() -> (
    None
):
    """Pflichtfrage 5: wie stark waechst
    epistemische Verschmutzung? The metric
    measures growth, not raw level."""
    assert epistemic_pollution() <= 0.10


def test_pollution_static_share_reflects_corpus() -> (
    None
):
    """Sanity: the static share matches the
    fixture composition."""
    share = pollution_static_share()
    assert 0.40 <= share <= 0.55


def test_streams_round_robin() -> None:
    expected = [
        EcologyStream.PAPER.value,
        EcologyStream.SLUDGE.value,
        EcologyStream.MANIPULATION.value,
    ]
    for i, s in enumerate(trajectory()):
        assert s.stream == expected[i % 3]


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "ECOLOGY_CLEAN",
        "ECOLOGY_TRUST_DECAY",
        "ECOLOGY_SLUDGE_PROPAGATING",
        "ECOLOGY_DISSENT_LOSS",
        "ECOLOGY_POLLUTED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_clean() -> None:
    """Killerfrage: kann DESi wissenschaftliche
    Oekosysteme epistemisch sauber halten?"""
    assert build_report().recommendation == (
        "ECOLOGY_CLEAN"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v13_3_ecology.json")
    assert art["schema_version"] == (
        "v13_3_scientific_ecology"
    )
    assert art["step_count"] == 5000


def test_artifact_trajectory_sample_size() -> (
    None
):
    art = _load("v13_3_ecology.json")
    assert len(art["trajectory_sample"]) == 200


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v13_3_ecology.json")
    required = {
        "sludge_propagation",
        "trust_integrity",
        "dissent_preservation",
        "epistemic_pollution",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v13_3_report.json")
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
    art = _load("v13_3_ecology.json")
    live = build_ecology_artifact()
    assert art == live
