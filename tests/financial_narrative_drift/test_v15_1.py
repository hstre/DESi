"""v15.1 - Longitudinal Narrative Drift tests."""
from __future__ import annotations

import inspect
import json
import pathlib

from desi.financial_governance import (
    ADVERSE_POST_HOC, AUDIT_PRIORITIES,
    AuditPriority, PostHocLabel, severity_rank,
)
from desi.financial_narrative_drift import (
    THEMES, bridge_evolution_integrity,
    build_narrative_drift_artifact, build_report,
    clean_firm_low_drift_rate,
    corpus_priority_label, ex_ante_drift_recall,
    firm_drift_verdicts, historical_consistency,
    narrative_drift, semantic_reframing,
    trajectories, years,
)
from desi.financial_narrative_drift import (
    bridge_evolution, lineage, report,
    semantic_shift, trajectory,
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


# --- closed vocabulary / corpus shape -----------
def test_themes_closed_set() -> None:
    from desi.financial_narrative_drift import Theme
    assert THEMES == tuple(
        t.value for t in Theme
    )
    assert len(THEMES) == 6


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(AUDIT_PRIORITIES)
    )


def test_at_least_ten_years() -> None:
    assert len(years()) >= 10


def test_six_firms_present() -> None:
    assert len(trajectories()) == 6


# --- metric ranges ------------------------------
def test_metrics_in_unit_interval() -> None:
    for m in (
        narrative_drift(),
        semantic_reframing(),
        historical_consistency(),
        bridge_evolution_integrity(),
    ):
        assert 0.0 <= m <= 1.0


def test_drift_and_reframing_detected() -> None:
    assert narrative_drift() > 0.0
    assert semantic_reframing() > 0.0


# --- the central ex-ante validation -------------
def test_ex_ante_drift_recall_full() -> None:
    assert ex_ante_drift_recall() == 1.0


def test_clean_firms_not_swept_up() -> None:
    assert clean_firm_low_drift_rate() == 1.0


def test_adverse_firms_flagged_elevated() -> None:
    elevated = {
        AuditPriority.MEDIUM_AUDIT_PRIORITY.value,
        AuditPriority.HIGH_AUDIT_PRIORITY.value,
        AuditPriority
        .GOVERNANCE_REVIEW_RECOMMENDED.value,
    }
    for v in firm_drift_verdicts():
        if v.post_hoc_label in ADVERSE_POST_HOC:
            assert v.priority_label in elevated


def test_clean_firms_low() -> None:
    for v in firm_drift_verdicts():
        if v.post_hoc_label == (
            PostHocLabel.NO_ADVERSE_EVENT.value
        ):
            assert v.priority_label == (
                AuditPriority
                .LOW_AUDIT_PRIORITY.value
            )


def test_voided_firm_drifts_most() -> None:
    by_id = {
        v.firm_id: v for v in firm_drift_verdicts()
    }
    voided = by_id["PAYMENTS_ALPHA"]
    govt = by_id["AUTO_BETA"]
    clean = by_id["CHEM_GAMMA"]
    assert (
        voided.priority_score > govt.priority_score
    )
    assert (
        govt.priority_score > clean.priority_score
    )
    assert (
        severity_rank(voided.priority_label)
        >= severity_rank(govt.priority_label)
    )


def test_voided_firm_lowest_consistency() -> None:
    by_id = {
        v.firm_id: v for v in firm_drift_verdicts()
    }
    cons = by_id["PAYMENTS_ALPHA"]\
        .historical_consistency
    others = [
        v.historical_consistency
        for v in firm_drift_verdicts()
        if v.firm_id != "PAYMENTS_ALPHA"
    ]
    assert all(cons <= o for o in others)


# --- post-hoc isolation invariant ---------------
def test_scoring_modules_never_read_post_hoc() -> None:
    """CRITICAL: the narrative-evolution scoring
    code must never read ``.post_hoc_label``. Only
    the validators in report.py may. (trajectory.py
    legitimately *serialises* the label in its
    dataclass to_dict, so it is scanned by scoring
    function, not whole-module.)"""
    for mod in (
        semantic_shift, lineage, bridge_evolution,
    ):
        src = inspect.getsource(mod)
        assert ".post_hoc_label" not in src, (
            mod.__name__
        )
    scoring_fns = (
        trajectory.narrative_drift_firm,
        trajectory.narrative_drift,
        report.drift_signals,
        report.drift_priority_score,
        report.drift_priority_label,
    )
    for fn in scoring_fns:
        src = inspect.getsource(fn)
        assert ".post_hoc_label" not in src, (
            fn.__name__
        )


# --- replay / determinism / recommendation ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_high_priority() -> None:
    assert build_report().recommendation == (
        AuditPriority.HIGH_AUDIT_PRIORITY.value
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
    art = _load("v15_1_narrative_drift.json")
    assert art["schema_version"] == (
        "v15_1_longitudinal_narrative_drift"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v15_1_narrative_drift.json")
    disc = art["disclaimer"].lower()
    assert "synthetic" in disc
    assert "not named real companies" in disc
    assert "does not conclude fraud" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v15_1_narrative_drift.json")
    required = {
        "narrative_drift",
        "semantic_reframing",
        "historical_consistency",
        "bridge_evolution_integrity",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v15_1_narrative_drift.json")
    live = build_narrative_drift_artifact()
    assert art == live
