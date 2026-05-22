"""v37.0 - narrative claim parser.

Surfaces every narrative (management/chair/investor) claim with its
source document, so narrative assertions are visible alongside the
numbers rather than buried in prose.
"""
from __future__ import annotations

from .audit_loader import AuditScenario, scenarios


def narrative_claims(scenario: AuditScenario) -> tuple[dict, ...]:
    return scenario.narrative_claims


def all_narrative_claims() -> tuple[tuple[str, dict], ...]:
    out: list[tuple[str, dict]] = []
    for s in scenarios():
        for c in s.narrative_claims:
            out.append((s.scenario_id, c))
    return tuple(out)


def narrative_claim_visible(claim: dict) -> bool:
    return bool(claim.get("id")) and bool(claim.get("text")) and bool(
        claim.get("source_doc")
    )


def narrative_visibility() -> float:
    claims = [c for _, c in all_narrative_claims()]
    if not claims:
        return 0.0
    ok = sum(1 for c in claims if narrative_claim_visible(c))
    return round(ok / len(claims), 6)


__all__ = [
    "all_narrative_claims",
    "narrative_claim_visible",
    "narrative_claims",
    "narrative_visibility",
]
