"""README/System-Paper self-review tests.

Verifies the audit is hard and honest: it returns NO-GO, surfaces the
specific overreach / staleness / scanner findings, and never asserts
that DESi validates itself.
"""
from __future__ import annotations

import json
import pathlib

from desi.readme_self_review import (
    CLAIM_STATUSES, artifact_backing_rate, build_claim_audit_artifact,
    build_go_no_go, build_overreach_report, build_revision_suggestions,
    claims, external_generalization_guard, forbidden_term_hits,
    forbidden_term_risk, gate_conditions, gate_failing_conditions,
    gate_passes_all, overreach_claims, recommendation,
    replay_explanation_correct, reviewer_port_module_present,
    stale_regression_runs, synthetic_vs_real_separation,
    unsupported_numeric_claims,
)
from desi.readme_self_review.report import (
    VERDICT_NOT_READY,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "readme_self_review"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


def _read(name: str) -> str:
    return (_ARTIFACT_ROOT / name).read_text(encoding="utf-8")


# --- claim extraction ---------------------------
def test_claims_use_closed_status_set() -> None:
    cs = claims()
    assert len(cs) >= 20
    for c in cs:
        assert c.verdict in CLAIM_STATUSES


def test_each_claim_has_full_schema() -> None:
    for c in claims():
        d = c.to_dict()
        for k in ("claim_id", "claim_text", "claim_type",
                  "evidence_source", "artifact_support",
                  "risk_level", "verdict", "recommended_action"):
            assert d[k], (c.claim_id, k)


# --- hard, skeptical outcome --------------------
def test_review_is_no_go() -> None:
    assert gate_passes_all() is False
    assert recommendation() == VERDICT_NOT_READY


def test_failing_conditions_are_the_expected_four() -> None:
    failing = set(gate_failing_conditions())
    assert "unsupported_numeric_claims" in failing
    assert "artifact_backing_rate" in failing
    assert "overreach_claims" in failing
    assert "forbidden_term_risk" in failing


def test_passing_conditions_are_real_strengths() -> None:
    assert synthetic_vs_real_separation() == 1.0
    assert external_generalization_guard() == 1.0
    assert replay_explanation_correct() == 1.0


# --- specific findings --------------------------
def test_forbidden_terms_detected_in_readme() -> None:
    assert forbidden_term_risk() == len(forbidden_term_hits())
    assert forbidden_term_risk() >= 1
    assert "AGI" in forbidden_term_hits()


def test_stale_regression_runs_flagged() -> None:
    stale = stale_regression_runs()
    assert any("7573" in s for s in stale)
    assert any("7683" in s for s in stale)


def test_overreach_flagged() -> None:
    assert overreach_claims() >= 1
    blob = json.dumps([c.to_dict() for c in claims()])
    assert "epistemic operating system" in blob
    assert "LangSmith" in blob


def test_reviewer_port_module_absent() -> None:
    assert reviewer_port_module_present() is False


def test_unsupported_numeric_nonzero() -> None:
    assert unsupported_numeric_claims() >= 1


def test_artifact_backing_below_ceiling() -> None:
    assert artifact_backing_rate() < 0.95


# --- safety rule: no self-validation ------------
def test_no_self_validation_assertion() -> None:
    for name in (
        "desi_readme_overreach_report.md",
        "desi_readme_revision_suggestions.md",
        "desi_readme_go_no_go.md",
    ):
        text = _read(name)
        assert "internal consistency and overreach audit" in text
        # never the bald self-validation claim
        assert "DESi validates itself" not in text


def test_go_no_go_has_safety_statement() -> None:
    doc = _read("desi_readme_go_no_go.md")
    assert "DESi did not validate itself" in doc
    assert "Human approval remains required" in doc


# --- artifacts present --------------------------
def test_four_deliverables_present() -> None:
    for name in (
        "desi_readme_claim_audit.json",
        "desi_readme_overreach_report.md",
        "desi_readme_revision_suggestions.md",
        "desi_readme_go_no_go.md",
    ):
        assert (_ARTIFACT_ROOT / name).exists()


def test_claim_audit_artifact_shape() -> None:
    art = _load("desi_readme_claim_audit.json")
    assert art["schema_version"] == "readme_self_review_claim_audit"
    assert art["gate_passes_all"] is False
    assert art["reviewed_snapshot_sha256"]
    assert len(art["claims"]) >= 20
    assert len(art["gate_conditions"]) == 7


def test_claim_audit_records_scanner_facts() -> None:
    art = _load("desi_readme_claim_audit.json")
    sf = art["scanner_facts"]
    assert sf["forbidden_term_hits"]
    assert sf["reviewer_port_module_present"] is False
    assert sf["stale_regression_runs_omitted_by_readme"]


def test_claim_audit_full_matches_live_build() -> None:
    art = _load("desi_readme_claim_audit.json")
    assert art == build_claim_audit_artifact()


def test_reports_match_live_build() -> None:
    assert _read("desi_readme_overreach_report.md") == (
        build_overreach_report()
    )
    assert _read("desi_readme_revision_suggestions.md") == (
        build_revision_suggestions()
    )
    assert _read("desi_readme_go_no_go.md") == build_go_no_go()


def test_gate_conditions_count() -> None:
    assert len(gate_conditions()) == 7
