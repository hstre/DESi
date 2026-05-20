"""v17.3 - Long-Horizon Sensitive Document Ecology
tests."""
from __future__ import annotations

import json
import pathlib

from desi.sensitive_ecology import (
    N_STEPS, build_ecology_artifact, build_report,
    dissent_preservation, enum_snapshot_hash,
    epistemic_stability, final_hash,
    governance_integrity, min_source_quality_visibility,
    min_stability, mythologization_bounded,
    mythologization_growth, replay_hashes_match, run,
    sample, source_quality_always_visible,
    source_quality_visibility, trust_decayed,
    trust_volatility,
)
from desi.sensitive_ecology.report import (
    REPORT_VERDICTS, VERDICT_STABLE,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "sensitive_documents"
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


def test_sample_bounded() -> None:
    assert len(sample()) <= 200


# --- stability does NOT collapse ----------------
def test_epistemic_stability_holds() -> None:
    assert epistemic_stability() >= 0.90
    assert min_stability() >= 0.90


def test_source_quality_stays_visible() -> None:
    assert source_quality_visibility() >= 0.90
    assert min_source_quality_visibility() >= 0.90
    assert source_quality_always_visible() is True


def test_governance_integrity_holds() -> None:
    assert governance_integrity() >= 0.90


def test_dissent_preserved() -> None:
    assert dissent_preservation() == 1.0


# --- myth bounded, trust stress real ------------
def test_mythologization_bounded() -> None:
    assert mythologization_bounded() is True
    assert 0.0 < mythologization_growth() <= 0.28


def test_trust_genuinely_decays() -> None:
    assert trust_decayed() is True
    assert trust_volatility() > 0.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        mythologization_growth(), epistemic_stability(),
        source_quality_visibility(), governance_integrity(),
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
    art = _load("v17_3_ecology.json")
    assert art["schema_version"] == (
        "v17_3_long_horizon_sensitive_ecology"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v17_3_ecology.json")
    disc = art["disclaimer"].lower()
    assert "adopts no myth" in disc
    assert "identifies no one" in disc
    assert "no sensitive content" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v17_3_ecology.json")
    required = {
        "mythologization_growth",
        "epistemic_stability",
        "source_quality_visibility",
        "governance_integrity",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v17_3_ecology.json")
    live = build_ecology_artifact()
    assert art == live
