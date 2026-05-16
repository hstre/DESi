"""v4.4 — counterfactual probes + safe-probe contamination."""
from __future__ import annotations

from desi.residual_semantic_probe import (
    SemanticProbe, collect_residue_cases,
    semantic_probe_evaluate_all,
)
from desi.residual_semantic_probe.rescue import analyse
from desi.residual_semantic_probe.classifier import classify_all
from desi.residual_semantic_probe.replay import replay_all


def _bundle():
    cases = collect_residue_cases()
    records = replay_all(cases)
    text_index = {c.chain_id: c.text for c in cases}
    classes = classify_all(records, text_index)
    return cases, classes


def test_each_probe_evaluated_on_every_case() -> None:
    cases = collect_residue_cases()
    out = semantic_probe_evaluate_all(cases)
    by_probe: dict[str, list] = {}
    for o in out:
        by_probe.setdefault(o.probe, []).append(o)
    if cases:
        assert len(by_probe) == len(SemanticProbe)
        for probe in SemanticProbe:
            assert len(by_probe[probe.value]) == len(cases)
    else:
        # After v4.5/v4.7/v4.9 the live residue may be empty;
        # evaluate_all returns no outcomes.
        assert by_probe == {}


def test_s5_bidirectional_link_check_is_safe() -> None:
    cases, classes = _bundle()
    per_probe, _ = analyse(cases, classes)
    s5 = next(
        p for p in per_probe
        if p.probe == SemanticProbe.S5_BIDIRECTIONAL_LINK_CHECK.value
    )
    assert s5.contamination_risk == 0
    assert s5.unsafe is False


def test_aggressive_probes_have_contamination() -> None:
    cases, classes = _bundle()
    per_probe, _ = analyse(cases, classes)
    aggressive = {
        SemanticProbe.S2_INNER_ONLY_ROUTE.value,
        SemanticProbe.S3_MANDATORY_CONSILIUM.value,
    }
    for p in per_probe:
        if p.probe in aggressive:
            assert p.contamination_risk > 0, p.probe


def test_v44_majority_rescue_clusters_pinned_in_frozen_artifact() -> None:
    """At v4.4 time the only majority rescue cluster was
    BIDIRECTIONAL_CYCLE — the v4.5 patch then absorbed exactly
    that cluster, so the live residue no longer contains it.
    We pin the v4.4-era result against the frozen artifact."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_4" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    assert tuple(
        data["agreement"]["majority_rescue_clusters"],
    ) == ("BIDIRECTIONAL_CYCLE",)
