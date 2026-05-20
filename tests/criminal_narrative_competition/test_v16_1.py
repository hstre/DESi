"""v16.1 - Narrative Competition tests."""
from __future__ import annotations

import json
import pathlib

from desi.criminal_epistemics import ClaimStatus, by_id
from desi.criminal_narrative_competition import (
    NARRATIVE_IDS, bridge_pressure,
    bridge_pressure_by_narrative,
    build_narratives_artifact, build_report,
    cross_narrative_overlap, most_bridge_dependent,
    narratives, no_preferred_narrative,
    robust_claims, source_dependency,
    speculative_growth,
)
from desi.criminal_narrative_competition.report import (
    REPORT_VERDICTS, VERDICT_NO_PREFERENCE,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "criminal_epistemics"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- closed vocabulary --------------------------
def test_narrative_ids_closed_set() -> None:
    from desi.criminal_narrative_competition import (
        NarrativeId,
    )
    assert NARRATIVE_IDS == tuple(
        n.value for n in NarrativeId
    )
    assert len(NARRATIVE_IDS) == 4


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


# --- metrics ------------------------------------
def test_metrics_in_unit_interval() -> None:
    for m in (
        bridge_pressure(),
        source_dependency(),
        speculative_growth(),
        cross_narrative_overlap(),
    ):
        assert 0.0 <= m <= 1.0


def test_alternative_is_most_leap_dependent() -> None:
    """Pflichtfrage 1: the alternative
    reconstruction needs the most unsupported
    bridges."""
    assert most_bridge_dependent() == (
        "alternative_reconstruction"
    )


def test_bridge_pressure_ordering() -> None:
    by = bridge_pressure_by_narrative()
    assert (
        by["institutional"]
        <= by["lone_gunman"]
        <= by["multi_actor"]
        <= by["alternative_reconstruction"]
    )


def test_robust_core_is_verified_facts() -> None:
    """Pflichtfrage 4: the claims robust across all
    narratives are exactly the uncontested verified
    facts."""
    robust = set(robust_claims())
    assert robust == {"C01", "C02", "C03", "C04"}
    for cid in robust:
        assert by_id(cid).status == (
            ClaimStatus.VERIFIED.value
        )


def test_speculation_grows_in_alternative() -> None:
    by = build_report().speculative_growth_by_narrative
    assert (
        by["alternative_reconstruction"]
        == max(by.values())
    )


# --- the no-preference governance invariant -----
def test_no_preferred_narrative() -> None:
    assert no_preferred_narrative() is True


def test_no_narrative_conclusion_promoted() -> None:
    """DESi must not crown a winner: no narrative's
    conclusion may be elevated to VERIFIED."""
    for n in narratives():
        assert by_id(n.conclusion).status != (
            ClaimStatus.VERIFIED.value
        )


def test_report_has_no_winner_field() -> None:
    """Structurally there must be no 'true' or
    'preferred' narrative field in the output."""
    d = build_report().to_dict()
    for forbidden in (
        "true_narrative", "preferred_narrative",
        "winning_narrative", "correct_narrative",
    ):
        assert forbidden not in d


def test_recommendation_is_no_preference() -> None:
    assert build_report().recommendation == (
        VERDICT_NO_PREFERENCE
    )


# --- replay / determinism -----------------------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v16_1_narratives.json")
    assert art["schema_version"] == (
        "v16_1_narrative_competition"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v16_1_narratives.json")
    disc = art["disclaimer"].lower()
    assert "prefers no narrative" in disc
    assert "no 'true_narrative' output" in disc
    assert "no new factual claim" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v16_1_narratives.json")
    required = {
        "bridge_pressure",
        "source_dependency",
        "speculative_growth",
        "cross_narrative_overlap",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v16_1_narratives.json")
    live = build_narratives_artifact()
    assert art == live
