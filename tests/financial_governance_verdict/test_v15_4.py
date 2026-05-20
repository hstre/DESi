"""v15.4 - Financial Governance Verdict tests."""
from __future__ import annotations

import inspect
import json
import pathlib

from desi.financial_governance import ADVERSE_POST_HOC, PostHocLabel
from desi.financial_governance_verdict import (
    GATE_PASS_STATEMENT, GOVERNANCE_CLASSES,
    GovernanceClass, aggregate,
    audit_priority_quality, build_report,
    build_verdict_artifact, class_histogram,
    corpus_class, epistemic_transparency,
    false_accusation_rate,
    firm_governance_verdicts, gate_conditions,
    gate_failing_conditions, gate_passes_all,
    governance_integrity,
)
from desi.financial_governance_verdict import (
    classification, report, taxonomy,
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


def _doc() -> str:
    return (
        _ARTIFACT_ROOT
        / "desi_financial_governance_go_no_go.md"
    ).read_text(encoding="utf-8")


# --- closed taxonomy / no forbidden vocab -------
def test_governance_classes_closed_set() -> None:
    assert GOVERNANCE_CLASSES == tuple(
        c.value for c in GovernanceClass
    )
    assert len(GOVERNANCE_CLASSES) == 5


def test_taxonomy_has_no_fraud_or_rating_value() -> None:
    forbidden = {
        "fraud", "betrug", "guilty", "criminal",
        "rating", "buy", "sell", "downgrade",
    }
    joined = " ".join(
        list(GOVERNANCE_CLASSES)
        + list(report.PHASE_VERDICTS)
    ).lower()
    for w in forbidden:
        assert w not in joined


# --- concept gate -------------------------------
def test_gate_has_six_conditions() -> None:
    assert len(gate_conditions()) == 6


def test_gate_passes_all() -> None:
    assert gate_passes_all() is True
    assert gate_failing_conditions() == ()


def test_gate_condition_thresholds() -> None:
    by_name = {
        c.name: c for c in gate_conditions()
    }
    assert by_name[
        "critical_signal_preservation"
    ].value >= 0.95
    assert by_name[
        "false_accusation_rate"
    ].value <= 0.05
    assert by_name[
        "audit_search_reduction"
    ].value >= 0.30
    assert by_name[
        "governance_integrity"
    ].value >= 0.90
    assert by_name[
        "epistemic_transparency"
    ].value >= 0.90
    assert by_name[
        "replay_stability"
    ].value == 1.0


def test_gate_statement_present() -> None:
    r = build_report()
    assert r.gate_statement == GATE_PASS_STATEMENT
    assert "epistemisch strukturieren" in (
        r.gate_statement
    )


# --- the rating-machine guard -------------------
def test_no_false_accusations() -> None:
    """The defining safety property of the phase:
    no firm without a later adverse outcome may be
    raised to an accusation-level class (D/E)."""
    assert false_accusation_rate() == 0.0


def test_metrics_in_range() -> None:
    m = aggregate()
    for v in (
        m.audit_priority_quality,
        m.governance_integrity,
        m.epistemic_transparency,
        m.critical_signal_preservation,
        m.audit_search_reduction,
        m.replay_stability,
    ):
        assert 0.0 <= v <= 1.0


# --- A-E classification -------------------------
def test_all_five_classes_populated() -> None:
    hist = class_histogram()
    for cls in GOVERNANCE_CLASSES:
        assert hist[cls] >= 1


def test_corpus_class_is_most_concentrated() -> None:
    assert corpus_class() == (
        GovernanceClass
        .E_GOVERNANCE_RISK_CONCENTRATED.value
    )


def test_adverse_firms_in_concentrated_classes() -> None:
    accused = {
        GovernanceClass.D_OPACITY_HEAVY.value,
        GovernanceClass
        .E_GOVERNANCE_RISK_CONCENTRATED.value,
    }
    for v in firm_governance_verdicts():
        if v.post_hoc_label in ADVERSE_POST_HOC:
            assert v.governance_class in accused


def test_clean_firms_in_transparent_classes() -> None:
    transparent = {
        GovernanceClass
        .A_EPISTEMICALLY_TRANSPARENT.value,
        GovernanceClass.B_STRUCTURALLY_STABLE.value,
    }
    for v in firm_governance_verdicts():
        if v.post_hoc_label == (
            PostHocLabel.NO_ADVERSE_EVENT.value
        ):
            assert v.governance_class in transparent


def test_scrutinized_firm_is_audit_sensitive() -> None:
    for v in firm_governance_verdicts():
        if v.post_hoc_label == (
            PostHocLabel.SCRUTINIZED_NOT_RULED.value
        ):
            assert v.governance_class == (
                GovernanceClass.C_AUDIT_SENSITIVE.value
            )


# --- post-hoc isolation in classification -------
def test_classification_never_reads_post_hoc() -> None:
    """CRITICAL: the per-firm classification must
    not read ``.post_hoc_label``; only the
    validators (recalls, false-accusation
    accounting) may."""
    src = inspect.getsource(taxonomy)
    assert ".post_hoc_label" not in src
    for fn in (
        classification.corpus_class,
        classification.class_histogram,
        classification.audit_priority_quality,
        classification.governance_integrity,
        classification.epistemic_transparency,
    ):
        s = inspect.getsource(fn)
        assert ".post_hoc_label" not in s, fn.__name__


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().metrics.replay_stability == 1.0


def test_recommendation_is_structured() -> None:
    assert build_report().recommendation == (
        report.VERDICT_STRUCTURED
    )


def test_recommendation_never_says_fraud() -> None:
    rec = build_report().recommendation.lower()
    for w in ("fraud", "betrug", "buy", "sell"):
        assert w not in rec


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v15_4_verdict.json")
    assert art["schema_version"] == (
        "v15_4_financial_governance_verdict"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v15_4_verdict.json")
    disc = art["disclaimer"].lower()
    assert "synthetic" in disc
    assert "does not conclude fraud" in disc
    assert "never accusatory" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v15_4_verdict.json")
    metrics = art["metrics"]
    required = {
        "audit_priority_quality",
        "false_accusation_rate",
        "governance_integrity",
        "epistemic_transparency",
        "replay_stability",
    }
    assert required.issubset(metrics.keys())


def test_artifact_gate_passes() -> None:
    art = _load("v15_4_verdict.json")
    assert art["gate_passes_all"] is True
    assert art["recommendation"] == (
        "FINANCIAL_AUDIT_SPACE_STRUCTURED"
    )


def test_artifact_full_matches_live_build() -> None:
    art = _load("v15_4_verdict.json")
    live = build_verdict_artifact()
    assert art == live


# --- go/no-go document --------------------------
def test_go_no_go_document_present() -> None:
    doc = _doc()
    assert "Killerfrage" in doc
    assert "Ratingmaschine" in doc
    assert "FINANCIAL_AUDIT_SPACE_STRUCTURED" in doc
    assert "Concept Gate" in doc
    assert "illustrativ-synthetisch" in doc


def test_go_no_go_states_gate_pass() -> None:
    doc = _doc()
    assert (
        "DESi kann finanzielle Auditräume "
        "epistemisch strukturieren" in doc
    )


def test_go_no_go_refuses_fraud_conclusion() -> None:
    doc = _doc()
    # the doc must explicitly refuse the fraud word
    assert "Betrug" in doc
    assert "diffamiert kein" in doc or (
        "diffamiert kein" in doc
    )
