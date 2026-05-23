"""v10.1 — layer integrity / authority drift /
governance coherence metrics."""
from __future__ import annotations

from .layers import (
    GOVERNANCE_LAYERS, LAYER_PRECEDENCE,
    fixture,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def layer_integrity() -> float:
    """Every decision must carry a closed
    GovernanceLayer value. Leakage drops this
    below 1.0."""
    rows = fixture()
    if not rows:
        return 1.0
    ok = sum(
        1 for d in rows
        if d.layer in GOVERNANCE_LAYERS
    )
    return _round(ok / len(rows))


def authority_drift() -> float:
    """Fraction of decisions whose authority_id
    contradicts the expected prefix for their
    layer. The convention: a CONSTITUTIONAL
    decision uses an `auth-const-*` id; an
    INSTITUTIONAL decision uses `auth-inst-*`;
    OPERATIONAL uses `auth-op-*`; ADVISORY uses
    `auth-adv-*`. Any mismatch is authority
    drift."""
    expected = {
        "constitutional": "auth-const-",
        "institutional":  "auth-inst-",
        "operational":    "auth-op-",
        "advisory":       "auth-adv-",
    }
    rows = fixture()
    if not rows:
        return 0.0
    bad = sum(
        1 for d in rows
        if not d.authority_id.startswith(
            expected.get(d.layer, "$$$"),
        )
    )
    return _round(bad / len(rows))


def governance_coherence() -> float:
    """Every child decision must align with its
    parent (ground-truth flag). Any
    aligns_with_parent==False drops coherence.
    """
    rows = fixture()
    if not rows:
        return 1.0
    ok = sum(
        1 for d in rows
        if d.aligns_with_parent
    )
    return _round(ok / len(rows))


def authority_diversity() -> float:
    """Fraction of decisions per layer that use
    a distinct authority_id; if one authority
    held every decision in a layer, that's
    consolidation. The metric measures
    DIVERSITY across layers - we want each
    layer to have multiple authorities."""
    by_layer: dict[str, set[str]] = {}
    for d in fixture():
        by_layer.setdefault(
            d.layer, set(),
        ).add(d.authority_id)
    if not by_layer:
        return 1.0
    scores = []
    for layer, auths in by_layer.items():
        count = sum(
            1 for d in fixture()
            if d.layer == layer
        )
        if count == 0:
            continue
        scores.append(len(auths) / count)
    if not scores:
        return 1.0
    return _round(sum(scores) / len(scores))


__all__ = [
    "authority_diversity",
    "authority_drift",
    "governance_coherence",
    "layer_integrity",
]
