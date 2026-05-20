"""v5.5 — required v5.x recommendations and v4 repro
class claims must be present."""
from __future__ import annotations

from ._helpers import load_claims


_REQUIRED_FINDINGS = {
    "METHODOLOGY_TRANSFER_CONFIRMED",
    "TAXONOMY_STABLE",
    "TAXONOMY_GENERALIZES",
    "CORPUS_FIT_TO_TAXONOMY",
    "TAXONOMY_GENERALIZES_PROBES_FAIL",
}


def test_every_required_finding_has_claim() -> None:
    expected_values = {
        c["expected_value"] for c in load_claims()
        if c["field_path"] == "recommendation"
    }
    missing = _REQUIRED_FINDINGS - expected_values
    assert not missing, missing


def test_v50_recommendation_claim_present() -> None:
    assert any(
        c["artifact"] == "v5_0/report.json"
        and c["field_path"] == "recommendation"
        and c["expected_value"] == (
            "METHODOLOGY_TRANSFER_CONFIRMED"
        )
        for c in load_claims()
    )


def test_v51_recommendation_claim_present() -> None:
    assert any(
        c["artifact"] == "v5_1/report.json"
        and c["field_path"] == "recommendation"
        and c["expected_value"] == "TAXONOMY_STABLE"
        for c in load_claims()
    )


def test_v52_recommendation_claim_present() -> None:
    assert any(
        c["artifact"] == "v5_2/report.json"
        and c["field_path"] == "recommendation"
        and c["expected_value"] == "TAXONOMY_GENERALIZES"
        for c in load_claims()
    )


def test_v53_recommendation_claim_present() -> None:
    assert any(
        c["artifact"] == "v5_3/report.json"
        and c["field_path"] == "recommendation"
        and c["expected_value"] == "CORPUS_FIT_TO_TAXONOMY"
        for c in load_claims()
    )


def test_v54_recommendation_claim_present() -> None:
    assert any(
        c["artifact"] == "v5_4/report.json"
        and c["field_path"] == "recommendation"
        and c["expected_value"] == (
            "TAXONOMY_GENERALIZES_PROBES_FAIL"
        )
        for c in load_claims()
    )


def test_v4_repro_artifacts_pinned() -> None:
    artifacts = {c["artifact"] for c in load_claims()}
    assert "v4_11/replay_matrix.json" in artifacts
    assert "v4_12/report.json" in artifacts
