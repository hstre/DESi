"""v35.3 - Public Benchmark Scorecards & HF Export tests."""
from __future__ import annotations

import json
import pathlib

from desi.external_benchmarks_export import (
    FORBIDDEN_MARKETING_TERMS, build_public_exports_artifact,
    build_report, export_metrics, governance_visibility, hf_dataset,
    hf_space, limitation_visibility, marketing_free, marketing_hits,
    public_scorecards, real_run_names, real_vs_synthetic_visibility,
    replay_manifest, replay_manifest_integrity, scorecard_traceability,
    synthetic_run_names, system_card,
)
from desi.external_benchmarks_export.report import (
    REPORT_VERDICTS, VERDICT_HONEST,
)
from desi.external_benchmarks_export.system_card import _contains_term


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "external_benchmarks"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- no AGI marketing ---------------------------
def test_marketing_free() -> None:
    assert marketing_free() is True
    assert marketing_hits() == ()


def test_marketing_guard_actually_catches_hype() -> None:
    # the guard must fire on real hype terms (word-boundary match)
    assert _contains_term("this is agi now", "agi")
    assert _contains_term("a superintelligence system", "superintelligence")
    # but must NOT fire inside unrelated words
    assert not _contains_term("we paginate results", "agi")


def test_not_claims_present() -> None:
    card = system_card()
    joined = " ".join(card["not_claims"]).lower()
    assert "not agi" in joined


# --- real vs synthetic separation ---------------
def test_real_vs_synthetic_visibility_full() -> None:
    assert real_vs_synthetic_visibility() == 1.0


def test_real_and_synthetic_runs_separated() -> None:
    real = set(real_run_names())
    synth = set(synthetic_run_names())
    assert real == {"real_drift", "real_search"}
    assert synth == {"reproducibility", "scientific_rendering"}
    assert not (real & synth)


# --- traceability / limitations / governance ----
def test_scorecard_traceability_full() -> None:
    assert scorecard_traceability() == 1.0
    for c in public_scorecards():
        assert c.is_traceable()


def test_limitation_visibility_full() -> None:
    assert limitation_visibility() == 1.0


def test_governance_visibility_full() -> None:
    assert governance_visibility() == 1.0


# --- replay manifest ----------------------------
def test_replay_manifest_integrity_full() -> None:
    assert replay_manifest_integrity() == 1.0
    man = replay_manifest()
    assert "real_drift" in man
    assert "system_card" in man


def test_metrics_in_unit_interval() -> None:
    for v in export_metrics().values():
        assert 0.0 <= v <= 1.0


# --- hf exports ---------------------------------
def test_hf_dataset_records() -> None:
    ds = hf_dataset()
    assert ds["license"] == "CC0-1.0"
    assert len(ds["records"]) == len(public_scorecards())


def test_hf_space_honest_banner() -> None:
    space = hf_space()
    banner = space["honest_banner"].lower()
    assert "not official leaderboard" in banner
    assert "not an agi system" in banner


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_honest() -> None:
    assert build_report().recommendation == VERDICT_HONEST


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v35_3_public_exports.json")
    assert art["schema_version"] == "v35_3_public_exports"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v35_3_public_exports.json")
    disc = art["disclaimer"].lower()
    assert "not official leaderboard results" in disc
    assert "no agi" in disc or "not an agi" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v35_3_public_exports.json")
    required = {
        "scorecard_traceability", "limitation_visibility",
        "real_vs_synthetic_visibility", "governance_visibility",
        "replay_manifest_integrity",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v35_3_public_exports.json")
    assert art == build_public_exports_artifact()


def test_forbidden_marketing_terms_listed() -> None:
    assert "agi" in FORBIDDEN_MARKETING_TERMS
    assert "superintelligence" in FORBIDDEN_MARKETING_TERMS
