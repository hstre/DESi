"""v3.117 - state blindness census tests."""
from __future__ import annotations

import json
import pathlib

from desi.state_blindness.census import (
    all_blindness_pools,
    cross_family_pools,
    state_signature,
)
from desi.state_blindness.detect import (
    affected_family_count,
    blindness_pool_count,
    largest_pool_size,
    mean_pool_size,
    total_blind_anchor_count,
    total_pool_count,
)
from desi.state_blindness.report import (
    build_report,
    build_state_blindness_census_artifact,
)


def test_state_signature_deterministic() -> None:
    from desi.epistemic_trajectory.extractor import (
        extract_all_trajectories,
    )
    trajs = {
        t.trajectory_id: t
        for t in extract_all_trajectories()
    }
    a = state_signature(trajs["v314:A01"])
    b = state_signature(trajs["v314:A01"])
    assert a == b


def test_blindness_pool_count_at_least_ten() -> None:
    """Killerfrage: ist der 10-Familien-Fall
    einzigartig? Nein - the corpus contains
    dozens of cross-family blindness pools."""
    assert blindness_pool_count() >= 10


def test_largest_pool_dominates() -> None:
    """The biggest cross-family collapse covers
    a large fraction of the corpus."""
    assert largest_pool_size() >= 50


def test_affected_family_count_high() -> None:
    """Most families are involved in at least
    one blindness pool."""
    assert affected_family_count() >= 10


def test_mean_pool_size_above_two() -> None:
    assert mean_pool_size() > 2.0


def test_total_blind_anchors_above_half() -> None:
    """More than half of trajectories live in a
    cross-family pool."""
    from desi.epistemic_trajectory.extractor import (
        extract_all_trajectories,
    )
    total = len(list(extract_all_trajectories()))
    assert total_blind_anchor_count() > total / 2


def test_pools_all_cross_family() -> None:
    """``cross_family_pools`` returns only the
    pools whose member set spans 2+ families."""
    for p in cross_family_pools():
        assert p.family_count >= 2


def test_total_pool_count_at_least_blindness() -> None:
    """Total pools (including same-family) is
    at least as big as cross-family pools."""
    assert total_pool_count() >= (
        blindness_pool_count()
    )


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "BLINDNESS_PERVASIVE",
        "BLINDNESS_LOCAL",
        "NO_BLINDNESS",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_pervasive() -> None:
    assert build_report().recommendation == (
        "BLINDNESS_PERVASIVE"
    )


def test_artifact_lists_all_pools() -> None:
    art = build_state_blindness_census_artifact()
    assert len(art["pools"]) == (
        blindness_pool_count()
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_117" / "report.json").read_text(
            encoding="utf-8",
        )
    )
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
