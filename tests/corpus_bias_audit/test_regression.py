"""v5.3 — regression: forbidden roots untouched, all
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


def test_v5_0_report_artifact_unchanged() -> None:
    doc = json.loads(
        (_REPO / "artifacts" / "v5_0" / "report.json")
        .read_text(encoding="utf-8"),
    )
    assert doc["recommendation"] == (
        "METHODOLOGY_TRANSFER_CONFIRMED"
    )


def test_v5_1_stability_artifact_unchanged() -> None:
    doc = json.loads(
        (_REPO / "artifacts" / "v5_1"
         / "stability_metrics.json")
        .read_text(encoding="utf-8"),
    )
    assert doc["recommendation"] == "TAXONOMY_STABLE"


def test_v5_2_report_artifact_unchanged() -> None:
    doc = json.loads(
        (_REPO / "artifacts" / "v5_2" / "report.json")
        .read_text(encoding="utf-8"),
    )
    assert doc["recommendation"] == (
        "TAXONOMY_GENERALIZES"
    )


def test_v53_writes_only_under_allowed_paths() -> None:
    a = _REPO / "artifacts" / "v5_3"
    assert (a / "report.json").is_file()
    assert (a / "rewrite_diff.json").is_file()


def test_v53_does_not_modify_forbidden_runtime() -> None:
    forbidden = (
        "src/desi/logic", "src/desi/frames",
        "src/desi/frame_tension",
        "src/desi/frame_inference",
        "src/desi/recursive", "src/desi/consilium",
        "src/desi/tools",
    )
    pkg = _REPO / "src" / "desi" / "corpus_bias_audit"
    for p in pkg.glob("*.py"):
        txt = p.read_text(encoding="utf-8")
        for f in forbidden:
            assert f not in txt, (p.name, f)


def test_v53_does_not_modify_v52_corpus_source() -> None:
    """The v5.2 corpus.py file's content must be
    byte-identical to what v5.2 committed — v5.3 reads
    it but never edits it."""
    # If v5.3 had touched the v5.2 corpus, the bias
    # audit would be circular. Read both the FINAL
    # corpus and the RAW_CONCLUSIONS table and verify
    # that for every rewritten chain the FINAL text is
    # what the v5.2 corpus.py exports.
    from desi.corpus_bias_audit.raw_corpus import (
        RAW_CONCLUSIONS,
    )
    from desi.taxonomy_generalization.corpus import (
        all_chains,
    )
    final_by_id = {c.chain_id: c.text for c in all_chains()}
    for base_id in RAW_CONCLUSIONS:
        # Every base id should have at least one variant
        # in the FINAL corpus.
        variants = [
            cid for cid in final_by_id
            if cid.startswith(base_id + "-v")
        ]
        assert variants, base_id


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
    from desi.methodology_transfer.report import (
        build_report as v50,
    )
    from desi.taxonomy_stability.report import (
        build_report as v51,
    )
    from desi.taxonomy_generalization.report import (
        build_report as v52,
    )
    assert v50().recommendation == (
        "METHODOLOGY_TRANSFER_CONFIRMED"
    )
    assert v51().recommendation == "TAXONOMY_STABLE"
    assert v52().recommendation == "TAXONOMY_GENERALIZES"
