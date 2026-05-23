"""v5.2 — full generalization report + recommendation
gate."""
from __future__ import annotations

import json
import pathlib

from desi.taxonomy_generalization.enums import (
    GeneralizationRecommendation,
)
from desi.taxonomy_generalization.report import (
    build_classification_matrix_artifact, build_report,
)


def test_build_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_recommendation_is_closed_enum() -> None:
    allowed = {
        r.value for r in GeneralizationRecommendation
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_generalizes() -> None:
    r = build_report()
    assert r.recommendation == (
        GeneralizationRecommendation.GENERALIZES.value
    ), r.rationale


def test_rationale_explains_every_gate() -> None:
    r = build_report()
    assert len(r.rationale) >= 10
    for reason in r.rationale:
        assert reason.startswith(("PASS:", "FAIL:"))


def test_corpus_size_in_report() -> None:
    assert build_report().corpus_size >= 500


def test_nc_count_meets_floor() -> None:
    assert build_report().nc_count >= 100


def test_safe_probe_false_activation_is_zero() -> None:
    assert build_report().safe_probe_false_activation == 0


def test_report_to_json_round_trips() -> None:
    r = build_report()
    obj = json.loads(r.to_json())
    assert obj["recommendation"] == r.recommendation
    assert obj["corpus_size"] == r.corpus_size


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    artifact = json.loads(
        (root / "artifacts" / "v5_2" / "report.json")
        .read_text(encoding="utf-8"),
    )
    live = build_report().to_dict()
    assert artifact == live


def test_artifact_classification_matrix_matches_live() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    artifact = json.loads(
        (root / "artifacts" / "v5_2"
         / "classification_matrix.json")
        .read_text(encoding="utf-8"),
    )
    live = build_classification_matrix_artifact()
    assert artifact == live
