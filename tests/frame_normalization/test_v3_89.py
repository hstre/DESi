"""v3.89 — frame contribution audit tests."""
from __future__ import annotations

import json
import pathlib

from desi.frame_normalization.contribution import (
    FrameCondition,
    dominant_dim,
    frame_variance_share,
    novel_vectors_frame_only,
    novel_vectors_full,
    novel_vectors_no_frame,
    novel_vectors_residual,
    per_dim_variance,
    total_variance,
    vectors_for_condition,
)
from desi.frame_normalization.report import (
    build_frame_contribution_audit_artifact,
    build_report,
)
from desi.frame_normalization.variance import (
    all_condition_outcomes,
    cluster_purity_for,
)


def test_four_frame_conditions() -> None:
    """Closed enum has exactly the directive's
    four conditions A/B/C/D."""
    vals = {c.value for c in FrameCondition}
    assert vals == {
        "full", "no_frame",
        "frame_only", "residual",
    }


def test_novel_vectors_full_count_is_thirty_eight() -> None:
    assert len(novel_vectors_full()) == 38


def test_no_frame_zeros_frame_slots_only() -> None:
    """In no_frame vectors the frame_id slots must
    all be 0.0; other slots must equal the full
    vector."""
    full = novel_vectors_full()
    nf = novel_vectors_no_frame()
    frame_slots = {0, 9, 18, 27, 36}
    for tid in full:
        for i in range(45):
            if i in frame_slots:
                assert nf[tid][i] == 0.0
            else:
                assert nf[tid][i] == full[tid][i]


def test_frame_only_keeps_frame_slots_only() -> None:
    full = novel_vectors_full()
    fo = novel_vectors_frame_only()
    frame_slots = {0, 9, 18, 27, 36}
    for tid in full:
        for i in range(45):
            if i in frame_slots:
                assert fo[tid][i] == full[tid][i]
            else:
                assert fo[tid][i] == 0.0


def test_residual_zeros_frame_slots() -> None:
    res = novel_vectors_residual()
    frame_slots = {0, 9, 18, 27, 36}
    for tid in res:
        for i in frame_slots:
            assert res[tid][i] == 0.0


def test_residual_centered_per_cell() -> None:
    """After per-cell regression on frame_id, the
    column mean for every non-frame slot must be
    close to zero."""
    res = novel_vectors_residual()
    frame_slots = {0, 9, 18, 27, 36}
    ids = sorted(res)
    for i in range(45):
        if i in frame_slots:
            continue
        col = [res[tid][i] for tid in ids]
        mean = sum(col) / len(col)
        assert abs(mean) < 1e-3


def test_frame_variance_share_in_unit_interval() -> None:
    fvs = frame_variance_share()
    assert 0.0 <= fvs <= 1.0


def test_frame_is_dominant_dim() -> None:
    """Killerfrage: ist frame_id wirklich der
    dominante Verzerrer?"""
    assert dominant_dim() == "frame_id"


def test_frame_variance_share_above_half() -> None:
    """For the directive's verdict
    FRAME_IS_DOMINANT_NOISE the share must be at
    least 0.5."""
    assert frame_variance_share() >= 0.5


def test_purity_no_frame_beats_full() -> None:
    """Concept Gate condition #1:
    purity_no_frame > purity_full."""
    full = cluster_purity_for(
        FrameCondition.FULL.value,
    )
    nf = cluster_purity_for(
        FrameCondition.NO_FRAME.value,
    )
    assert nf > full


def test_purity_residual_at_least_no_frame() -> None:
    nf = cluster_purity_for(
        FrameCondition.NO_FRAME.value,
    )
    res = cluster_purity_for(
        FrameCondition.RESIDUAL.value,
    )
    assert res >= nf - 1e-9


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "FRAME_IS_DOMINANT_NOISE",
        "FRAME_IS_PARTIAL_NOISE",
        "FRAME_IS_NOT_NOISE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_per_dim_variance_sums_to_total() -> None:
    pdv = per_dim_variance()
    s = sum(pdv.values())
    assert abs(s - total_variance()) < 1e-6


def test_artifact_lists_four_conditions() -> None:
    art = build_frame_contribution_audit_artifact()
    assert len(art["condition_outcomes"]) == 4


def test_vectors_for_condition_dispatch() -> None:
    assert (
        vectors_for_condition("full")
        == novel_vectors_full()
    )
    assert (
        vectors_for_condition("no_frame")
        == novel_vectors_no_frame()
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_89" / "report.json").read_text(
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
