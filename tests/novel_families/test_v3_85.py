"""v3.85 — novel family isolation tests."""
from __future__ import annotations

import json
import pathlib

from desi.novel_families.isolation import (
    all_novel_families,
    pairwise_family_separations,
)
from desi.novel_families.report import (
    build_novel_claim_families_artifact,
    build_report,
)
from desi.novel_families.select import (
    FORBIDDEN_ANCHORS, NOVEL_FAMILY_SPECS,
    all_family_members, all_novel_anchors,
    family_members,
)


def test_four_family_specs() -> None:
    """Directive § v3.85: at least 4 new families."""
    assert len(NOVEL_FAMILY_SPECS) == 4


def test_family_ids_unique() -> None:
    ids = [s.family_id for s in NOVEL_FAMILY_SPECS]
    assert len(set(ids)) == len(ids)


def test_each_family_has_three_or_more_anchors() -> None:
    """Directive § v3.85: each family ≥ 3 anchors."""
    for spec in NOVEL_FAMILY_SPECS:
        assert len(family_members(spec)) >= 3


def test_no_member_in_forbidden_pool() -> None:
    """Killerfrage: wirklich neues epistemisches
    Material? Every selected anchor must lie
    outside the prior-sprint pool."""
    for members in all_family_members().values():
        for m in members:
            assert m not in FORBIDDEN_ANCHORS


def test_overlap_with_prior_is_zero() -> None:
    """Stop rule: overlap_with_prior > 0 ⇒
    sprint invalid."""
    assert build_report().overlap_with_prior == 0


def test_family_count_metric() -> None:
    assert build_report().family_count == 4


def test_anchor_count_matches_sum_of_members() -> None:
    r = build_report()
    total = sum(
        len(m) for m in all_family_members().values()
    )
    assert r.anchor_count == total


def test_family_variance_positive() -> None:
    """Pflichtfrage 2: Haben sie genug Varianz?
    Mean across families must be > 0."""
    assert build_report().family_variance > 0.0


def test_each_family_isolated_object_matches_spec() -> None:
    fams = {f.family_id: f for f in all_novel_families()}
    for spec in NOVEL_FAMILY_SPECS:
        f = fams[spec.family_id]
        assert f.corpus == spec.corpus
        assert f.letter == spec.letter
        assert f.overlap_with_prior == 0
        assert f.anchor_count == len(f.members)


def test_pairwise_separations_present() -> None:
    """4 families → C(4,2) = 6 pairwise distances."""
    seps = pairwise_family_separations()
    assert len(seps) == 6


def test_pairwise_separations_mean_non_trivial() -> None:
    """Pflichtfrage 3: separable. Mean distance
    must be > 0 for every cross-family pair."""
    for s in pairwise_family_separations():
        assert s.mean_distance > 0.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_isolated() -> None:
    assert build_report().recommendation == (
        "NOVEL_FAMILIES_ISOLATED"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "NOVEL_FAMILIES_ISOLATED",
        "NOVEL_FAMILIES_DEGENERATE",
        "SPRINT_INVALID_OVERLAP",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_lists_specs_and_families() -> None:
    art = build_novel_claim_families_artifact()
    assert len(art["family_specs"]) == 4
    assert len(art["families"]) == 4
    assert art["family_count"] == 4
    assert art["anchor_count"] == sum(
        len(m) for m in all_family_members().values()
    )


def test_novel_anchors_disjoint_from_forbidden() -> None:
    novel = set(all_novel_anchors())
    assert novel.isdisjoint(FORBIDDEN_ANCHORS)


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_85" / "report.json").read_text(
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
