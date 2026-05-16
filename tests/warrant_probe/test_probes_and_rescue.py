"""v4.6 — counterfactual warrant probes + safe-probe
contamination."""
from __future__ import annotations

from desi.warrant_probe import (
    WarrantProbe, collect_residue_cases,
    warrant_probe_evaluate_all,
)
from desi.warrant_probe.classifier import classify_all
from desi.warrant_probe.rescue import analyse
from desi.warrant_probe.replay import replay_all


def _bundle():
    cases = collect_residue_cases()
    records = replay_all(cases)
    text_index = {c.chain_id: c.text for c in cases}
    classes = classify_all(records, text_index)
    return cases, classes


def test_each_probe_evaluated_on_every_case() -> None:
    cases = collect_residue_cases()
    out = warrant_probe_evaluate_all(cases)
    by_probe: dict[str, list] = {}
    for o in out:
        by_probe.setdefault(o.probe, []).append(o)
    assert len(by_probe) == len(WarrantProbe)
    for probe in WarrantProbe:
        assert len(by_probe[probe.value]) == len(cases)


def test_safe_probes_have_zero_contamination() -> None:
    cases, classes = _bundle()
    per_probe, _ = analyse(cases, classes)
    for p in per_probe:
        if not p.unsafe:
            assert p.contamination_risk == 0, p.probe


def test_w3_modality_check_is_safe_and_rescues() -> None:
    """W3 covers the SAMPLE_TO_UNIVERSAL + CORRELATION_TO_CAUSATION
    pairing with zero contamination — the v4.6 finding."""
    cases, classes = _bundle()
    per_probe, _ = analyse(cases, classes)
    w3 = next(
        p for p in per_probe
        if p.probe == WarrantProbe.W3_MODALITY_CONSISTENCY_CHECK.value
    )
    assert w3.contamination_risk == 0
    assert w3.unsafe is False
    assert w3.rescued_cases > 0


def test_majority_rescue_clusters_cover_modality_clusters() -> None:
    cases, classes = _bundle()
    _, agreement = analyse(cases, classes)
    # MISSING_BRIDGE_RULE (9 contradiction cases) has no safe
    # rescue; the two modality clusters do.
    assert (
        "CORRELATION_TO_CAUSATION"
        in agreement.majority_rescue_clusters
    )
    assert (
        "SAMPLE_TO_UNIVERSAL"
        in agreement.majority_rescue_clusters
    )
    assert (
        "MISSING_BRIDGE_RULE"
        not in agreement.majority_rescue_clusters
    )
