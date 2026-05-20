"""v9.2 - coalition warfare tests."""
from __future__ import annotations

import json
import pathlib

from desi.coalition_warfare.coalitions import (
    COALITION_ROLES, CoalitionRole, fixture,
    role_counts,
)
from desi.coalition_warfare.lineage import (
    coalition_detection, detected_coalitions,
    lineage_nodes, lineage_stability,
)
from desi.coalition_warfare.propagation import (
    consensus_integrity,
    dissent_preservation,
    isolated_preservation,
)
from desi.coalition_warfare.report import (
    build_coalition_warfare_artifact,
    build_report,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "strategic_epistemics"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_coalition_roles_closed_set() -> None:
    assert COALITION_ROLES == tuple(
        r.value for r in CoalitionRole
    )
    assert len(COALITION_ROLES) == 3


def test_coalition_detection_full() -> None:
    """Pflichtfrage 1: erkennt DESi
    kuenstlichen Konsens?"""
    assert coalition_detection() >= 0.90


def test_two_coalitions_detected() -> None:
    """Coalition A (3 members) and Coalition B
    (2 members) both flagged."""
    assert len(detected_coalitions()) == 2


def test_dissent_preservation_full() -> None:
    """Pflichtfrage 2: kollabiert Dissens?
    NEIN - jeder Dissenter bleibt ausserhalb
    jeder detected Coalition."""
    assert dissent_preservation() == 1.0


def test_isolated_preservation_full() -> None:
    """Isolierte Akteure werden NICHT
    versehentlich in eine detected Coalition
    gezogen."""
    assert isolated_preservation() == 1.0


def test_consensus_integrity_full() -> None:
    """Pflichtfrage 3 / 4: bleibt epistemische
    Vielfalt erhalten? Jede detected coalition
    ist eine reine artificial group, kein
    versehentlich groupierter isolated actor."""
    assert consensus_integrity() == 1.0


def test_lineage_stability_one() -> None:
    """Der Lineage-Builder ist deterministisch.
    """
    assert lineage_stability() == 1.0


def test_no_dissenter_in_any_coalition() -> None:
    dissenters = {
        b.broadcast_id for b in fixture()
        if b.coalition_role == (
            CoalitionRole.DISSENTER.value
        )
    }
    for _, members in detected_coalitions():
        for m in members:
            assert m not in dissenters


def test_every_coalition_member_detected() -> (
    None
):
    truth = {
        b.broadcast_id for b in fixture()
        if b.coalition_role == (
            CoalitionRole.COALITION_MEMBER.value
        )
    }
    detected: set[str] = set()
    for _, members in detected_coalitions():
        detected.update(members)
    assert truth <= detected


def test_lineage_nodes_cover_fixture() -> None:
    assert {
        n.broadcast_id for n in lineage_nodes()
    } == {
        b.broadcast_id for b in fixture()
    }


def test_role_counts_consistent() -> None:
    counts = role_counts()
    assert sum(counts.values()) == len(
        fixture(),
    )


def test_replay_stability_one() -> None:
    """Pflichtfrage 4: bleibt Replay stabil?"""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "COALITION_RESILIENT",
        "COALITION_DETECTION_WEAK",
        "COALITION_CONSENSUS_FAKE",
        "COALITION_DISSENT_SUPPRESSED",
        "COALITION_ISOLATED_SWALLOWED",
        "COALITION_LINEAGE_DRIFT",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_resilient() -> None:
    """Killerfrage: kann DESi epistemische
    Vielfalt gegen koordinierte Narrative
    verteidigen?"""
    assert build_report().recommendation == (
        "COALITION_RESILIENT"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v9_2_coalition_warfare.json")
    assert art["schema_version"] == (
        "v9_2_coalition_warfare"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v9_2_coalition_warfare.json")
    required = {
        "coalition_detection",
        "consensus_integrity",
        "dissent_preservation",
        "lineage_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v9_2_report.json")
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
    art = _load("v9_2_coalition_warfare.json")
    live = build_coalition_warfare_artifact()
    assert art == live
