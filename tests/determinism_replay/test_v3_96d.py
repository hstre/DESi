"""v3.96d - historical replay audit tests.

The audit runs 125 subprocesses (25 sprints x 5
seeds); we keep tests cheap by reading the
persisted artifact rather than rebuilding it.
"""
from __future__ import annotations

import json
import pathlib

from desi.determinism_replay.historical import (
    HISTORICAL_SPRINTS, sprints_by_family,
)
from desi.determinism_replay.replay import (
    REPLAY_SEEDS, total_replay_count,
)


_ARTIFACT_ROOT = pathlib.Path(
    __file__,
).resolve().parents[2] / "artifacts" / "v3_96d"


def _load_artifact(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_historical_sprint_count_at_least_twenty() -> None:
    """The directive's 50-replay floor is met by
    >= 10 sprints x 5 seeds = 50; we cover 25
    sprints to ensure all six families are
    represented."""
    assert len(HISTORICAL_SPRINTS) >= 20


def test_replay_seeds_at_least_five() -> None:
    assert len(REPLAY_SEEDS) >= 5


def test_total_replay_count_meets_directive_minimum() -> None:
    """Directive § v3.96d: at least 50 replays."""
    assert total_replay_count() >= 50


def test_all_six_families_represented() -> None:
    fams = set(sprints_by_family().keys())
    expected = {
        "mozart", "neptun", "doppelganger",
        "novel_family", "frame_normalization",
        "entangled",
    }
    assert expected.issubset(fams)


def test_module_paths_are_unique() -> None:
    paths = [
        s.module_path for s in HISTORICAL_SPRINTS
    ]
    assert len(set(paths)) == len(paths)


def test_artifact_present() -> None:
    art = _load_artifact("report.json")
    assert (
        art["sprint_count"]
        >= len(HISTORICAL_SPRINTS)
    )


def test_artifact_historical_replay_match_is_one() -> None:
    """Killerfrage: post-patch, every registered
    sprint's report.json digest must agree across
    every seed."""
    art = _load_artifact("report.json")
    assert art["historical_replay_match"] == 1.0


def test_artifact_no_unstable_sprints() -> None:
    art = _load_artifact("report.json")
    assert art["unstable_sprint_ids"] == []


def test_artifact_seed_invariance_is_one() -> None:
    art = _load_artifact("report.json")
    assert art["seed_invariance"] == 1.0


def test_artifact_gate_flip_count_is_zero() -> None:
    art = _load_artifact("report.json")
    assert art["gate_flip_count"] == 0


def test_artifact_metric_delta_is_zero() -> None:
    art = _load_artifact("report.json")
    assert art["metric_delta"] == 0.0


def test_artifact_replay_stability_is_one() -> None:
    art = _load_artifact("report.json")
    assert art["replay_stability"] == 1.0


def test_artifact_recommendation_in_closed_set() -> None:
    allowed = {
        "HISTORICAL_REPLAY_INVARIANT",
        "HISTORICAL_REPLAY_MOSTLY_STABLE",
        "HISTORICAL_REPLAY_BROKEN",
        "HALT_REPLAY_DRIFT",
    }
    art = _load_artifact("report.json")
    assert art["recommendation"] in allowed


def test_artifact_recommendation_is_invariant() -> None:
    art = _load_artifact("report.json")
    assert art["recommendation"] == (
        "HISTORICAL_REPLAY_INVARIANT"
    )


def test_historical_replay_artifact_present() -> None:
    art = _load_artifact(
        "historical_replay_audit.json",
    )
    assert (
        art["schema_version"]
        == "v3_96d_historical_replay_audit"
    )
    assert (
        len(art["outcomes"])
        == len(HISTORICAL_SPRINTS)
    )
