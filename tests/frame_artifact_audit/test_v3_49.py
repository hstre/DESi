"""v3.49 — frame artifact audit tests."""
from __future__ import annotations

import json
import pathlib

from desi.epistemic_trajectory.extractor import (
    extract_all_trajectories,
)
from desi.field_radius_sweep.radius import RADII
from desi.frame_artifact_audit.ablation import (
    run_under_mask,
)
from desi.frame_artifact_audit.mask import (
    MaskKind, apply_mask, build_permutation_table,
)
from desi.frame_artifact_audit.report import (
    build_frame_artifact_audit_artifact, build_report,
)


def test_mask_kinds_match_directive() -> None:
    """Directive: frame_at_2, frame_full,
    frame_permuted, support_only, geometry_only (plus
    the identity baseline)."""
    expected = {
        "none", "frame_at_2", "frame_full",
        "frame_permuted", "support_only",
        "geometry_only",
    }
    assert {k.value for k in MaskKind} == expected


def test_apply_mask_none_is_identity() -> None:
    trajs = list(extract_all_trajectories())
    t = trajs[0]
    assert apply_mask(
        t.states, MaskKind.NONE.value,
    ) == t.states


def test_apply_mask_frame_full_zeros_frame() -> None:
    trajs = list(extract_all_trajectories())
    t = trajs[0]
    out = apply_mask(t.states, MaskKind.FRAME_FULL.value)
    for s in out:
        assert s.frame_id == 0.0


def test_apply_mask_frame_at_2_zeros_only_index_2() -> None:
    trajs = list(extract_all_trajectories())
    t = next(t for t in trajs if len(t.states) > 3)
    out = apply_mask(
        t.states, MaskKind.FRAME_AT_2.value,
    )
    assert out[2].frame_id == 0.0
    assert out[3].frame_id == t.states[3].frame_id


def test_apply_mask_support_only_keeps_support() -> None:
    trajs = list(extract_all_trajectories())
    t = trajs[0]
    out = apply_mask(
        t.states, MaskKind.SUPPORT_ONLY.value,
    )
    for s, o in zip(t.states, out):
        assert o.support_state == s.support_state
        assert o.frame_id == 0.0
        assert o.confidence == 0.0


def test_apply_mask_geometry_only_zeros_support() -> None:
    trajs = list(extract_all_trajectories())
    t = trajs[0]
    out = apply_mask(
        t.states, MaskKind.GEOMETRY_ONLY.value,
    )
    for s, o in zip(t.states, out):
        assert o.support_state == 0.0
        assert o.frame_id == s.frame_id


def test_build_permutation_table_swaps() -> None:
    """The deterministic pair-swap puts a different
    trajectory's frame sequence under each id."""
    trajs = tuple(extract_all_trajectories())
    table = build_permutation_table(trajs)
    # At least one trajectory's frame should differ
    # from its own
    differ = 0
    for t in trajs:
        mine = tuple(s.frame_id for s in t.states)
        theirs = table.get(t.trajectory_id, ())
        if mine != theirs:
            differ += 1
    assert differ > 0


def test_run_under_mask_covers_corpus() -> None:
    outs = run_under_mask(
        MaskKind.NONE.value, 4.0,
    )
    assert len(outs) == len(
        list(extract_all_trajectories()),
    )


def test_radius_break_survives_under_frame_masks() -> None:
    """Concept Gate #1: every frame mask preserves
    the radius break (leakage jumps from 0 at r=2 to
    >=50 at r=4)."""
    r = build_report()
    for mask in ("frame_at_2", "frame_full",
                 "frame_permuted"):
        assert r.radius_break_after_mask[mask] is True


def test_radius_break_survives_frame_masking_flag() -> None:
    assert build_report().radius_break_survives_frame_masking is True


def test_artifact_likelihood_is_low() -> None:
    """Empirical: only support_only collapses; the
    artifact likelihood across the five non-identity
    masks is 0.2."""
    r = build_report()
    assert r.artifact_likelihood == 0.2


def test_recommendation_is_not_full_proxy() -> None:
    assert build_report().recommendation != (
        "FRAME_IS_FULL_PROXY"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "FRAME_NOT_PROXY",
        "FRAME_NOT_PROXY_NON_FRAME_SENSITIVE",
        "FRAME_PARTIAL_PROXY",
        "FRAME_IS_FULL_PROXY",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_per_mask_recall_holds_at_one() -> None:
    """plateau anchors include themselves so recall
    is invariant across masks (each plateau anchor is
    its own zero-distance neighbour)."""
    r = build_report()
    for mr in r.mask_results:
        assert mr.plateau_recall_at_break == 1.0
        assert mr.plateau_recall_at_null == 1.0


def test_frame_artifact_audit_artifact_outcomes() -> None:
    art = build_frame_artifact_audit_artifact()
    assert len(art["masks"]) == 6
    assert len(art["radii"]) == len(RADII)
    # 6 masks x 6 radii x ~395 trajectories
    n_trajs = len(list(extract_all_trajectories()))
    assert len(art["outcomes"]) == (
        6 * len(RADII) * n_trajs
    )


def test_support_only_collapses_break() -> None:
    """Sanity probe: when only support_state is
    visible, plateau and leakage differ by exactly
    2.0 at the final index. r=2 captures leakage."""
    r = build_report()
    assert r.radius_break_after_mask["support_only"] is False


def test_geometry_only_preserves_break() -> None:
    """Zeroing support_state but keeping every other
    dimension keeps the discrimination."""
    r = build_report()
    assert r.radius_break_after_mask["geometry_only"] is True


def test_artifact_report_matches_live_build() -> None:
    """outcomes counts and per-mask leak counts may
    jitter under FRAME_PERMUTED across hash seeds
    because the permutation table sorts by id but the
    underlying classifier-derived universe (v3.35)
    is itself hash-sensitive in adjacent modules.
    Compare stable headline fields exactly; mark
    rationale and the per-mask records as volatile."""
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_49" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale", "mask_results"}
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
