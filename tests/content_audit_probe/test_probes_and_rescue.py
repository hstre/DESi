"""v4.8 — counterfactual probes + safe-probe coverage."""
from __future__ import annotations

from desi.content_audit_probe import (
    ContentProbe, collect_residue_cases,
    content_probe_evaluate_all,
)
from desi.content_audit_probe.classifier import classify_all
from desi.content_audit_probe.rescue import analyse
from desi.content_audit_probe.replay import replay_all


def _bundle():
    cases = collect_residue_cases()
    records = replay_all(cases)
    text_index = {c.chain_id: c.text for c in cases}
    classes = classify_all(records, text_index)
    return cases, classes


def test_each_probe_evaluated_on_every_case() -> None:
    cases = collect_residue_cases()
    out = content_probe_evaluate_all(cases)
    by_probe: dict[str, list] = {}
    for o in out:
        by_probe.setdefault(o.probe, []).append(o)
    assert len(by_probe) == len(ContentProbe)
    for probe in ContentProbe:
        assert len(by_probe[probe.value]) == len(cases)


def test_c1_contradiction_pair_check_is_safe_and_rescues_dc() -> None:
    cases, classes = _bundle()
    per_probe, _ = analyse(cases, classes)
    c1 = next(
        p for p in per_probe
        if p.probe == ContentProbe.C1_CONTRADICTION_PAIR_CHECK.value
    )
    assert c1.contamination_risk == 0
    assert c1.unsafe is False
    assert c1.rescued_cases == 4


def test_c2_polarity_flip_check_is_safe_and_rescues_pr() -> None:
    cases, classes = _bundle()
    per_probe, _ = analyse(cases, classes)
    c2 = next(
        p for p in per_probe
        if p.probe == ContentProbe.C2_POLARITY_FLIP_CHECK.value
    )
    assert c2.contamination_risk == 0
    assert c2.unsafe is False
    assert c2.rescued_cases == 5


def test_c5_entity_consistency_check_is_unsafe() -> None:
    cases, classes = _bundle()
    per_probe, _ = analyse(cases, classes)
    c5 = next(
        p for p in per_probe
        if p.probe == ContentProbe.C5_ENTITY_CONSISTENCY_CHECK.value
    )
    assert c5.unsafe is True
    assert c5.contamination_risk > 0


def test_majority_rescue_clusters_cover_both_residue_classes() -> None:
    cases, classes = _bundle()
    _, agreement = analyse(cases, classes)
    # Both residue clusters have at least one safe probe
    # rescuing every case (C1 for DC, C2 for PR).
    assert (
        "DIRECT_CONTRADICTION"
        in agreement.majority_rescue_clusters
    )
    assert (
        "PROPERTY_REVERSAL"
        in agreement.majority_rescue_clusters
    )
