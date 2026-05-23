"""v16.3 - Long-Horizon Historical Ecology tests."""
from __future__ import annotations

import json
import pathlib

from desi.criminal_historical_ecology import (
    N_STEPS, build_ecology_artifact, build_report,
    core_lines_intact, drift_visible,
    enum_snapshot_hash, epistemic_stability,
    final_hash, governance_stable,
    independent_evidence_preservation,
    min_stability, mythologization_growth,
    narrative_inflation, narrative_inflation_bounded,
    replay_hashes_match, run, sample,
)
from desi.criminal_historical_ecology.report import (
    REPORT_VERDICTS, VERDICT_STABLE,
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


# --- long horizon -------------------------------
def test_runs_at_least_5000_steps() -> None:
    assert N_STEPS >= 5000
    assert len(run()) == N_STEPS


def test_sample_is_bounded() -> None:
    assert len(sample()) <= 200


# --- stability does NOT collapse ----------------
def test_epistemic_stability_holds() -> None:
    assert epistemic_stability() >= 0.90
    assert min_stability() >= 0.90


def test_independent_evidence_preserved() -> None:
    assert independent_evidence_preservation() >= 0.90
    assert core_lines_intact() is True


# --- inflation / myth grow but stay bounded -----
def test_inflation_bounded_and_visible() -> None:
    assert narrative_inflation_bounded() is True
    assert drift_visible() is True
    assert 0.0 < narrative_inflation() <= 0.25


def test_mythologization_growth_bounded() -> None:
    mg = mythologization_growth()
    assert 0.0 < mg <= 0.30


def test_governance_stable() -> None:
    assert governance_stable() is True


def test_metrics_in_unit_interval() -> None:
    for m in (
        narrative_inflation(), epistemic_stability(),
        independent_evidence_preservation(),
        mythologization_growth(),
    ):
        assert 0.0 <= m <= 1.0


# --- replay -------------------------------------
def test_replay_hashes_match() -> None:
    assert replay_hashes_match() is True


def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_final_hash_deterministic() -> None:
    assert final_hash() == build_report().final_hash
    assert len(final_hash()) == 64


def test_enum_snapshot_stable() -> None:
    assert enum_snapshot_hash() == (
        build_report().enum_snapshot_hash
    )


# --- recommendation / determinism ---------------
def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


def test_recommendation_is_stable() -> None:
    assert build_report().recommendation == (
        VERDICT_STABLE
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v16_3_ecology.json")
    assert art["schema_version"] == (
        "v16_3_long_horizon_historical_ecology"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v16_3_ecology.json")
    disc = art["disclaimer"].lower()
    assert "made visible" in disc
    assert "never adopts them as fact" in disc
    assert "no new factual claim" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v16_3_ecology.json")
    required = {
        "narrative_inflation",
        "epistemic_stability",
        "independent_evidence_preservation",
        "mythologization_growth",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v16_3_ecology.json")
    live = build_ecology_artifact()
    assert art == live
