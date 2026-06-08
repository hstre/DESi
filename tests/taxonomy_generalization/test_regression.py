"""v5.2 — regression: forbidden roots untouched, no v5.0
or v5.1 artifact rewrites, no taxonomy renaming."""
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


def test_v5_0_report_artifact_unchanged() -> None:
    doc = json.loads(
        (_REPO / "artifacts" / "v5_0" / "report.json")
        .read_text(encoding="utf-8"),
    )
    assert doc["recommendation"] == (
        "METHODOLOGY_TRANSFER_CONFIRMED"
    )
    assert doc["corpus_size"] == 565


def test_v5_1_stability_artifact_unchanged() -> None:
    doc = json.loads(
        (_REPO / "artifacts" / "v5_1"
         / "stability_metrics.json")
        .read_text(encoding="utf-8"),
    )
    assert doc["recommendation"] == "TAXONOMY_STABLE"


def test_v52_writes_only_under_allowed_paths() -> None:
    a = _REPO / "artifacts" / "v5_2"
    assert (a / "report.json").is_file()
    assert (a / "classification_matrix.json").is_file()


def test_v52_does_not_modify_forbidden_runtime() -> None:
    forbidden = (
        "src/desi/logic", "src/desi/frames",
        "src/desi/frame_tension",
        "src/desi/frame_inference",
        "src/desi/recursive", "src/desi/consilium",
        "src/desi/tools",
    )
    pkg = _REPO / "src" / "desi" / "taxonomy_generalization"
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


def test_v5_0_methodology_transfer_still_confirmed() -> None:
    from desi.methodology_transfer.report import (
        build_report,
    )
    assert build_report().recommendation == (
        "METHODOLOGY_TRANSFER_CONFIRMED"
    )


def test_v5_1_taxonomy_stability_still_stable() -> None:
    from desi.taxonomy_stability.report import (
        build_report,
    )
    assert build_report().recommendation == (
        "TAXONOMY_STABLE"
    )


def test_canonical_class_names_unchanged() -> None:
    from desi.taxonomy_generalization.canonical import (
        load_canonical_reference,
    )
    expected = {
        "MT_AMBIGUITY_DECISIVENESS",
        "MT_AUDIT_OVER_BLOCK",
        "MT_AUDIT_OVER_SUPPORT",
        "MT_MODAL_ASYMMETRY",
        "MT_NEGATION_ASYMMETRY",
        "MT_NOVEL_ENTITY",
        "MT_OVERLAP_LOOP",
        "MT_UNIVERSAL_LEAP",
    }
    assert set(
        load_canonical_reference().class_names
    ) == expected
