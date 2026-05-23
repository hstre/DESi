"""v5.5 — drift scan: prior-version recommendations and
v2.8 replay hashes are unchanged."""
from __future__ import annotations

from ._helpers import load_artifact


def test_v5_0_recommendation_unchanged() -> None:
    assert load_artifact("v5_0/report.json")[
        "recommendation"
    ] == "METHODOLOGY_TRANSFER_CONFIRMED"


def test_v5_1_recommendation_unchanged() -> None:
    assert load_artifact("v5_1/report.json")[
        "recommendation"
    ] == "TAXONOMY_STABLE"


def test_v5_2_recommendation_unchanged() -> None:
    assert load_artifact("v5_2/report.json")[
        "recommendation"
    ] == "TAXONOMY_GENERALIZES"


def test_v5_3_recommendation_unchanged() -> None:
    assert load_artifact("v5_3/report.json")[
        "recommendation"
    ] == "CORPUS_FIT_TO_TAXONOMY"


def test_v5_4_recommendation_unchanged() -> None:
    assert load_artifact("v5_4/report.json")[
        "recommendation"
    ] == "TAXONOMY_GENERALIZES_PROBES_FAIL"


def test_v2_8_reconstruction_replay_hash_preserved() -> None:
    from desi.repro_audit.report import (
        V2_8_FROZEN_RECONSTRUCTION_HASH,
    )
    assert V2_8_FROZEN_RECONSTRUCTION_HASH == (
        "1f4d9dfe44cb16e1"
    )


def test_v2_8_failcase_replay_hash_preserved() -> None:
    from desi.repro_audit.report import (
        V2_8_FROZEN_FAILCASE_HASH,
    )
    assert V2_8_FROZEN_FAILCASE_HASH == (
        "d83d81ab8417c022"
    )


def test_v4_repro_classes_artifact_intact() -> None:
    matrix = load_artifact(
        "v4_11/replay_matrix.json",
    )["matrix"]
    assert len(matrix) >= 20
    # Every entry carries a repro_class.
    for entry in matrix:
        assert "repro_class" in entry


def test_v5_5_does_not_overwrite_prior_artifacts() -> None:
    """v5.5 may only add docs/papers/, tests/paper_v5/,
    artifacts/v5_5/, docs/memory/. Prior artifacts must
    keep their committed shape."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[2]
    # Spot-check: v5.0 taxonomy.json keeps its anchor.
    tax = load_artifact("v5_0/taxonomy.json")
    assert tax["cluster_count"] == 8
    assert tax["failure_count"] == 346
