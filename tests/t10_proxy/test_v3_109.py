"""v3.109 - T10 metadata ablation tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_proxy.ablation import (
    all_metadata_ablation_outcomes,
    collapsed_candidates,
)
from desi.t10_proxy.metadata import (
    anonymize_id, id_remapping,
    is_metadata_stripped,
)
from desi.t10_proxy.report import (
    AUC_THRESHOLD,
    auc_delta,
    build_report,
    build_t10_metadata_ablation_artifact,
    metadata_free_auc,
    metadata_free_purity,
    rescue_rate,
)


def test_anonymize_id_is_deterministic() -> None:
    a1 = anonymize_id("v314:A01")
    a2 = anonymize_id("v314:A01")
    assert a1 == a2


def test_anonymize_id_distinguishes_inputs() -> None:
    assert anonymize_id("v314:A01") != (
        anonymize_id("v314:A02")
    )


def test_anonymize_id_strips_metadata() -> None:
    """Anonymized ids must NOT contain the
    original corpus or letter prefix."""
    anon = anonymize_id("v314:A01")
    assert "v314" not in anon
    assert is_metadata_stripped(anon)


def test_id_remapping_covers_all_trajectories() -> None:
    remap = id_remapping()
    assert len(remap) > 0
    for orig, anon in remap.items():
        assert anon.startswith("anon:")


def test_metadata_ablation_outcome_count() -> None:
    """One outcome per v3.105 entanglement
    instance."""
    assert len(
        all_metadata_ablation_outcomes(),
    ) == 31


def test_metadata_free_auc_drops_below_gate() -> None:
    """Concept Gate condition #1 FAILS:
    metadata_free_auc < 0.70 ⇒ candidates lean
    on metadata."""
    assert metadata_free_auc() < AUC_THRESHOLD


def test_auc_delta_positive_and_large() -> None:
    """The metadata-aware v3.107 mean AUC was
    1.0; the metadata-free version is much
    lower."""
    assert auc_delta() > 0.30


def test_rescue_rate_collapses() -> None:
    """Almost no instance survives metadata
    ablation."""
    assert rescue_rate() < 0.10


def test_collapsed_candidates_include_corpus_hash() -> None:
    """corpus_hash collapses to a constant under
    anonymization (every anon id has the same
    corpus 'anon')."""
    assert "corpus_hash" in (
        collapsed_candidates()
    )


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "CANDIDATES_SURVIVE_ABLATION",
        "CANDIDATES_PARTIALLY_SURVIVE",
        "CANDIDATES_COLLAPSE_UNDER_ABLATION",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_partial_or_collapse() -> None:
    """Killerfrage: ueberleben die Kandidaten
    ohne Metadaten? Mostly NO."""
    assert build_report().recommendation in {
        "CANDIDATES_PARTIALLY_SURVIVE",
        "CANDIDATES_COLLAPSE_UNDER_ABLATION",
    }


def test_artifact_lists_all_outcomes() -> None:
    art = build_t10_metadata_ablation_artifact()
    assert len(art["outcomes"]) == 31


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_109" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable
