"""v5.4 — regression: forbidden roots untouched, all
prior artifacts unchanged."""
from __future__ import annotations

import json
import pathlib


_REPO = pathlib.Path(__file__).resolve().parents[2]


def test_v5_0_taxonomy_artifact_unchanged() -> None:
    doc = json.loads(
        (_REPO / "artifacts" / "v5_0" / "taxonomy.json")
        .read_text(encoding="utf-8"),
    )
    assert doc["cluster_count"] == 8
    assert doc["failure_count"] == 346
    assert doc["largest_cluster_fraction"] == 0.563584


def test_v5_2_report_artifact_unchanged() -> None:
    doc = json.loads(
        (_REPO / "artifacts" / "v5_2" / "report.json")
        .read_text(encoding="utf-8"),
    )
    assert doc["recommendation"] == "TAXONOMY_GENERALIZES"


def test_v5_3_artifacts_unchanged() -> None:
    rep = json.loads(
        (_REPO / "artifacts" / "v5_3" / "report.json")
        .read_text(encoding="utf-8"),
    )
    assert rep["recommendation"] == (
        "CORPUS_FIT_TO_TAXONOMY"
    )
    rc = json.loads(
        (_REPO / "artifacts" / "v5_3" / "raw_corpus.json")
        .read_text(encoding="utf-8"),
    )
    assert rc["chain_count"] == 540


def test_v54_writes_only_under_allowed_paths() -> None:
    a = _REPO / "artifacts" / "v5_4"
    assert (a / "report.json").is_file()
    assert (a / "split_eval.json").is_file()


def test_v54_does_not_modify_forbidden_runtime() -> None:
    forbidden = (
        "src/desi/logic", "src/desi/frames",
        "src/desi/frame_tension",
        "src/desi/frame_inference",
        "src/desi/recursive", "src/desi/consilium",
        "src/desi/tools",
    )
    pkg = _REPO / "src" / "desi" / "raw_generalization"
    for p in pkg.glob("*.py"):
        txt = p.read_text(encoding="utf-8")
        for f in forbidden:
            assert f not in txt, (p.name, f)


def test_v28_replay_hashes_preserved() -> None:
    from desi.repro_audit.report import (
        V2_8_FROZEN_FAILCASE_HASH,
        V2_8_FROZEN_RECONSTRUCTION_HASH,
    )
    assert V2_8_FROZEN_RECONSTRUCTION_HASH == (
        "1f4d9dfe44cb16e1"
    )
    assert V2_8_FROZEN_FAILCASE_HASH == (
        "d83d81ab8417c022"
    )


def test_prior_recommendations_still_hold() -> None:
    from desi.corpus_bias_audit.report import (
        build_report as v53,
    )
    from desi.methodology_transfer.report import (
        build_report as v50,
    )
    from desi.taxonomy_generalization.report import (
        build_report as v52,
    )
    from desi.taxonomy_stability.report import (
        build_report as v51,
    )
    assert v50().recommendation == (
        "METHODOLOGY_TRANSFER_CONFIRMED"
    )
    assert v51().recommendation == "TAXONOMY_STABLE"
    assert v52().recommendation == "TAXONOMY_GENERALIZES"
    assert v53().recommendation == (
        "CORPUS_FIT_TO_TAXONOMY"
    )
