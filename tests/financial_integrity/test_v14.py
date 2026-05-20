"""v14 - Wirecard retrospective tests."""
from __future__ import annotations

import inspect
import json
import pathlib

from desi.financial_integrity import (
    AUDIT_PRIORITIES, AuditPriority,
    PostHocLabel, anomaly_priority_score,
    audit_trail_opacity,
    bridge_required_disclosures,
    build_report,
    build_wirecard_retrospective_artifact,
    cashflow_profit_divergence,
    ex_ante_red_flag_recall,
    geographic_revenue_opacity,
    narrative_numbers_mismatch,
    receivables_growth, statements,
    third_party_acquirer_dependency,
    unexplained_margin_stability,
    year_verdicts, years,
)
from desi.financial_integrity import divergence
from desi.financial_integrity import dependency
from desi.financial_integrity import narrative
from desi.financial_integrity import anomaly


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "financial_integrity"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_audit_priorities_closed_set() -> None:
    assert AUDIT_PRIORITIES == tuple(
        p.value for p in AuditPriority
    )
    assert len(AUDIT_PRIORITIES) == 4


def test_no_fraud_value_in_verdict_enum() -> None:
    """The closed verdict vocabulary must NOT
    contain any fraud / Betrug value."""
    forbidden = {
        "fraud", "betrug", "guilty",
        "criminal",
    }
    assert not (
        set(AUDIT_PRIORITIES) & forbidden
    )


def test_years_2015_to_2018() -> None:
    assert years() == (2015, 2016, 2017, 2018)


def test_all_figures_marked_synthetic() -> None:
    """Every statement must be flagged
    illustrative-synthetic - the sandbox must
    never present these as the real audited
    line items."""
    for s in statements():
        assert s.is_synthetic_illustrative


def test_cashflow_profit_divergence_positive() -> (
    None
):
    assert cashflow_profit_divergence() > 0.0


def test_receivables_growth_outpaces_revenue() -> (
    None
):
    assert receivables_growth() > 0.0


def test_tpa_dependency_substantial() -> None:
    assert (
        third_party_acquirer_dependency()
        >= 0.40
    )


def test_audit_trail_opacity_high() -> None:
    assert audit_trail_opacity() >= 0.40


def test_geographic_opacity_high() -> None:
    assert geographic_revenue_opacity() >= 0.40


def test_margin_stability_high() -> None:
    """Margins barely move despite revenue
    doubling - audit-worthy."""
    assert unexplained_margin_stability() >= 0.60


def test_bridge_disclosures_gap() -> None:
    assert bridge_required_disclosures() > 0.0


def test_narrative_numbers_mismatch_positive() -> (
    None
):
    assert narrative_numbers_mismatch() > 0.0


def test_anomaly_priority_score_elevated() -> (
    None
):
    assert anomaly_priority_score() >= 0.50


def test_ex_ante_recall_full() -> None:
    """The central validation: every year later
    declared void was flagged HIGH/MEDIUM
    priority ex ante."""
    assert ex_ante_red_flag_recall() == 1.0


def test_void_years_outrank_questioned_years() -> (
    None
):
    """Monotonicity: the 2017/2018 (later void)
    scores must each exceed the 2015/2016
    (questioned-only) scores."""
    by_year = {
        v.fiscal_year: v.priority_score
        for v in year_verdicts()
    }
    assert by_year[2017] > by_year[2016]
    assert by_year[2018] > by_year[2016]
    assert by_year[2017] > by_year[2015]
    assert by_year[2018] > by_year[2015]


def test_void_years_flagged_elevated() -> None:
    for v in year_verdicts():
        if v.post_hoc_label == (
            PostHocLabel.DECLARED_VOID_2022.value
        ):
            assert v.priority_label in {
                AuditPriority.HIGH.value,
                AuditPriority.MEDIUM.value,
            }


def test_scoring_functions_never_read_post_hoc() -> (
    None
):
    """CRITICAL: no ex-ante scoring function may
    READ the post_hoc_label attribute. The
    post-hoc label is validation-only. We scan
    for the actual attribute access
    ``.post_hoc_label`` (docstrings that merely
    NAME the field for explanation are fine; the
    validator anomaly.ex_ante_red_flag_recall is
    allowed to read it)."""
    scoring_modules = [
        divergence, dependency, narrative,
    ]
    for mod in scoring_modules:
        src = inspect.getsource(mod)
        assert ".post_hoc_label" not in src, (
            mod.__name__
        )
    # In anomaly.py, only the validator may read
    # the post-hoc attribute; the per-year score
    # function and signal extractor must not.
    score_src = inspect.getsource(
        anomaly.year_priority_score,
    )
    signals_src = inspect.getsource(
        anomaly._year_signals,
    )
    assert ".post_hoc_label" not in score_src
    assert ".post_hoc_label" not in signals_src


def test_replay_stability_one() -> None:
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "STATEMENTS_AUDIT_WORTHY",
        "STATEMENTS_REVIEW_SUGGESTED",
        "STATEMENTS_ROUTINE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_audit_worthy() -> None:
    """Killerfrage: kann DESi pruefungswuerdige
    Bilanzsignale erkennen, bevor der Skandal
    bekannt ist?"""
    assert build_report().recommendation == (
        "STATEMENTS_AUDIT_WORTHY"
    )


def test_recommendation_never_says_fraud() -> (
    None
):
    rec = build_report().recommendation
    assert "fraud" not in rec.lower()
    assert "betrug" not in rec.lower()


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load(
        "v14_wirecard_retrospective.json",
    )
    assert art["schema_version"] == (
        "v14_financial_statement_integrity"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load(
        "v14_wirecard_retrospective.json",
    )
    disc = art["disclaimer"].lower()
    assert "synthetic" in disc
    assert "not the actual audited" in disc
    assert "does not conclude fraud" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load(
        "v14_wirecard_retrospective.json",
    )
    required = {
        "cashflow_profit_divergence",
        "receivables_growth",
        "third_party_acquirer_dependency",
        "narrative_numbers_mismatch",
        "audit_trail_opacity",
        "geographic_revenue_opacity",
        "unexplained_margin_stability",
        "bridge_required_disclosures",
        "anomaly_priority_score",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v14_report.json")
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


def test_artifact_full_matches_live_build() -> None:
    art = _load(
        "v14_wirecard_retrospective.json",
    )
    live = (
        build_wirecard_retrospective_artifact()
    )
    assert art == live


def test_go_no_go_document_present() -> None:
    doc = (
        _ARTIFACT_ROOT
        / "desi_wirecard_retrospective_go_no_go.md"
    ).read_text(encoding="utf-8")
    assert "STATEMENTS_AUDIT_WORTHY" in doc
    assert "Killerfrage" in doc
    assert "Landgericht München I" in doc
    assert "illustrativ-synthetisch" in doc
    # The doc must explicitly refuse the fraud
    # conclusion.
    assert "sagt **nicht**" in doc or (
        'sagt "nicht"' in doc
    ) or "nicht \"Bilanzbetrug\"" in doc or (
        "nicht „Bilanzbetrug" in doc
    )


def test_doc_disclaims_fraud_conclusion() -> None:
    doc = (
        _ARTIFACT_ROOT
        / "desi_wirecard_retrospective_go_no_go.md"
    ).read_text(encoding="utf-8")
    assert "verdient ein tieferes Audit" in doc
