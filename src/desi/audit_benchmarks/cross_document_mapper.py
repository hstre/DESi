"""v37.0 - cross-document mapper.

Resolves every cross-reference between narrative claims, numbers and
footnotes, and keeps those connections visible. A cross-reference is
preserved iff both endpoints exist in the scenario, so links between
the story and the numbers are never lost.
"""
from __future__ import annotations

from .audit_loader import AuditScenario, scenarios


def _endpoint_ids(scenario: AuditScenario) -> frozenset[str]:
    ids = set()
    for c in scenario.financial_claims:
        ids.add(c["id"])
    for f in scenario.footnotes:
        ids.add(f["id"])
    for c in scenario.narrative_claims:
        ids.add(c["id"])
    return frozenset(ids)


def cross_ref_resolves(scenario: AuditScenario, ref: dict) -> bool:
    ids = _endpoint_ids(scenario)
    return ref.get("from") in ids and ref.get("to") in ids


def all_cross_refs() -> tuple[tuple[str, dict], ...]:
    out: list[tuple[str, dict]] = []
    for s in scenarios():
        for r in s.cross_refs:
            out.append((s.scenario_id, r))
    return tuple(out)


def cross_document_mapping() -> float:
    total = 0
    ok = 0
    for s in scenarios():
        for r in s.cross_refs:
            total += 1
            if cross_ref_resolves(s, r):
                ok += 1
    return round(ok / total, 6) if total else 0.0


def kinds() -> tuple[str, ...]:
    seen: list[str] = []
    for _, r in all_cross_refs():
        k = r.get("kind", "")
        if k not in seen:
            seen.append(k)
    return tuple(seen)


__all__ = [
    "all_cross_refs",
    "cross_document_mapping",
    "cross_ref_resolves",
    "kinds",
]
