"""v23.1 - Experimental Conditions Reconstruction tests."""
from __future__ import annotations

import json
import pathlib

from desi.scientific_rendering import forbidden_hits
from desi.icrl_followup_conditions import (
    PROVENANCE, build_conditions_artifact, build_report,
    by_result_id, condition_visibility, defined_names,
    definitions, documented_result_ids, fixture_notes,
    metric_visibility, naked_numbers, provenance_section,
    result_traceability, results, sandbox_honesty,
    sandbox_limit_ids, sandbox_limits, synthetic_share,
    undefined_metrics, undocumented_results,
)
from desi.icrl_followup_conditions.report import (
    REPORT_VERDICTS, VERDICT_GROUNDED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "icrl_followup"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- provenance map -----------------------------
def test_provenance_maps_four_phases() -> None:
    assert PROVENANCE == {
        "desi_only_baseline": "v19",
        "desi_plus_wild": "v20",
        "comparison": "v21",
        "paper_generation": "v22",
    }


# --- no naked numbers ---------------------------
def test_no_naked_numbers() -> None:
    assert naked_numbers() == ()


def test_every_result_traceable_and_conditioned() -> None:
    for r in results():
        assert r.is_traceable()
        assert r.has_conditions()
        assert r.is_synthetic is True


def test_result_traceability_full() -> None:
    assert result_traceability() == 1.0


def test_condition_visibility_full() -> None:
    assert condition_visibility() == 1.0


def test_synthetic_share_full() -> None:
    assert synthetic_share() == 1.0


# --- metric definitions -------------------------
def test_metric_visibility_full() -> None:
    assert metric_visibility() == 1.0
    assert undefined_metrics() == ()


def test_every_reported_metric_is_defined() -> None:
    used = {r.metric_name for r in results()}
    assert used.issubset(defined_names())


def test_metric_definitions_have_ranges() -> None:
    for d in definitions():
        assert d.definition.strip()
        assert d.range_lo <= d.range_hi
        assert d.source.strip()


# --- fixtures -----------------------------------
def test_every_result_documented() -> None:
    assert undocumented_results() == ()
    rids = {r.result_id for r in results()}
    assert documented_result_ids() == frozenset(rids)


def test_fixture_notes_have_derivations() -> None:
    for n in fixture_notes():
        assert n.fixture.strip()
        assert n.derivation.strip()


# --- sandbox honesty ----------------------------
def test_sandbox_honesty_true() -> None:
    assert sandbox_honesty() is True


def test_sandbox_limits_present() -> None:
    assert len(sandbox_limits()) == 5
    assert set(sandbox_limit_ids()) == {
        "L1", "L2", "L3", "L4", "L5"
    }


# --- live grounding (values derived, not typed) -
def test_values_match_live_sources() -> None:
    from desi.icrl_governed import redundancy_reduction
    from desi.dual_agent_negotiation import exploration_diversity
    from desi.dual_agent_ecology import (
        authority_drift, capture_resistance,
    )
    from desi.comparative_exploration import (
        delta_novelty_gain, dual_agent, productivity_gain,
    )
    assert by_result_id("R1").value == redundancy_reduction()
    assert by_result_id("R2").value == delta_novelty_gain()
    assert by_result_id("R3").value == (
        dual_agent()["residual_hallucination"]
    )
    assert by_result_id("R4").value == exploration_diversity()
    assert by_result_id("R5").value == authority_drift()
    assert by_result_id("R6").value == capture_resistance()
    assert by_result_id("R7").value == productivity_gain()
    assert by_result_id("R8").value == 1.0


# --- metrics in range ---------------------------
def test_metrics_in_unit_interval() -> None:
    for m in (
        metric_visibility(), condition_visibility(),
        result_traceability(), synthetic_share(),
    ):
        assert 0.0 <= m <= 1.0


# --- governance rule (forbidden terms) ----------
def test_no_forbidden_terms_in_provenance_section() -> None:
    assert forbidden_hits(provenance_section()) == ()


def test_no_forbidden_terms_in_artifact() -> None:
    art = build_conditions_artifact()
    assert forbidden_hits(art["disclaimer"]) == ()
    assert forbidden_hits(provenance_section()) == ()


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_grounded() -> None:
    assert build_report().recommendation == VERDICT_GROUNDED


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v23_1_conditions.json")
    assert art["schema_version"] == (
        "v23_1_experimental_conditions"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v23_1_conditions.json")
    disc = art["disclaimer"].lower()
    assert "synthetic" in disc
    assert "sandbox" in disc
    assert "live" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v23_1_conditions.json")
    required = {
        "metric_visibility", "condition_visibility",
        "result_traceability", "sandbox_honesty",
    }
    assert required.issubset(art.keys())


def test_artifact_provenance_block() -> None:
    art = _load("v23_1_conditions.json")
    assert art["provenance"] == {
        "comparison": "v21",
        "desi_only_baseline": "v19",
        "desi_plus_wild": "v20",
        "paper_generation": "v22",
    }


def test_artifact_no_naked_numbers() -> None:
    art = _load("v23_1_conditions.json")
    assert art["naked_numbers"] == []
    assert art["recommendation"] == (
        "CONDITIONS_RECONSTRUCTED"
    )


def test_artifact_full_matches_live_build() -> None:
    art = _load("v23_1_conditions.json")
    live = build_conditions_artifact()
    assert art == live
