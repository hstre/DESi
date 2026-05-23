"""v4.2 — distribution metrics, counterfactual safety, guard
pressure map."""
from __future__ import annotations

from desi.external_audit_probe import (
    MIN_LARGEST_CLUSTER, MAX_UNKNOWN_FRACTION,
    classify_all, collect_false_support_cases,
    counterfactual_evaluate_all, distribution_summarise,
    measure_guard_pressure, replay_all,
)
from desi.external_audit_probe.enums import ExternalAuditFailure


def _bundle():
    cases = collect_false_support_cases()
    records = replay_all(cases)
    text_index = {c.chain_id: c.text for c in cases}
    classes = classify_all(records, text_index)
    return cases, records, classes


def test_v42_distribution_largest_cluster_pinned() -> None:
    """v4.2-era distribution had HIDDEN_NEGATION 69/143 =
    0.483 as the largest cluster. After v4.9 the live residue
    is empty; we pin the v4.2-era distribution via the
    frozen artifact."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_2" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["distribution"]["largest_cluster"] >= (
        MIN_LARGEST_CLUSTER
    )


def test_v42_distribution_unknown_pinned() -> None:
    """v4.2-era distribution had UNKNOWN = 0. Pin via the
    frozen artifact."""
    import json, pathlib
    p = (
        pathlib.Path(__file__).resolve().parents[2]
        / "artifacts" / "v4_2" / "report.json"
    )
    data = json.loads(p.read_text(encoding="utf-8"))
    total = data["distribution"]["total"]
    unknown = data["distribution"]["failure_count"].get(
        ExternalAuditFailure.UNKNOWN.value, 0,
    )
    assert total > 0
    assert unknown / total <= MAX_UNKNOWN_FRACTION


def test_counterfactual_contamination_is_zero() -> None:
    cases, records, classes = _bundle()
    cfs = counterfactual_evaluate_all(cases, classes)
    assert all(cf.contamination_risk == 0 for cf in cfs)
    assert sum(cf.contamination_risk for cf in cfs) == 0


def test_guard_pressure_zero_actual_firing() -> None:
    """Every case is, by construction, a false support — i.e.
    every actual guard returned False. Shadow pressure is the
    interesting quantity."""
    cases, records, _ = _bundle()
    pressures = tuple(
        measure_guard_pressure(c, r)
        for c, r in zip(cases, records)
    )
    for p in pressures:
        assert p.actual_guard_hits == ()
