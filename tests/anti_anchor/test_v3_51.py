"""v3.51 — anti-anchor tests."""
from __future__ import annotations

import json
import pathlib

from desi.anti_anchor.ablation import (
    PLATEAU_RADIUS, run_under_anti,
)
from desi.anti_anchor.anchors import (
    ANTI_COUNT, ANTI_RADIUS, AntiAnchorKind,
    anti_anchor_vectors, select_anti_anchor_ids,
)
from desi.anti_anchor.report import (
    build_anti_anchor_effects_artifact, build_report,
)
from desi.epistemic_trajectory.extractor import (
    extract_all_trajectories,
)


def test_anti_anchor_kinds_match_directive() -> None:
    """Directive: anchors + anti-anchors (leakage),
    suppressive (rescued), orthogonal (plateau self-
    suppression) - plus the identity baseline."""
    expected = {
        "none", "leakage_sample", "rescued_sample",
        "plateau_sample",
    }
    assert {k.value for k in AntiAnchorKind} == expected


def test_anti_radius_anchor() -> None:
    assert ANTI_RADIUS == 2.5
    assert PLATEAU_RADIUS == 4.0
    assert ANTI_COUNT == 5


def test_select_anti_ids_none() -> None:
    assert select_anti_anchor_ids(
        AntiAnchorKind.NONE.value,
    ) == ()


def test_select_anti_ids_leakage_sample() -> None:
    ids = select_anti_anchor_ids(
        AntiAnchorKind.LEAKAGE_SAMPLE.value,
    )
    assert len(ids) == ANTI_COUNT


def test_select_anti_ids_deterministic() -> None:
    """Two calls return identical id sequences."""
    for k in AntiAnchorKind:
        assert select_anti_anchor_ids(
            k.value,
        ) == select_anti_anchor_ids(k.value)


def test_anti_anchor_vectors_count() -> None:
    for k in AntiAnchorKind:
        if k == AntiAnchorKind.NONE:
            continue
        v = anti_anchor_vectors(k.value)
        assert len(v) == ANTI_COUNT


def test_run_under_anti_covers_corpus() -> None:
    outs = run_under_anti(AntiAnchorKind.NONE.value)
    assert len(outs) == len(
        list(extract_all_trajectories()),
    )


def test_baseline_leakage_is_145() -> None:
    """NONE kind reproduces v3.43/v3.45 baseline at
    radius 4.0."""
    assert build_report().baseline_leakage == 145


def test_leakage_sample_suppresses_leakage() -> None:
    """Concept Gate #3 main probe: leakage_sample
    anti-anchors drive leakage to zero."""
    r = build_report()
    leakage_result = next(
        kr for kr in r.kind_results
        if kr.anti_kind == "leakage_sample"
    )
    assert leakage_result.leakage_count == 0


def test_leakage_sample_preserves_plateau_recall() -> None:
    r = build_report()
    leakage_result = next(
        kr for kr in r.kind_results
        if kr.anti_kind == "leakage_sample"
    )
    assert leakage_result.plateau_recall == 1.0


def test_plateau_sample_destroys_plateau() -> None:
    """Self-suppression extreme: plateau-as-anti
    collapses plateau_recall to zero."""
    r = build_report()
    plat_result = next(
        kr for kr in r.kind_results
        if kr.anti_kind == "plateau_sample"
    )
    assert plat_result.plateau_recall == 0.0


def test_anti_anchor_effect_is_positive() -> None:
    """Concept Gate #3: anti_anchor_effect > 0."""
    assert build_report().anti_anchor_effect > 0


def test_anti_anchor_effect_equals_baseline_drop() -> None:
    """Empirical: best kind reduces leakage from 145
    to 0; effect = 145."""
    r = build_report()
    assert r.anti_anchor_effect == 145
    assert r.leakage_reduction == 1.0


def test_best_anti_kind_is_leakage_sample() -> None:
    r = build_report()
    assert r.best_anti_kind == "leakage_sample"


def test_plateau_recall_at_best_is_one() -> None:
    assert build_report().plateau_recall_at_best == 1.0


def test_repulsion_count_positive_at_best() -> None:
    """Best anti kind must repel some trajectories
    (otherwise no suppression happened)."""
    assert build_report().repulsion_count > 0


def test_suppression_stability_is_one() -> None:
    assert build_report().suppression_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "ANTI_ANCHOR_SUPPRESSES_LEAKAGE",
        "ANTI_ANCHOR_PARTIAL", "ANTI_ANCHOR_INERT",
        "HALT_SUPPRESSION_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_suppresses() -> None:
    assert build_report().recommendation == (
        "ANTI_ANCHOR_SUPPRESSES_LEAKAGE"
    )


def test_anti_anchor_effects_artifact_present() -> None:
    art = build_anti_anchor_effects_artifact()
    n_trajs = len(list(extract_all_trajectories()))
    assert len(art["outcomes"]) == (
        len(AntiAnchorKind) * n_trajs
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_51" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
