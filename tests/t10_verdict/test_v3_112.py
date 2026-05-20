"""v3.112 - T10 proxy verdict tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_verdict.report import (
    VALIDATED_VOCAB_MIN,
    build_report,
    build_t10_proxy_verdict_artifact,
)
from desi.t10_verdict.verdict import (
    DimVerdict,
    SMALL_VOCAB_DIMS,
    all_classifications,
    ambiguous_dims,
    classify,
    epistemic_dims,
    proxy_dims,
    validated_vocab_size,
)


def test_small_vocab_has_three_dims() -> None:
    assert len(SMALL_VOCAB_DIMS) == 3


def test_classify_contradiction_type_epistemic() -> None:
    assert classify("contradiction_type") == (
        DimVerdict.EPISTEMIC.value
    )


def test_classify_corpus_hash_proxy() -> None:
    assert classify("corpus_hash") == (
        DimVerdict.PROXY.value
    )


def test_classify_letter_prefix_hash_proxy() -> None:
    assert classify("letter_prefix_hash") == (
        DimVerdict.PROXY.value
    )


def test_classify_unknown_is_ambiguous() -> None:
    assert classify("unknown_xyz") == (
        DimVerdict.AMBIGUOUS.value
    )


def test_all_classifications_cover_small_vocab() -> None:
    classed = {
        c.dim for c in all_classifications()
    }
    assert classed == set(SMALL_VOCAB_DIMS)


def test_epistemic_dims_only_contradiction_type() -> None:
    assert epistemic_dims() == (
        "contradiction_type",
    )


def test_proxy_dims_include_metadata_candidates() -> None:
    pd = set(proxy_dims())
    assert "corpus_hash" in pd
    assert "letter_prefix_hash" in pd


def test_ambiguous_dims_empty() -> None:
    """All three small-vocab dims have a
    clean verdict."""
    assert ambiguous_dims() == ()


def test_validated_vocab_size_is_one() -> None:
    """Killerfrage: habe ich ein epistemisches
    Alphabet - oder nur Dataset-Shortcuts? Only
    one of the three small-vocab dims survives
    as epistemic."""
    assert validated_vocab_size() == 1


def test_validated_vocab_size_below_minimum() -> None:
    """Concept Gate condition #5:
    validated_vocab_size >= 2. FAILS."""
    assert validated_vocab_size() < (
        VALIDATED_VOCAB_MIN
    )


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_single_dim() -> None:
    assert build_report().recommendation == (
        "SINGLE_EPISTEMIC_DIM_ONLY"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "EPISTEMIC_VOCAB_VALIDATED",
        "SINGLE_EPISTEMIC_DIM_ONLY",
        "NO_EPISTEMIC_VOCAB",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_has_classifications() -> None:
    art = build_t10_proxy_verdict_artifact()
    assert len(art["classifications"]) == 3


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_112" / "report.json").read_text(
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
