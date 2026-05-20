"""v15.2 - Financial Blindness Pools tests."""
from __future__ import annotations

import inspect
import json
import pathlib

from desi.financial_governance import (
    ADVERSE_POST_HOC, AUDIT_PRIORITIES,
    AuditPriority, PostHocLabel,
)
from desi.financial_blindness import (
    RISK_FAMILIES, RiskFamily,
    blindness_pool_count,
    build_blindness_artifact, build_report,
    clean_firm_sound_rate, corpus_priority_label,
    ex_ante_pool_recall, firm_pool_verdicts,
    multi_member_pools, pools,
    recoverability_signal, risk_family_detection,
    signatures, structural_redundancy,
)
from desi.financial_blindness import (
    clusters, redundancy, report, risk_families,
    trajectory_similarity,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "financial_governance"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- closed vocabulary --------------------------
def test_risk_families_closed_set() -> None:
    assert RISK_FAMILIES == tuple(
        f.value for f in RiskFamily
    )
    assert len(RISK_FAMILIES) == 5


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(AUDIT_PRIORITIES)
    )


# --- pools are epistemic, NOT industry ----------
def test_blindness_pools_found() -> None:
    assert blindness_pool_count() >= 2


def test_clustering_is_not_industry() -> None:
    """The defining property of the sprint: at
    least one pool spans multiple sectors, proving
    the clustering groups by epistemic structure
    rather than by industry."""
    assert any(p.is_cross_sector for p in pools())


def test_multi_member_pool_spans_sectors() -> None:
    multi = multi_member_pools()
    assert multi
    biggest = max(multi, key=lambda p: p.size)
    assert len(set(biggest.sectors)) >= 2


def test_no_pool_is_a_single_sector_block() -> None:
    """No multi-member pool may be just one whole
    sector's firms - that would be industry
    classification, not structure."""
    # every firm in the corpus has a unique sector
    # here, so any multi-member pool is necessarily
    # cross-sector; assert that explicitly.
    for p in multi_member_pools():
        assert len(set(p.sectors)) == p.size


# --- metric ranges ------------------------------
def test_metrics_in_unit_interval() -> None:
    for m in (
        risk_family_detection(),
        structural_redundancy(),
        recoverability_signal(),
    ):
        assert 0.0 <= m <= 1.0


def test_full_risk_taxonomy_detected() -> None:
    assert risk_family_detection() == 1.0


def test_redundancy_and_recoverability_positive() -> None:
    assert structural_redundancy() > 0.0
    assert recoverability_signal() > 0.0


# --- ex-ante validation -------------------------
def test_ex_ante_pool_recall_full() -> None:
    assert ex_ante_pool_recall() == 1.0


def test_clean_firms_sound() -> None:
    assert clean_firm_sound_rate() == 1.0


def test_adverse_firms_in_non_sound_family() -> None:
    for v in firm_pool_verdicts():
        if v.post_hoc_label in ADVERSE_POST_HOC:
            assert RiskFamily\
                .STRUCTURALLY_SOUND.value \
                not in v.risk_families


def test_clean_firms_structurally_sound() -> None:
    for v in firm_pool_verdicts():
        if v.post_hoc_label == (
            PostHocLabel.NO_ADVERSE_EVENT.value
        ):
            assert v.risk_families == (
                RiskFamily
                .STRUCTURALLY_SOUND.value,
            )


def test_voided_firm_widest_blind_spot() -> None:
    by_id = {
        v.firm_id: v for v in firm_pool_verdicts()
    }
    voided = by_id["PAYMENTS_ALPHA"]
    others = [
        v.family_count
        for v in firm_pool_verdicts()
        if v.firm_id != "PAYMENTS_ALPHA"
    ]
    assert all(
        voided.family_count >= o for o in others
    )


# --- post-hoc isolation invariant ---------------
def test_scoring_modules_never_read_post_hoc() -> None:
    """CRITICAL: structure/cluster modules must
    never read ``.post_hoc_label``; only the
    validators in report.py may."""
    for mod in (
        trajectory_similarity, risk_families,
        clusters, redundancy,
    ):
        src = inspect.getsource(mod)
        assert ".post_hoc_label" not in src, (
            mod.__name__
        )
    # The priority decision itself must be
    # post-hoc-free (firm_pool_verdicts only
    # ATTACHES the label for the artifact).
    src = inspect.getsource(
        report.pool_priority_label,
    )
    assert ".post_hoc_label" not in src


# --- replay / determinism / recommendation ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_governance_review() -> None:
    assert build_report().recommendation == (
        AuditPriority
        .GOVERNANCE_REVIEW_RECOMMENDED.value
    )


def test_corpus_label_matches_recommendation() -> None:
    assert (
        build_report().recommendation
        == corpus_priority_label()
    )


def test_recommendation_never_says_fraud() -> None:
    rec = build_report().recommendation.lower()
    for word in ("fraud", "betrug", "buy", "sell"):
        assert word not in rec


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v15_2_blindness.json")
    assert art["schema_version"] == (
        "v15_2_financial_blindness_pools"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v15_2_blindness.json")
    disc = art["disclaimer"].lower()
    assert "synthetic" in disc
    assert "not an industry classification" in disc
    assert "does not conclude fraud" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v15_2_blindness.json")
    required = {
        "blindness_pool_count",
        "risk_family_detection",
        "structural_redundancy",
        "recoverability_signal",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v15_2_blindness.json")
    live = build_blindness_artifact()
    assert art == live
