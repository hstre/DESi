"""v27.3 - Long-Horizon Research Ecology tests."""
from __future__ import annotations

import json
import pathlib

from desi.research_ecology import (
    build_ecology_artifact, build_report, conflict_preservation,
    forgotten_events, fragility_visibility, hype_amplitude,
    hype_visibility, lineage_preserved,
    open_question_preservation, plurality_preservation,
    rediscovery_events, replay_stability, run,
)
from desi.research_ecology.report import (
    REPORT_VERDICTS, VERDICT_PLURAL,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "research_harvester"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- long horizon -------------------------------
def test_at_least_5000_steps() -> None:
    assert run().steps >= 5000


def test_sample_recorded() -> None:
    assert len(run().sample) == 200


# --- plurality not collapsing -------------------
def test_plurality_preservation_full() -> None:
    assert plurality_preservation() == 1.0


def test_lineage_preserved_nothing_deleted() -> None:
    assert lineage_preserved() is True
    r = run()
    assert r.min_present_lines == r.method_count


# --- hype waves visible -------------------------
def test_hype_visibility_full() -> None:
    assert hype_visibility() == 1.0
    assert hype_amplitude() > 0.0


# --- fragility / open questions / conflicts kept -
def test_fragility_visibility_full() -> None:
    assert fragility_visibility() == 1.0


def test_open_question_preservation_full() -> None:
    assert open_question_preservation() == 1.0


def test_conflict_preservation_full() -> None:
    assert conflict_preservation() == 1.0


# --- forgetting is soft -------------------------
def test_forgetting_and_rediscovery_happen() -> None:
    # ideas do go dormant and return, but nothing is deleted
    assert forgotten_events() > 0
    assert rediscovery_events() > 0
    assert lineage_preserved() is True


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_run_is_deterministic() -> None:
    assert run().chain_head == run().chain_head
    assert run().to_dict() == run().to_dict()


def test_metrics_in_unit_interval() -> None:
    for m in (
        plurality_preservation(), hype_visibility(),
        fragility_visibility(), open_question_preservation(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- no ranking / authority ---------------------
def test_report_has_no_ranking_fields() -> None:
    d = build_report().to_dict()
    forbidden = {"score", "rank", "ranking", "impact", "best",
                 "winner"}
    assert forbidden.isdisjoint(set(d.keys()))


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_plural_stable() -> None:
    assert build_report().recommendation == VERDICT_PLURAL


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v27_3_ecology.json")
    assert art["schema_version"] == "v27_3_research_ecology"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v27_3_ecology.json")
    disc = art["disclaimer"].lower()
    assert "never deleted" in disc
    assert "without becoming a research authority" in disc
    assert "no prng" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v27_3_ecology.json")
    required = {
        "plurality_preservation", "hype_visibility",
        "fragility_visibility", "open_question_preservation",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_run_at_least_5000_steps() -> None:
    art = _load("v27_3_ecology.json")
    assert art["run"]["steps"] >= 5000


def test_artifact_full_matches_live_build() -> None:
    art = _load("v27_3_ecology.json")
    live = build_ecology_artifact()
    assert art == live
