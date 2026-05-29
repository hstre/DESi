"""Tests for the deterministic paper auditor (offline)."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "utility_evolution" / "paper_audit"))

import audit as A  # noqa: E402


def _checks(issues):
    return {i.check for i in issues}


def test_numeric_consistency_flags_disagreeing_ranges():
    doc = ("# P\n\nWe report compression of 41–60% here.\n\n"
           "## Results\nThe compression of 42–50% is achievable.\n")
    issues = A.check_numeric_consistency(doc)
    assert any(i.check == "numeric_consistency" and i.severity == "high" for i in issues)


def test_numeric_consistency_silent_when_consistent():
    doc = "compression of 42–50% in the abstract.\n\ncompression of 42–50% in results.\n"
    assert A.check_numeric_consistency(doc) == []


def test_duplicate_paragraphs_detected():
    p = ("The reviewer port maps the structure of the epistemic space that emerged including "
         "attractors drift vectors evidence gaps and recoverability contours across the system.")
    doc = f"# T\n\n{p}\n\nUnrelated filler sentence about something entirely different here.\n\n{p}\n"
    issues = A.check_duplicate_paragraphs(doc)
    assert any(i.check == "duplicate_paragraphs" for i in issues)


def test_structure_tables_out_of_order():
    doc = "See Table 2 for the taxonomy.\n\nLater, Table 1 summarizes domains.\n"
    issues = A.check_structure_tables(doc)
    assert any("order" in i.quote.lower() for i in issues)


def test_traceability_contradiction():
    doc = ("All numerical claims are derived from artifact JSON files.\n\n"
           "Seven claims are documented in the companion SSRN paper rather than traceable to artifacts here.\n")
    issues = A.check_traceability(doc)
    assert any(i.check == "traceability" and i.severity == "high" for i in issues)


def test_overclaim_terms_and_universal_claim():
    doc = "This is a breakthrough.\n\nAll 17 phases achieved Class A verdicts.\n"
    issues = A.check_overclaim_terms(doc)
    assert any(i.severity == "low" for i in issues)       # 'breakthrough'
    assert any(i.severity == "medium" for i in issues)    # universal 'all 17 ... achieved'


def test_audit_is_deterministic_and_sorted():
    doc = ("All numerical claims are derived from artifacts.\n\n"
           "compression 41–60%.\n\ncompression 42–50%.\n\n"
           "rather than traceable to artifacts in the companion paper.\n")
    a = A.audit(doc)
    b = A.audit(doc)
    assert [(i.severity, i.check, i.line) for i in a] == [(i.severity, i.check, i.line) for i in b]
    sev = [A.SEVERITY_ORDER[i.severity] for i in a]
    assert sev == sorted(sev)


def test_dogfood_readme_if_present():
    readme = _REPO / "README.md"
    if not readme.exists():
        return
    issues = A.audit(readme.read_text(encoding="utf-8"))
    # the paper's known compression-range inconsistency must surface
    assert any(i.check == "numeric_consistency" for i in issues)
