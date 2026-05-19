"""v8.0 - resource scarcity audit tests."""
from __future__ import annotations

import json
import pathlib

from desi.persistent_conflicts.budget import (
    BUDGET, SCHEDULE_DECISIONS,
    ScheduleDecision, deferred_count,
    processed_count, schedule, skipped_count,
    total_processed_cost,
)
from desi.persistent_conflicts.report import (
    build_report,
    build_resource_scarcity_artifact,
)
from desi.persistent_conflicts.resources import (
    RESOURCE_KINDS, ResourceKind, fixture,
)
from desi.persistent_conflicts.tradeoffs import (
    cheap_solution_drift,
    complexity_preservation,
    governance_integrity, resource_bias,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "persistent_conflicts"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_resource_kinds_closed_set() -> None:
    assert RESOURCE_KINDS == tuple(
        r.value for r in ResourceKind
    )
    assert len(RESOURCE_KINDS) == 5


def test_schedule_decisions_closed_set() -> None:
    assert SCHEDULE_DECISIONS == tuple(
        d.value for d in ScheduleDecision
    )


def test_fixture_quadrants_present() -> None:
    """Sanity: the fixture spans all four
    (cost, value) quadrants so the scheduler
    has to discriminate on value, not cost."""
    high_val_high_cost = [
        c for c in fixture()
        if c.epistemic_value >= 0.70
        and c.complexity_cost >= 0.70
    ]
    high_val_low_cost = [
        c for c in fixture()
        if c.epistemic_value >= 0.70
        and c.complexity_cost <= 0.30
    ]
    low_val_high_cost = [
        c for c in fixture()
        if c.epistemic_value <= 0.30
        and c.complexity_cost >= 0.70
    ]
    low_val_low_cost = [
        c for c in fixture()
        if c.epistemic_value <= 0.30
        and c.complexity_cost <= 0.30
    ]
    assert len(high_val_high_cost) >= 1
    assert len(high_val_low_cost) >= 1
    assert len(low_val_high_cost) >= 1
    assert len(low_val_low_cost) >= 1


def test_schedule_is_deterministic() -> None:
    a = [s.to_dict() for s in schedule()]
    b = [s.to_dict() for s in schedule()]
    assert a == b


def test_total_processed_cost_within_budget() -> (
    None
):
    assert total_processed_cost() <= BUDGET


def test_counts_sum_to_fixture() -> None:
    assert (
        processed_count()
        + deferred_count()
        + skipped_count()
        == len(fixture())
    )


def test_resource_bias_low() -> None:
    """Pflichtfrage 3: driftet DESi zu billigen
    Loesungen?"""
    assert resource_bias() <= 0.10


def test_complexity_preservation_high() -> None:
    """Pflichtfrage 2: werden komplexe Konflikte
    verdraengt? NEIN - kein einziger high-value
    Claim wird SKIPPED."""
    assert complexity_preservation() >= 0.50


def test_no_high_value_skipped() -> None:
    """Stronger invariant: no claim with
    epistemic_value >= 0.70 is ever SKIPPED."""
    for s in schedule():
        if s.epistemic_value >= 0.70:
            assert s.decision != (
                ScheduleDecision.SKIP.value
            )


def test_cheap_solution_drift_low() -> None:
    """Pflichtfrage 1: entsteht epistemische
    Vereinfachung?"""
    assert cheap_solution_drift() <= 0.30


def test_governance_integrity_one() -> None:
    """Pflichtfrage 4: bleibt Governance
    stabil?"""
    assert governance_integrity() == 1.0


def test_low_value_high_cost_mostly_skipped() -> (
    None
):
    """Sanity: low-value high-cost claims (the
    expensive trash) should NOT be PROCESSED -
    that would be wasted budget."""
    for s in schedule():
        if (
            s.epistemic_value < 0.30
            and s.complexity_cost > 0.70
        ):
            assert s.decision != (
                ScheduleDecision.PROCESS.value
            )


def test_replay_stability_one() -> None:
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "SCARCITY_HONEST",
        "SCARCITY_RESOURCE_BIAS",
        "SCARCITY_COMPLEXITY_LOSS",
        "SCARCITY_CHEAP_DRIFT",
        "SCARCITY_GOVERNANCE_BREACH",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_honest() -> None:
    """Killerfrage: bleibt DESi ehrlich, wenn
    Wahrheit teuer wird?"""
    assert build_report().recommendation == (
        "SCARCITY_HONEST"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v8_0_resource_scarcity.json")
    assert art["schema_version"] == (
        "v8_0_resource_scarcity"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v8_0_resource_scarcity.json")
    required = {
        "resource_bias",
        "complexity_preservation",
        "cheap_solution_drift",
        "governance_integrity",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v8_0_report.json")
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable


def test_artifact_full_matches_live_build() -> None:
    art = _load("v8_0_resource_scarcity.json")
    live = build_resource_scarcity_artifact()
    assert art == live
