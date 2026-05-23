"""v3.108 - T10 expansion vocabulary tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_vocabulary.decision import (
    all_strategy_outcomes,
    architecture_roi,
    best_strategy,
    complexity_score,
    recovery_score,
    stability_score,
)
from desi.t10_vocabulary.report import (
    build_report,
    build_t10_expansion_vocabulary_artifact,
)
from desi.t10_vocabulary.vocabulary import (
    ExpansionStrategy,
    case_specific_dims,
    single_universal_dims,
    small_vocab_dims,
    strategy_dims,
)


def test_three_strategies_enumerated() -> None:
    """Closed enum: SINGLE_UNIVERSAL,
    SMALL_VOCAB, CASE_SPECIFIC."""
    assert len(
        {s.value for s in ExpansionStrategy},
    ) == 3


def test_single_universal_has_one_dim() -> None:
    assert len(single_universal_dims()) == 1


def test_single_universal_uses_contradiction_type() -> None:
    assert "contradiction_type" in (
        single_universal_dims()
    )


def test_small_vocab_includes_contradiction_type() -> None:
    assert "contradiction_type" in (
        small_vocab_dims()
    )


def test_small_vocab_includes_adaptive_candidates() -> None:
    """The small vocab must contain at least one
    of the v3.107 adaptive candidates."""
    from desi.t10_adaptive.adaptive import (
        ADAPTIVE_CANDIDATES,
    )
    used = set(small_vocab_dims())
    assert used & set(ADAPTIVE_CANDIDATES)


def test_case_specific_supersets_single() -> None:
    """case_specific includes contradiction_type
    plus whatever v3.107 chose for the failed
    cases."""
    assert "contradiction_type" in (
        case_specific_dims()
    )


def test_all_strategies_have_outcomes() -> None:
    outs = all_strategy_outcomes()
    assert len(outs) == 3


def test_recovery_score_in_unit_interval() -> None:
    for s in ExpansionStrategy:
        v = recovery_score(s.value)
        assert 0.0 <= v <= 1.0


def test_complexity_score_in_unit_interval() -> None:
    for s in ExpansionStrategy:
        v = complexity_score(s.value)
        assert 0.0 <= v <= 1.0


def test_stability_score_is_one() -> None:
    """All strategies are 0-adverse-flip by
    construction."""
    for s in ExpansionStrategy:
        assert stability_score(s.value) == 1.0


def test_single_universal_has_lowest_complexity() -> None:
    sing = complexity_score(
        ExpansionStrategy.SINGLE_UNIVERSAL.value,
    )
    small = complexity_score(
        ExpansionStrategy.SMALL_VOCAB.value,
    )
    case = complexity_score(
        ExpansionStrategy.CASE_SPECIFIC.value,
    )
    assert sing <= small
    assert sing <= case


def test_small_vocab_has_max_recovery() -> None:
    """The small alphabet recovers every G/E +
    every v3.105 instance."""
    assert recovery_score(
        ExpansionStrategy.SMALL_VOCAB.value,
    ) == 1.0


def test_best_strategy_recovery_is_max() -> None:
    """Killerfrage decision criterion: best
    strategy must achieve top recovery."""
    best = best_strategy()
    max_rec = max(
        recovery_score(s.value)
        for s in ExpansionStrategy
    )
    assert best.recovery_score == max_rec


def test_best_strategy_is_small_vocab() -> None:
    """Killerfrage: ist T10 ein einzelner
    Schluessel - oder ein ganzes Alphabet? A
    SMALL alphabet of 3 keys
    (contradiction_type + corpus_hash +
    letter_prefix_hash)."""
    assert best_strategy().strategy == (
        ExpansionStrategy.SMALL_VOCAB.value
    )


def test_best_strategy_dims_count_is_three() -> None:
    assert len(best_strategy().dims) == 3


def test_architecture_roi_positive() -> None:
    assert architecture_roi(
        best_strategy().strategy,
    ) > 0.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_small_alphabet() -> None:
    assert build_report().recommendation == (
        "T10_IS_SMALL_ALPHABET"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "T10_IS_SINGLE_KEY",
        "T10_IS_SMALL_ALPHABET",
        "T10_IS_PER_CASE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_lists_all_strategies() -> None:
    art = build_t10_expansion_vocabulary_artifact()
    assert len(art["strategy_outcomes"]) == 3


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_108" / "report.json").read_text(
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
