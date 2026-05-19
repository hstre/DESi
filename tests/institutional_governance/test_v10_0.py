"""v10.0 - institutional ecology tests."""
from __future__ import annotations

import json
import pathlib

from desi.institutional_governance.institutions import (
    GOVERNANCE_STYLES, GovernanceStyle,
    INSTITUTION_KINDS, InstitutionKind,
    fixture, kind_counts, style_counts,
)
from desi.institutional_governance.report import (
    build_institutional_ecology_artifact,
    build_report,
)
from desi.institutional_governance.roles import (
    INSTITUTIONAL_ROLES, InstitutionalRole,
    role_assignments, role_counts,
)
from desi.institutional_governance.trust_layers import (
    epistemic_equality,
    governance_transparency,
    power_concentration,
    role_distribution_balance, trust_fairness,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "institutional_governance"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_institution_kinds_closed_set() -> None:
    assert INSTITUTION_KINDS == tuple(
        i.value for i in InstitutionKind
    )
    assert len(INSTITUTION_KINDS) == 5


def test_governance_styles_closed_set() -> None:
    assert GOVERNANCE_STYLES == tuple(
        g.value for g in GovernanceStyle
    )
    assert len(GOVERNANCE_STYLES) == 4


def test_institutional_roles_closed_set() -> None:
    assert INSTITUTIONAL_ROLES == tuple(
        r.value for r in InstitutionalRole
    )
    assert len(INSTITUTIONAL_ROLES) == 5


def test_fixture_balanced_kinds() -> None:
    counts = kind_counts()
    assert set(counts.keys()) == set(
        INSTITUTION_KINDS,
    )
    assert set(counts.values()) == {2}


def test_role_assignments_cover_fixture() -> None:
    assert len(role_assignments()) == len(
        fixture(),
    )


def test_role_counts_balanced() -> None:
    counts = role_counts()
    assert set(counts.values()) == {2}


def test_power_concentration_low() -> None:
    """Pflichtfrage 1: entstehen
    Machtzentren?"""
    assert power_concentration() <= 0.10


def test_trust_fairness_high() -> None:
    """Pflichtfrage 2: driftet Vertrauen
    institutionell?"""
    assert trust_fairness() >= 0.50


def test_epistemic_equality_high() -> None:
    """Pflichtfrage 3: entsteht epistemische
    Ungleichheit?"""
    assert epistemic_equality() >= 0.80


def test_governance_transparency_high() -> None:
    """Pflichtfrage 4: bleibt Governance
    transparent?"""
    assert governance_transparency() >= 0.95


def test_role_distribution_balance_high() -> (
    None
):
    """Roles are evenly distributed across the
    five closed kinds."""
    assert role_distribution_balance() >= 0.95


def test_no_single_institution_dominates() -> (
    None
):
    """Sanity invariant: no institution holds
    more than 15 percent of power or
    resources."""
    for i in fixture():
        assert i.power_share <= 0.15
        assert i.resource_share <= 0.15


def test_style_counts_consistent() -> None:
    sc = style_counts()
    assert sum(sc.values()) == len(fixture())


def test_replay_stability_one() -> None:
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "ECOLOGY_BALANCED",
        "ECOLOGY_POWER_CONCENTRATED",
        "ECOLOGY_TRUST_UNFAIR",
        "ECOLOGY_INEQUALITY",
        "ECOLOGY_OPAQUE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_balanced() -> None:
    """Killerfrage: kann DESi institutionelle
    Ordnung modellieren, ohne epistemische
    Machtakkumulation zu tolerieren?"""
    assert build_report().recommendation == (
        "ECOLOGY_BALANCED"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load(
        "v10_0_institutional_ecology.json",
    )
    assert art["schema_version"] == (
        "v10_0_institutional_ecology"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load(
        "v10_0_institutional_ecology.json",
    )
    required = {
        "power_concentration",
        "trust_fairness",
        "epistemic_equality",
        "governance_transparency",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v10_0_report.json")
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
    art = _load(
        "v10_0_institutional_ecology.json",
    )
    live = (
        build_institutional_ecology_artifact()
    )
    assert art == live
