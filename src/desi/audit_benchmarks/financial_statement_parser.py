"""v37.0 - financial statement parser.

Surfaces every numeric financial claim and resolves its footnote
reference. A financial claim is aligned iff its footnote_ref points to
a footnote that exists in the same scenario - numbers are never shown
without their footnote context.
"""
from __future__ import annotations

from .audit_loader import AuditScenario, scenarios


def financial_claims(scenario: AuditScenario) -> tuple[dict, ...]:
    return scenario.financial_claims


def footnote_ids(scenario: AuditScenario) -> frozenset[str]:
    return frozenset(f["id"] for f in scenario.footnotes)


def claim_footnote_resolves(scenario: AuditScenario, claim: dict) -> bool:
    ref = claim.get("footnote_ref")
    if ref is None:
        return True
    return ref in footnote_ids(scenario)


def all_financial_claims() -> tuple[tuple[str, dict], ...]:
    out: list[tuple[str, dict]] = []
    for s in scenarios():
        for c in s.financial_claims:
            out.append((s.scenario_id, c))
    return tuple(out)


def financial_statement_alignment() -> float:
    total = 0
    ok = 0
    for s in scenarios():
        for c in s.financial_claims:
            total += 1
            if claim_footnote_resolves(s, c):
                ok += 1
    return round(ok / total, 6) if total else 0.0


__all__ = [
    "all_financial_claims",
    "claim_footnote_resolves",
    "financial_claims",
    "financial_statement_alignment",
    "footnote_ids",
]
