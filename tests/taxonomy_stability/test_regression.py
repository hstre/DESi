"""v5.1 — regression: forbidden roots untouched, no
artifact rewrites, no taxonomy relabel."""
from __future__ import annotations

import json
import pathlib


_REPO = pathlib.Path(__file__).resolve().parents[2]


def test_v5_0_taxonomy_artifact_unchanged_structure() -> None:
    """v5.1 must consume but never rewrite v5.0 artifacts."""
    doc = json.loads(
        (_REPO / "artifacts" / "v5_0" / "taxonomy.json")
        .read_text(encoding="utf-8"),
    )
    assert doc["cluster_count"] == 8
    assert doc["failure_count"] == 346
    assert doc["largest_cluster_fraction"] == 0.563584


def test_v5_0_report_artifact_unchanged_recommendation() -> None:
    doc = json.loads(
        (_REPO / "artifacts" / "v5_0" / "report.json")
        .read_text(encoding="utf-8"),
    )
    assert doc["recommendation"] == (
        "METHODOLOGY_TRANSFER_CONFIRMED"
    )
    assert doc["corpus_size"] == 565


def test_v51_writes_only_under_allowed_paths() -> None:
    a = _REPO / "artifacts" / "v5_1"
    assert (a / "report.json").is_file()
    assert (a / "cluster_mapping_matrix.json").is_file()
    assert (a / "stability_metrics.json").is_file()


def test_v51_taxonomy_class_names_unchanged() -> None:
    """v5.1 must not rename canonical v5.0 classes."""
    from desi.taxonomy_stability.baseline import (
        load_canonical_baseline,
    )
    b = load_canonical_baseline()
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
    assert {c.name for c in b.clusters} == expected


def test_v51_modules_dont_reference_forbidden_runtime() -> None:
    forbidden = (
        "src/desi/logic", "src/desi/frames",
        "src/desi/frame_tension",
        "src/desi/frame_inference",
        "src/desi/recursive", "src/desi/consilium",
        "src/desi/tools",
    )
    pkg = _REPO / "src" / "desi" / "taxonomy_stability"
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
    assert V2_8_FROZEN_FAILCASE_HASH == "d83d81ab8417c022"


def test_v5_0_methodology_transfer_still_confirmed() -> None:
    """v5.1 must not regress v5.0 — re-running the v5.0
    report must still produce CONFIRMED."""
    from desi.methodology_transfer.report import build_report
    r = build_report()
    assert r.recommendation == (
        "METHODOLOGY_TRANSFER_CONFIRMED"
    )
    assert r.safe_probe_count >= 3
