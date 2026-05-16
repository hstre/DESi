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


def test_v46_w3_modality_check_is_safe() -> None:
    """W3 is safe under any later runtime — the safety
    invariant (zero contamination on the protected pool) is
    a property of the predicate. After v4.7 the rescue count
    drops to 0 (the cases W3 used to catch are now suspended
    upstream) but the predicate remains safe."""
    cases, classes = _bundle()
    per_probe, _ = analyse(cases, classes)
    w3 = next(
        p for p in per_probe
        if p.probe == WarrantProbe.W3_MODALITY_CONSISTENCY_CHECK.value
    )
    assert w3.contamination_risk == 0
    assert w3.unsafe is False


def test_v46_historical_w3_rescue_pinned_in_frozen_artifact() -> None:
    """At v4.6 time W3 rescued 10/19 cases. Later patches
    (v4.7) absorb those cases, so the live rescue count drops.
    We pin the v4.6-era rescue count via the frozen file."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_6" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    w3 = next(
        r for r in data["probe_rescue"]
        if r["probe"] == WarrantProbe.W3_MODALITY_CONSISTENCY_CHECK.value
    )
    assert w3["rescued_cases"] == 10
    assert w3["contamination_risk"] == 0


def test_v46_historical_majority_rescue_clusters_pinned() -> None:
    """At v4.6 time the majority rescue clusters were
    CORRELATION_TO_CAUSATION + SAMPLE_TO_UNIVERSAL. After
    v4.7 those clusters are gone from the live residue."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_6" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    assert (
        "CORRELATION_TO_CAUSATION"
        in data["agreement"]["majority_rescue_clusters"]
    )
    assert (
        "SAMPLE_TO_UNIVERSAL"
        in data["agreement"]["majority_rescue_clusters"]
    )
    assert (
        "MISSING_BRIDGE_RULE"
        not in data["agreement"]["majority_rescue_clusters"]
    )
