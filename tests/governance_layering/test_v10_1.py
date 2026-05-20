"""v10.1 - governance layering tests."""
from __future__ import annotations

import json
import pathlib

from desi.governance_layering.authority import (
    authority_diversity, authority_drift,
    governance_coherence, layer_integrity,
)
from desi.governance_layering.delegation import (
    delegation_links,
    delegation_transparency,
    downward_delegation_share,
)
from desi.governance_layering.layers import (
    GOVERNANCE_LAYERS, GovernanceLayer,
    LAYER_PRECEDENCE, fixture, layer_counts,
)
from desi.governance_layering.report import (
    build_governance_layering_artifact,
    build_report,
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


def test_governance_layers_closed_set() -> None:
    assert GOVERNANCE_LAYERS == tuple(
        g.value for g in GovernanceLayer
    )
    assert len(GOVERNANCE_LAYERS) == 4


def test_precedence_strict_total_order() -> None:
    vals = list(LAYER_PRECEDENCE.values())
    assert sorted(vals) == [0, 1, 2, 3]


def test_layer_integrity_one() -> None:
    """Pflichtfrage 2: werden Layer
    undurchsichtig? NEIN - closed enum
    discipline."""
    assert layer_integrity() == 1.0


def test_authority_drift_zero() -> None:
    """Pflichtfrage 3: driftet Autoritaet?"""
    assert authority_drift() == 0.0


def test_delegation_transparency_one() -> None:
    """Every decision carries a non-empty
    rationale."""
    assert delegation_transparency() == 1.0


def test_governance_coherence_one() -> None:
    """Pflichtfrage 1: entsteht Governance-
    Korrosion?"""
    assert governance_coherence() == 1.0


def test_downward_delegation_share_one() -> None:
    """Every cross-layer link flows DOWN the
    precedence ladder. No authority inversion."""
    assert downward_delegation_share() == 1.0


def test_authority_diversity_one() -> None:
    """Each authority_id appears in only one
    decision - no consolidation."""
    assert authority_diversity() == 1.0


def test_no_layer_inversion_in_links() -> None:
    by_id = {
        d.decision_id: d for d in fixture()
    }
    for link in delegation_links():
        if link.parent_id is None:
            continue
        child = by_id[link.child_id]
        parent = by_id[link.parent_id]
        assert (
            LAYER_PRECEDENCE[parent.layer]
            >= LAYER_PRECEDENCE[child.layer]
        )


def test_layer_counts_cover_all_layers() -> None:
    counts = layer_counts()
    assert set(counts.keys()) == set(
        GOVERNANCE_LAYERS,
    )


def test_replay_stability_one() -> None:
    """Pflichtfrage 4: bleibt Replay erhalten?"""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "LAYERING_COHERENT",
        "LAYERING_INTEGRITY_BREACH",
        "LAYERING_AUTHORITY_DRIFT",
        "LAYERING_OPAQUE",
        "LAYERING_INCOHERENT",
        "LAYERING_INVERSION",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_coherent() -> None:
    """Killerfrage: kann DESi Governance
    schichten, ohne epistemische Verantwortlich-
    keit zu verlieren?"""
    assert build_report().recommendation == (
        "LAYERING_COHERENT"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load(
        "v10_1_governance_layering.json",
    )
    assert art["schema_version"] == (
        "v10_1_governance_layering"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load(
        "v10_1_governance_layering.json",
    )
    required = {
        "layer_integrity",
        "authority_drift",
        "delegation_transparency",
        "governance_coherence",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v10_1_report.json")
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
        "v10_1_governance_layering.json",
    )
    live = build_governance_layering_artifact()
    assert art == live
