"""v38.0 - OpenRouter Connector Layer tests (over real captures)."""
from __future__ import annotations

import json
import pathlib

from desi.live_llm_validation import (
    ROLE_DEEPSEEK, ROLE_GRANITE, api_response_capture,
    build_connectors_artifact, build_report, catalog_models,
    connector_metrics, content_hash, governance_identity,
    model_for_role, model_present, model_version_visibility,
    raw_output_replayability, replay_stability,
    response_hash_integrity, samples,
)
from desi.live_llm_validation.report import (
    REPORT_VERDICTS, VERDICT_INGESTED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "live_llm_validation"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- real catalog -------------------------------
def test_target_models_in_catalog() -> None:
    assert model_present(model_for_role(ROLE_GRANITE))
    assert model_present(model_for_role(ROLE_DEEPSEEK))
    assert "ibm-granite/granite-4.1-8b" in catalog_models()
    assert "deepseek/deepseek-v4-pro" in catalog_models()


def test_catalog_has_real_pricing() -> None:
    for m in catalog_models().values():
        p = m.get("pricing", {})
        assert p.get("prompt") is not None
        assert p.get("completion") is not None


# --- real captures present ----------------------
def test_samples_captured() -> None:
    sm = samples()
    assert len(sm) >= 2
    for r in sm:
        assert r["provenance"] == "live_openrouter_capture"
        assert r["raw_content"]
        assert r["model_version"]


def test_api_response_capture_full() -> None:
    assert api_response_capture() == 1.0


# --- hashing / replay ---------------------------
def test_response_hash_integrity_full() -> None:
    assert response_hash_integrity() == 1.0


def test_every_capture_hash_matches_content() -> None:
    for r in samples():
        assert r["content_hash"] == content_hash(r["raw_content"])


def test_raw_output_replayability_full() -> None:
    assert raw_output_replayability() == 1.0


def test_model_version_visibility_full() -> None:
    assert model_version_visibility() == 1.0


def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


# --- governance ---------------------------------
def test_governance_identity_full() -> None:
    assert governance_identity() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in connector_metrics().values():
        assert 0.0 <= v <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_ingested() -> None:
    assert build_report().recommendation == VERDICT_INGESTED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_real_cost_recorded() -> None:
    # real spend is captured and non-negative
    assert build_report().total_sample_cost >= 0.0


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v38_0_connectors.json")
    assert art["schema_version"] == "v38_0_openrouter_connectors"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v38_0_connectors.json")
    disc = art["disclaimer"].lower()
    assert "real live calls" in disc
    assert "never as canonical truth" in disc
    assert "no api key in the repo" in disc


def test_artifact_no_api_key_leak() -> None:
    art = _load("v38_0_connectors.json")
    assert "sk-or-v1" not in json.dumps(art)


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v38_0_connectors.json")
    required = {
        "api_response_capture", "raw_output_replayability",
        "response_hash_integrity", "model_version_visibility",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v38_0_connectors.json")
    assert art == build_connectors_artifact()
