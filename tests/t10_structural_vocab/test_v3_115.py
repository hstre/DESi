"""v3.115 - structural vocab tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_structural_vocab.report import (
    RECOVERY_THRESHOLD,
    build_report,
    build_t10_structural_vocab_artifact,
)
from desi.t10_structural_vocab.search import (
    MAX_VOCAB_SIZE,
    all_subset_outcomes,
    best_subset,
)
from desi.t10_structural_vocab.vocab import (
    complexity_cost,
    mean_auc,
    minimal_vocab_size,
    vocab_recovery,
)


def test_max_vocab_size_is_three() -> None:
    assert MAX_VOCAB_SIZE == 3


def test_subset_count_matches_combinations() -> None:
    """C(12,1)+C(12,2)+C(12,3) = 12+66+220 = 298."""
    assert len(all_subset_outcomes()) == 298


def test_vocab_recovery_in_unit_interval() -> None:
    assert 0.0 <= vocab_recovery() <= 1.0


def test_vocab_recovery_is_zero() -> None:
    """Killerfrage: gibt es ein echtes
    strukturelles Alphabet? Nein - even the
    best 3-subset rescues 0 of 31 instances."""
    assert vocab_recovery() == 0.0


def test_vocab_recovery_below_gate() -> None:
    """Concept Gate condition #5: vocab_recovery
    >= 0.90 FAILS."""
    assert vocab_recovery() < RECOVERY_THRESHOLD


def test_best_subset_is_nonempty() -> None:
    assert len(best_subset().subset) >= 1


def test_minimal_vocab_size_low() -> None:
    """Best subset prefers fewer dims when all
    are equally useless (which they are)."""
    assert minimal_vocab_size() == 1


def test_mean_auc_is_chance() -> None:
    assert mean_auc() == 0.5


def test_complexity_cost_in_unit_interval() -> None:
    assert 0.0 <= complexity_cost() <= 1.0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "STRUCTURAL_ALPHABET_FOUND",
        "STRUCTURAL_ALPHABET_PARTIAL",
        "NO_STRUCTURAL_ALPHABET",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_no_alphabet() -> None:
    assert build_report().recommendation == (
        "NO_STRUCTURAL_ALPHABET"
    )


def test_artifact_lists_all_subsets() -> None:
    art = build_t10_structural_vocab_artifact()
    assert len(art["subset_outcomes"]) == 298


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_115" / "report.json").read_text(
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
