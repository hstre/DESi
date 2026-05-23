"""v15.0 - Financial Structure Audit (DAX
retrospective) tests."""
from __future__ import annotations

import inspect
import json
import pathlib

from desi.financial_governance import (
    ADVERSE_POST_HOC, AUDIT_PRIORITIES,
    AuditPriority, PostHocLabel,
    bridge_validity, build_report,
    build_structure_artifact, cashflow_alignment,
    clean_firm_low_priority_rate,
    corpus_priority_label,
    ex_ante_structure_recall, firm_verdicts,
    firms, narrative_consistency,
    opacity_detection, sectors, years,
)
from desi.financial_governance import bridges
from desi.financial_governance import cashflow
from desi.financial_governance import governance
from desi.financial_governance import narratives


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


# --- closed-vocabulary / safety invariants ------
def test_audit_priorities_closed_set() -> None:
    assert AUDIT_PRIORITIES == tuple(
        p.value for p in AuditPriority
    )
    assert len(AUDIT_PRIORITIES) == 5


def test_audit_priority_values_are_directive() -> None:
    assert set(AUDIT_PRIORITIES) == {
        "LOW_AUDIT_PRIORITY",
        "MEDIUM_AUDIT_PRIORITY",
        "HIGH_AUDIT_PRIORITY",
        "GOVERNANCE_REVIEW_RECOMMENDED",
        "UNRESOLVED",
    }


def test_no_fraud_or_rating_value_in_vocab() -> None:
    """The closed verdict vocabulary must contain
    no fraud / Betrug / rating / buy-sell value."""
    forbidden = {
        "fraud", "betrug", "guilty", "criminal",
        "buy", "sell", "rating", "downgrade",
        "upgrade",
    }
    joined = " ".join(AUDIT_PRIORITIES).lower()
    for word in forbidden:
        assert word not in joined


# --- corpus shape (directive minimums) ----------
def test_at_least_ten_years() -> None:
    assert len(years()) >= 10


def test_multiple_sectors() -> None:
    assert len(sectors()) >= 3


def test_crisis_and_non_crisis_firms() -> None:
    labels = {f.post_hoc_label for f in firms()}
    # at least one later-adverse firm ...
    assert labels & ADVERSE_POST_HOC
    # ... and at least one clean firm.
    assert (
        PostHocLabel.NO_ADVERSE_EVENT.value
        in labels
    )


def test_all_figures_marked_synthetic() -> None:
    for f in firms():
        for y in f.years:
            assert y.is_synthetic_illustrative


# --- metric ranges ------------------------------
def test_pflichtmetriken_in_unit_interval() -> None:
    for m in (
        cashflow_alignment(),
        narrative_consistency(),
        opacity_detection(),
        bridge_validity(),
    ):
        assert 0.0 <= m <= 1.0


def test_opacity_detected_above_zero() -> None:
    assert opacity_detection() > 0.0


# --- the central ex-ante validation -------------
def test_ex_ante_structure_recall_full() -> None:
    """Killerfrage: every later-adverse firm was
    flagged elevated using ONLY ex-ante structure."""
    assert ex_ante_structure_recall() == 1.0


def test_clean_firms_not_swept_up() -> None:
    """No-false-accusation guard: every firm with
    no later adverse outcome stays LOW priority."""
    assert clean_firm_low_priority_rate() == 1.0


def test_adverse_firms_flagged_elevated() -> None:
    elevated = {
        AuditPriority.MEDIUM_AUDIT_PRIORITY.value,
        AuditPriority.HIGH_AUDIT_PRIORITY.value,
        AuditPriority
        .GOVERNANCE_REVIEW_RECOMMENDED.value,
    }
    for v in firm_verdicts():
        if v.post_hoc_label in ADVERSE_POST_HOC:
            assert v.priority_label in elevated


def test_clean_firms_low() -> None:
    for v in firm_verdicts():
        if v.post_hoc_label == (
            PostHocLabel.NO_ADVERSE_EVENT.value
        ):
            assert v.priority_label == (
                AuditPriority
                .LOW_AUDIT_PRIORITY.value
            )


def test_voided_firm_outranks_governance_event() -> None:
    """Monotonicity: the later-voided firm must
    rank at least as severe as the governance-event
    firm, which ranks above the clean firms."""
    by_id = {
        v.firm_id: v for v in firm_verdicts()
    }
    voided = by_id["PAYMENTS_ALPHA"]
    govt = by_id["AUTO_BETA"]
    clean = by_id["CHEM_GAMMA"]
    assert (
        governance.severity_rank(
            voided.priority_label,
        )
        >= governance.severity_rank(
            govt.priority_label,
        )
    )
    assert (
        govt.priority_score > clean.priority_score
    )
    assert (
        voided.priority_score > govt.priority_score
    )


# --- the post-hoc isolation invariant -----------
def test_scoring_functions_never_read_post_hoc() -> None:
    """CRITICAL: no ex-ante structure-scoring
    function may READ ``.post_hoc_label``. The
    post-hoc label is validation-only; only the
    validators in governance.py may read it."""
    scoring_modules = [
        cashflow, narratives, bridges,
    ]
    for mod in scoring_modules:
        src = inspect.getsource(mod)
        assert ".post_hoc_label" not in src, (
            mod.__name__
        )
    # In governance.py, only the two validators may
    # read the post-hoc attribute; the per-firm
    # signal and scoring functions must not.
    for fn in (
        governance.firm_signals,
        governance.firm_priority_score,
        governance.firm_priority_label,
    ):
        src = inspect.getsource(fn)
        assert ".post_hoc_label" not in src, (
            fn.__name__
        )


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(AUDIT_PRIORITIES)
    )


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
    art = _load("v15_0_structure.json")
    assert art["schema_version"] == (
        "v15_0_financial_structure_audit"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v15_0_structure.json")
    disc = art["disclaimer"].lower()
    assert "synthetic" in disc
    assert "not real audited" in disc
    assert "does not conclude fraud" in disc
    assert "not named real companies" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v15_0_structure.json")
    required = {
        "cashflow_alignment",
        "narrative_consistency",
        "opacity_detection",
        "bridge_validity",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v15_0_structure.json")
    live = build_structure_artifact()
    assert art == live
