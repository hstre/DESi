"""v3.96a - jitter census tests.

The full census is expensive (100 hash seeds plus
20 pytest shuffle iterations); we keep tests cheap
by validating the persisted artifact rather than
re-running the census, and by exercising the
probe surface with a 2-seed mini-run.
"""
from __future__ import annotations

import json
import pathlib

from desi.determinism.jitter import (
    REFERENCE_SEED, SEED_CENSUS,
    affected_packages, run_with_seed,
)
from desi.determinism.seeds import (
    SHUFFLE_SEEDS,
)


_ARTIFACT_ROOT = pathlib.Path(
    __file__,
).resolve().parents[2] / "artifacts" / "v3_96a"


def _load_artifact(name: str) -> dict:
    path = _ARTIFACT_ROOT / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_seed_census_meets_directive_minimum() -> None:
    """Directive § v3.96a: at least 100 hash seeds."""
    assert len(SEED_CENSUS) >= 100


def test_shuffle_seeds_meet_directive_minimum() -> None:
    """Directive § v3.96a: at least 20 shuffled
    test orders."""
    assert len(SHUFFLE_SEEDS) >= 20


def test_reference_seed_is_zero() -> None:
    assert REFERENCE_SEED == 0


def test_run_with_seed_returns_states() -> None:
    """Lightweight probe: one seed run yields a
    non-empty trajectory dict and a zero exit
    code."""
    snap, code = run_with_seed(0)
    assert code == 0
    assert len(snap) > 0


def test_two_seeds_may_differ_on_sample_traj() -> None:
    """The classic mozart trajectory drifts under
    PYTHONHASHSEED; under at least one alternate
    seed the frame_id of state 0 differs from the
    seed-0 baseline."""
    snap_a, _ = run_with_seed(0)
    snap_b, _ = run_with_seed(1)
    a = snap_a.get("sample:n03_mozart")
    b = snap_b.get("sample:n03_mozart")
    assert a is not None and b is not None
    # frame_id is index 0 in each state row.
    diffs = sum(
        1 for sa, sb in zip(a, b)
        if sa[0] != sb[0]
    )
    assert diffs > 0


def test_affected_packages_listed() -> None:
    """Static enumeration in the production
    module; if a future package re-introduces
    hash-based determinism it should be added."""
    pkgs = affected_packages()
    assert "epistemic_trajectory" in pkgs


def test_artifact_present() -> None:
    """The artifact must exist on disk so the
    full census doesn't have to re-run during
    regression."""
    art = _load_artifact("report.json")
    assert art["seed_count"] >= 100


def test_artifact_jitter_rate_in_unit_interval() -> None:
    art = _load_artifact("report.json")
    assert 0.0 <= art["jitter_rate"] <= 1.0


def test_artifact_jittery_includes_sample_trajs() -> None:
    """The persisted census recorded that the
    sample:n03_mozart and sample:n03_darwin
    trajectories drift."""
    art = _load_artifact("report.json")
    jittery = set(art["jittery_trajectory_ids"])
    assert "sample:n03_mozart" in jittery
    assert "sample:n03_darwin" in jittery


def test_artifact_affected_dims_only_frame_id() -> None:
    """The persisted census recorded that only
    frame_id drifts."""
    art = _load_artifact("report.json")
    assert tuple(art["affected_dims"]) == (
        "frame_id",
    )


def test_artifact_recommendation_in_closed_set() -> None:
    allowed = {
        "NO_JITTER_DETECTED",
        "JITTER_CONFIRMED",
        "ORDER_JITTER_ONLY",
        "HALT_REPLAY_DRIFT",
    }
    art = _load_artifact("report.json")
    assert art["recommendation"] in allowed


def test_artifact_replay_stability_is_one() -> None:
    art = _load_artifact("report.json")
    assert art["replay_stability"] == 1.0


def test_jitter_census_artifact_present() -> None:
    art = _load_artifact("jitter_census.json")
    assert (
        art["schema_version"]
        == "v3_96a_jitter_census"
    )
    assert "census" in art
