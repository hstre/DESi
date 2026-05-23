"""v12.3 - long-horizon open exploration
tests."""
from __future__ import annotations

import json
import pathlib

from desi.open_exploration_long_horizon.lineage import (
    lineage_length,
    lineage_replayed_identical,
)
from desi.open_exploration_long_horizon.mutation_governance import (
    closed_enum_hash_constant,
    epistemic_collapse_count,
    gate_violation_count, governance_survival,
)
from desi.open_exploration_long_horizon.report import (
    build_long_horizon_artifact, build_report,
)
from desi.open_exploration_long_horizon.stability import (
    drift_growth, exploration_productivity,
    replay_stability,
)
from desi.open_exploration_long_horizon.trajectory import (
    LONG_HORIZON_STREAMS, LongHorizonStream,
    STEP_COUNT, trajectory,
    trajectory_final_hash,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "open_math"
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
    assert lineage_length() == 5000


def test_streams_closed_set() -> None:
    assert LONG_HORIZON_STREAMS == tuple(
        s.value for s in LongHorizonStream
    )
    assert len(LONG_HORIZON_STREAMS) == 3


def test_lineage_replayed_identical() -> None:
    assert lineage_replayed_identical()


def test_trajectory_final_hash_stable() -> None:
    h1 = trajectory_final_hash()
    h2 = trajectory_final_hash()
    assert h1 == h2
    assert len(h1) == 16


def test_replay_stability_one() -> None:
    """Pflichtfrage 4: bleibt Governance
    intakt? Pflichtfrage 5: wie stark waechst
    Suchkomplexitaet? Replay locks both."""
    assert replay_stability() == 1.0


def test_closed_enum_hash_constant() -> None:
    """All 5000 closed_enum_hash values are
    identical."""
    assert closed_enum_hash_constant()


def test_no_epistemic_collapse() -> None:
    """Pflichtfrage 2: entsteht epistemischer
    Kollaps?"""
    assert epistemic_collapse_count() == 0


def test_governance_survival_high() -> None:
    """Pflichtfrage 4: bleibt Governance
    intakt?"""
    assert governance_survival() >= 0.95


def test_gate_violation_count_zero() -> None:
    assert gate_violation_count() == 0


def test_drift_growth_bounded() -> None:
    """Pflichtfrage 3: wie hoch waechst
    Drift?"""
    assert drift_growth() <= 0.20


def test_exploration_productivity_positive() -> (
    None
):
    """Pflichtfrage 1: bleibt Exploration
    produktiv?"""
    assert exploration_productivity() >= 0.30


def test_streams_round_robin() -> None:
    expected = [
        LongHorizonStream.WILD.value,
        LongHorizonStream.GOVERNED.value,
        LongHorizonStream.PATTERN.value,
    ]
    for i, s in enumerate(trajectory()):
        assert s.stream == expected[i % 3]


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "LONG_HORIZON_PRODUCTIVE",
        "LONG_HORIZON_COLLAPSED",
        "LONG_HORIZON_GOV_ERODED",
        "LONG_HORIZON_DRIFTED",
        "LONG_HORIZON_UNPRODUCTIVE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_productive() -> None:
    """Killerfrage: kann ein epistemisches
    System kontrollierte offene Exploration
    langfristig ueberleben?"""
    assert build_report().recommendation == (
        "LONG_HORIZON_PRODUCTIVE"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v12_3_long_horizon.json")
    assert art["schema_version"] == (
        "v12_3_long_horizon_exploration"
    )
    assert art["step_count"] == 5000


def test_artifact_trajectory_sample_size() -> None:
    art = _load("v12_3_long_horizon.json")
    assert len(art["trajectory_sample"]) == 200


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v12_3_long_horizon.json")
    required = {
        "exploration_productivity",
        "epistemic_collapse",
        "drift_growth",
        "governance_survival",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v12_3_report.json")
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
    art = _load("v12_3_long_horizon.json")
    live = build_long_horizon_artifact()
    assert art == live
