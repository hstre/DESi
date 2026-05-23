"""v3.111 - T10 semantic substitution tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_semantic.report import (
    RECOVERY_THRESHOLD,
    build_report,
    build_t10_semantic_substitution_artifact,
)
from desi.t10_semantic.semantic import (
    SEMANTIC_CANDIDATES,
    SemanticCandidate,
    semantic_value,
)
from desi.t10_semantic.substitute import (
    all_semantic_outcomes,
    complexity_delta,
    semantic_auc,
    semantic_purity,
    semantic_recovery,
)


def test_six_semantic_candidates() -> None:
    assert len(SEMANTIC_CANDIDATES) == 6


def test_semantic_candidate_enum_matches() -> None:
    vals = {c.value for c in SemanticCandidate}
    assert vals == set(SEMANTIC_CANDIDATES)


def test_semantic_value_deterministic() -> None:
    text = "All ravens are black. Therefore."
    for c in SEMANTIC_CANDIDATES:
        a = semantic_value(c, text)
        b = semantic_value(c, text)
        assert a == b


def test_semantic_value_text_dependent() -> None:
    """Different texts should yield different
    mean_word_length most of the time."""
    a = semantic_value(
        SemanticCandidate.MEAN_WORD_LENGTH.value,
        "Cat sat",
    )
    b = semantic_value(
        SemanticCandidate.MEAN_WORD_LENGTH.value,
        "Hippopotamus monstrosity",
    )
    assert a != b


def test_semantic_outcome_count() -> None:
    assert len(all_semantic_outcomes()) == 31


def test_semantic_recovery_in_unit_interval() -> None:
    assert 0.0 <= semantic_recovery() <= 1.0


def test_semantic_recovery_fails_gate() -> None:
    """Concept Gate condition #4:
    semantic_recovery >= 0.70 FAILS. Text-only
    candidates do not substitute for metadata."""
    assert semantic_recovery() < RECOVERY_THRESHOLD


def test_semantic_auc_below_threshold() -> None:
    """Mean AUC across all instances stays below
    the 0.70 separation threshold."""
    assert semantic_auc() < 0.70


def test_complexity_delta_positive() -> None:
    """6 semantic dims vs 3 small_vocab dims =
    +3 dims of complexity."""
    assert complexity_delta() > 0.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "SEMANTIC_SUBSTITUTE_FOUND",
        "SEMANTIC_SUBSTITUTE_PARTIAL",
        "NO_SEMANTIC_SUBSTITUTE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_not_substitute_found() -> None:
    """Killerfrage: gibt es strukturelle
    Alternativen zu den Proxies? NO clean
    substitute exists."""
    assert build_report().recommendation != (
        "SEMANTIC_SUBSTITUTE_FOUND"
    )


def test_artifact_lists_all_outcomes() -> None:
    art = build_t10_semantic_substitution_artifact()
    assert len(art["outcomes"]) == 31


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_111" / "report.json").read_text(
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
