"""v37.0 - Audit Scenario Connector Layer tests."""
from __future__ import annotations

import json
import pathlib

from desi.audit_benchmarks import (
    all_cross_refs, all_financial_claims, all_narrative_claims,
    build_connectors_artifact, build_report, claim_visibility,
    connector_metrics, cross_document_mapping,
    financial_statement_alignment, kinds, narrative_visibility,
    provenance, replay_stability, scenarios,
)
from desi.audit_benchmarks.report import (
    REPORT_VERDICTS, VERDICT_STRUCTURED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "audit_benchmarks"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- scenarios loaded ---------------------------
def test_scenarios_loaded() -> None:
    assert len(scenarios()) == 4
    assert provenance() == "offline_reference_dataset"


def test_claims_surfaced() -> None:
    assert len(all_financial_claims()) == 6
    assert len(all_narrative_claims()) == 5


# --- visibility / mapping -----------------------
def test_claim_visibility_full() -> None:
    assert claim_visibility() == 1.0
    assert narrative_visibility() == 1.0


def test_cross_document_mapping_full() -> None:
    assert cross_document_mapping() == 1.0
    assert len(all_cross_refs()) == 11


def test_cross_ref_kinds() -> None:
    assert "narrative_to_number" in kinds()
    assert "number_to_footnote" in kinds()


def test_financial_statement_alignment_full() -> None:
    assert financial_statement_alignment() == 1.0


# --- governance / replay ------------------------
def test_governance_and_replay() -> None:
    m = connector_metrics()
    assert m["governance_identity"] == 1.0
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in connector_metrics().values():
        assert 0.0 <= v <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_structured() -> None:
    assert build_report().recommendation == VERDICT_STRUCTURED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v37_0_connectors.json")
    assert art["schema_version"] == "v37_0_audit_connectors"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v37_0_connectors.json")
    disc = art["disclaimer"].lower()
    assert "not official exam content" in disc
    assert "not to replace auditors" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v37_0_connectors.json")
    required = {
        "claim_visibility", "cross_document_mapping",
        "financial_statement_alignment", "governance_identity",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v37_0_connectors.json")
    assert art == build_connectors_artifact()
