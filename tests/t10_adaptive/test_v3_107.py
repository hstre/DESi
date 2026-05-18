"""v3.107 - T10 adaptive candidate search tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_adaptive.adaptive import (
    ADAPTIVE_CANDIDATES, ALL_CANDIDATES,
    AdaptiveCandidate, adaptive_value,
)
from desi.t10_adaptive.report import (
    build_report,
    build_t10_adaptive_candidates_artifact,
    candidate_vocab_size,
    mean_candidate_auc,
    new_candidate_count,
    rescue_rate,
    reused_candidates,
    used_candidates,
)
from desi.t10_adaptive.search import (
    all_adaptive_outcomes,
)


def test_adaptive_candidate_count_is_four() -> None:
    assert len(ADAPTIVE_CANDIDATES) == 4


def test_all_candidates_includes_v3101_taxonomy() -> None:
    """ALL_CANDIDATES extends the v3.101 taxonomy
    with the v3.107 adaptive enrichments."""
    from desi.t10.candidate import CANDIDATE_DIMS
    for c in CANDIDATE_DIMS:
        assert c in ALL_CANDIDATES
    for c in ADAPTIVE_CANDIDATES:
        assert c in ALL_CANDIDATES


def test_letter_prefix_hash_for_v314_a() -> None:
    """A -> 0."""
    v = adaptive_value(
        AdaptiveCandidate.LETTER_PREFIX_HASH.value,
        "v314:A01", "anything",
    )
    assert v == 0.0


def test_letter_prefix_hash_for_v314_b() -> None:
    """B -> 1."""
    v = adaptive_value(
        AdaptiveCandidate.LETTER_PREFIX_HASH.value,
        "v314:B05", "anything",
    )
    assert v == 1.0


def test_corpus_hash_deterministic() -> None:
    v1 = adaptive_value(
        AdaptiveCandidate.CORPUS_HASH.value,
        "v314:X01", "anything",
    )
    v2 = adaptive_value(
        AdaptiveCandidate.CORPUS_HASH.value,
        "v314:Y99", "different text",
    )
    assert v1 == v2


def test_corpus_hash_distinguishes_corpora() -> None:
    v1 = adaptive_value(
        AdaptiveCandidate.CORPUS_HASH.value,
        "v314:X01", "anything",
    )
    v2 = adaptive_value(
        AdaptiveCandidate.CORPUS_HASH.value,
        "v316-surv:X01", "anything",
    )
    assert v1 != v2


def test_adaptive_outcome_count_is_thirty_one() -> None:
    assert len(all_adaptive_outcomes()) == 31


def test_rescue_rate_is_one() -> None:
    """Killerfrage: braucht T10 eine Familie von
    Erweiterungen? Yes - but a SMALL one. With
    the 4 adaptive candidates added to v3.101's
    6, every hidden entanglement is rescued."""
    assert rescue_rate() == 1.0


def test_candidate_vocab_size_small() -> None:
    """A small vocabulary suffices."""
    assert candidate_vocab_size() <= 4


def test_candidate_vocab_size_at_least_one() -> None:
    assert candidate_vocab_size() >= 1


def test_used_candidates_include_adaptive() -> None:
    """At least one v3.107-only candidate is
    needed (v3.101's contradiction_type alone
    failed v3.106)."""
    used = set(used_candidates())
    assert used & set(ADAPTIVE_CANDIDATES)


def test_reused_candidates_subset_of_used() -> None:
    used = set(used_candidates())
    for c in reused_candidates():
        assert c in used


def test_new_candidate_count_positive() -> None:
    """At least one adaptive candidate is
    actually picked as best."""
    assert new_candidate_count() >= 1


def test_mean_candidate_auc_above_threshold() -> None:
    """Mean AUC across all adaptive outcomes
    should clear 0.70."""
    assert mean_candidate_auc() >= 0.70


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "SINGLE_KEY_SUFFICES",
        "VOCAB_NEEDED_BUT_INCOMPLETE",
        "VOCAB_RESCUES_BROADLY",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_vocab_rescues_broadly() -> None:
    """With rescue_rate = 1.0 and candidate_vocab
    > 1, the verdict must be
    VOCAB_RESCUES_BROADLY."""
    assert build_report().recommendation == (
        "VOCAB_RESCUES_BROADLY"
    )


def test_artifact_lists_all_outcomes() -> None:
    art = build_t10_adaptive_candidates_artifact()
    assert len(art["adaptive_outcomes"]) == 31


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_107" / "report.json").read_text(
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
