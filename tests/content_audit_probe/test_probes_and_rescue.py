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
    if cases:
        assert len(by_probe) == len(ContentProbe)
        for probe in ContentProbe:
            assert len(by_probe[probe.value]) == len(cases)
    else:
        # After v4.9 the live residue is empty; evaluate_all
        # returns no outcomes.
        assert by_probe == {}


def test_c5_entity_consistency_check_is_unsafe() -> None:
    """Probe contamination is computed against the protected
    pool independently of the live residue; C5 remains
    unsafe after v4.9."""
    cases, classes = _bundle()
    per_probe, _ = analyse(cases, classes)
    c5 = next(
        p for p in per_probe
        if p.probe == ContentProbe.C5_ENTITY_CONSISTENCY_CHECK.value
    )
    assert c5.unsafe is True
    assert c5.contamination_risk > 0


def test_v48_c1_c2_rescue_pinned_in_frozen_artifact() -> None:
    """At v4.8 time C1 rescued 4 / C2 rescued 5, both with
    contamination 0. After v4.9 the live residue is empty so
    rescue counts go to zero, but the contamination invariant
    (zero) is unchanged. We pin the v4.8-era rescue counts
    via the frozen artifact."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_8" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    by_probe = {
        r["probe"]: r for r in data["probe_rescue"]
    }
    c1 = by_probe[
        ContentProbe.C1_CONTRADICTION_PAIR_CHECK.value
    ]
    c2 = by_probe[
        ContentProbe.C2_POLARITY_FLIP_CHECK.value
    ]
    assert c1["rescued_cases"] == 4
    assert c1["contamination_risk"] == 0
    assert c2["rescued_cases"] == 5
    assert c2["contamination_risk"] == 0


def test_v48_majority_rescue_clusters_pinned() -> None:
    """At v4.8 time both clusters were majority-rescue. After
    v4.9 the live residue is empty; we pin via the frozen
    artifact."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_8" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    assert (
        "DIRECT_CONTRADICTION"
        in data["agreement"]["majority_rescue_clusters"]
    )
    assert (
        "PROPERTY_REVERSAL"
        in data["agreement"]["majority_rescue_clusters"]
    )
