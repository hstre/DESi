"""v5.1 — full stability report + recommendation gate."""
from __future__ import annotations

import json
import pathlib

from desi.taxonomy_stability.enums import (
    StabilityRecommendation,
)
from desi.taxonomy_stability.report import (
    build_cluster_mapping_matrix_artifact, build_report,
)


def test_build_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_recommendation_is_closed_enum() -> None:
    allowed = {r.value for r in StabilityRecommendation}
    assert build_report().recommendation in allowed


def test_recommendation_is_stable() -> None:
    r = build_report()
    assert r.recommendation == (
        StabilityRecommendation.STABLE.value
    ), r.rationale


def test_report_rationale_explains_every_gate() -> None:
    r = build_report()
    assert len(r.rationale) >= 9
    for reason in r.rationale:
        assert reason.startswith(("PASS:", "FAIL:"))


def test_perturbation_count_meets_floor() -> None:
    assert build_report().perturbation_count >= 20


def test_nc_count_meets_floor() -> None:
    assert build_report().nc_count >= 100


def test_baseline_cluster_count_locked_at_eight() -> None:
    assert build_report().baseline_cluster_count == 8


def test_report_to_json_round_trips() -> None:
    r = build_report()
    obj = json.loads(r.to_json())
    assert obj["recommendation"] == r.recommendation
    assert obj["perturbation_count"] == r.perturbation_count


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    artifact = json.loads(
        (root / "artifacts" / "v5_1" / "report.json")
        .read_text(encoding="utf-8"),
    )
    live = build_report().to_dict()
    assert artifact == live


def test_artifact_cluster_mapping_matrix_matches_live() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    artifact = json.loads(
        (root / "artifacts" / "v5_1"
         / "cluster_mapping_matrix.json")
        .read_text(encoding="utf-8"),
    )
    live = build_cluster_mapping_matrix_artifact()
    assert artifact == live


def test_artifact_stability_metrics_matches_report() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    artifact = json.loads(
        (root / "artifacts" / "v5_1"
         / "stability_metrics.json")
        .read_text(encoding="utf-8"),
    )
    r = build_report()
    assert artifact["metrics"] == r.metrics.to_dict()
    assert artifact["recommendation"] == r.recommendation
    assert artifact["dominant_cluster"] == (
        "MT_AMBIGUITY_DECISIVENESS"
    )
