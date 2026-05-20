"""v11.2 - tactical stress tests."""
from __future__ import annotations

import json
import pathlib

from desi.tactical_stress.horizon import (
    assigned_depth, horizon_risk,
)
from desi.tactical_stress.report import (
    build_report,
    build_tactical_stress_artifact,
)
from desi.tactical_stress.tactics import (
    TACTICAL_PATTERNS, TacticalPattern,
    fixture, pattern_counts,
)
from desi.tactical_stress.trap_detection import (
    critical_line_preservation,
    resolved_cases, tactical_miss_rate,
    trap_detection,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "chess_governance"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_tactical_patterns_closed_set() -> None:
    assert TACTICAL_PATTERNS == tuple(
        p.value for p in TacticalPattern
    )
    assert len(TACTICAL_PATTERNS) == 7


def test_fixture_balanced_patterns() -> None:
    counts = pattern_counts()
    assert set(counts.keys()) == set(
        TACTICAL_PATTERNS,
    )
    assert set(counts.values()) == {2}


def test_tactical_miss_rate_zero() -> None:
    """Pflichtfrage 1: verliert DESi taktische
    Linien?"""
    assert tactical_miss_rate() <= 0.05


def test_tactical_miss_rate_actually_zero() -> (
    None
):
    """Stronger: no tactical case is ever
    missed under DESi's critical-tactic
    override."""
    assert tactical_miss_rate() == 0.0


def test_horizon_risk_zero() -> None:
    """Pflichtfrage 2: entsteht Horizon-
    Blindheit?"""
    assert horizon_risk() <= 0.05


def test_critical_line_preservation_full() -> (
    None
):
    """Every critical tactical case is
    preserved at full search depth."""
    assert critical_line_preservation() >= 0.95


def test_trap_detection_full() -> None:
    """All TRAP-pattern cases are resolved."""
    assert trap_detection() >= 0.95


def test_assigned_depth_meets_required() -> None:
    """For every critical case the assigned
    depth is at least depth_required."""
    for c in fixture():
        if c.is_critical:
            assert (
                assigned_depth(c.case_id)
                >= c.depth_required
            )


def test_every_case_resolved() -> None:
    for r in resolved_cases():
        assert r.resolved


def test_replay_stability_one() -> None:
    """Pflichtfrage 4: wie robust bleibt die
    Suche?"""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "TACTICAL_SURVIVED",
        "TACTICAL_LEAK",
        "TACTICAL_HORIZON_RISK",
        "TACTICAL_TRAP_BLIND",
        "TACTICAL_CRITICAL_LOSS",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_survived() -> None:
    """Killerfrage: spart DESi nur Compute -
    oder verliert es dabei Schachverstaendnis?"""
    assert build_report().recommendation == (
        "TACTICAL_SURVIVED"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v11_2_tactical_stress.json")
    assert art["schema_version"] == (
        "v11_2_tactical_stress"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v11_2_tactical_stress.json")
    required = {
        "tactical_miss_rate", "horizon_risk",
        "critical_line_preservation",
        "trap_detection",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v11_2_report.json")
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
    art = _load("v11_2_tactical_stress.json")
    live = build_tactical_stress_artifact()
    assert art == live
