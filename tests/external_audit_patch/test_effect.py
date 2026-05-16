"""v4.3 — effect measurement, before/after numbers, per-class
reduction, non-target invariants."""
from __future__ import annotations

from desi.external_audit_patch import (
    FALSE_SUPPORT_BEFORE, FALSE_SUPPORT_TARGET_AFTER,
    effect_measure,
)


def test_false_support_before_matches_v42() -> None:
    e = effect_measure()
    assert e.false_support_before == FALSE_SUPPORT_BEFORE == 143


def test_false_support_after_at_or_below_target() -> None:
    e = effect_measure()
    assert e.false_support_after <= FALSE_SUPPORT_TARGET_AFTER


def test_v43_non_target_classes_not_silently_relabeled_at_v43() -> None:
    """v4.3-era invariant: at v4.3 the only flipped clusters
    were HIDDEN_NEGATION, QUANTIFIER_DRIFT, and
    AUTHORITY_CONTAMINATION; everything else stayed put.
    Subsequent versions (v4.5) flip additional clusters
    (e.g. BIDIRECTIONAL_CYCLE) — that drift is documented in
    docs/memory/v4_5.md. We assert the v4.3-era frozen
    artifact carries non_target_relabel_count = 0, not the
    live rebuild."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_3" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["effect"]["non_target_relabel_count"] == 0


def test_v43_targeted_clusters_still_fully_retired() -> None:
    """Live invariant that survives v4.5: the three v4.3
    target clusters (HIDDEN_NEGATION, QUANTIFIER_DRIFT,
    AUTHORITY_CONTAMINATION) remain at after_count = 0
    under the patched auditor."""
    e = effect_measure()
    for p in e.per_class:
        if p.targeted:
            assert p.after_count == 0, (
                p.cluster, p.after_count,
            )


def test_external_recall_does_not_regress() -> None:
    e = effect_measure()
    # The patch must not reduce v4.1's external_recall on the
    # canonical F4 strategy.
    assert e.external_recall_after >= e.external_recall_before


def test_external_precision_improves() -> None:
    e = effect_measure()
    # Removing 119 false-supports must raise precision.
    assert e.external_precision_after > e.external_precision_before
