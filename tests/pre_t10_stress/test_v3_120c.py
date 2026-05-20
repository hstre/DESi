"""v3.120c - stress replay tests.

The full stress runs 10 subprocesses and takes
~45 seconds. Tests load the persisted artifact
to keep regression cost low.
"""
from __future__ import annotations

import json
import pathlib

from desi.pre_t10_stress.historical import (
    adverse_flip_count,
    false_negative_rate_max,
    historical_tpr_max,
    historical_tpr_min,
)
from desi.pre_t10_stress.stress import (
    SEEDS,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "v3_120c"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_seed_count_meets_directive() -> None:
    """Directive § v3.120c: at least 10 seeds."""
    assert len(SEEDS) >= 10


def test_artifact_present() -> None:
    art = _load("report.json")
    assert art["seed_count"] >= 10


def test_artifact_tpr_min_is_one() -> None:
    art = _load("report.json")
    assert art["historical_tpr_min"] == 1.0


def test_artifact_tpr_max_is_one() -> None:
    art = _load("report.json")
    assert art["historical_tpr_max"] == 1.0


def test_artifact_false_negative_zero() -> None:
    art = _load("report.json")
    assert art["false_negative_rate_max"] == 0.0


def test_artifact_no_adverse_flips() -> None:
    """Killerfrage: rettet die Regel weiterhin
    alle echten Faelle? JA - no seed produced a
    false negative."""
    art = _load("report.json")
    assert art["adverse_flip_count"] == 0


def test_artifact_replay_stability_is_one() -> None:
    art = _load("report.json")
    assert art["replay_stability"] == 1.0


def test_artifact_recommendation_in_closed_set() -> None:
    allowed = {
        "STRESS_TPR_STABLE",
        "STRESS_TPR_WEAK",
        "STRESS_TPR_UNSTABLE",
        "HALT_REPLAY_DRIFT",
    }
    art = _load("report.json")
    assert art["recommendation"] in allowed


def test_artifact_recommendation_is_stable() -> None:
    art = _load("report.json")
    assert art["recommendation"] == (
        "STRESS_TPR_STABLE"
    )


def test_artifact_lists_cells() -> None:
    art = _load("report.json")
    assert len(art["stress_cells"]) >= 10


def test_pre_t10_stress_artifact_present() -> None:
    art = _load("pre_t10_stress_replay.json")
    assert (
        art["schema_version"]
        == "v3_120c_pre_t10_stress_replay"
    )
