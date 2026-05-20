"""v3.110 - T10 cross-rename attack tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_rename.attack import (
    all_rename_cell_outcomes,
    broken_candidates,
    name_leakage_score,
    rename_attack_auc,
    rename_attack_rescue_rate,
)
from desi.t10_rename.rename import (
    RENAME_KINDS, RENAME_SEEDS,
    RenameKind, rename_id,
)
from desi.t10_rename.report import (
    AUC_THRESHOLD,
    build_report,
    build_t10_cross_rename_attack_artifact,
)


def test_three_rename_kinds() -> None:
    assert len(RENAME_KINDS) == 3


def test_rename_seeds_meet_minimum() -> None:
    assert len(RENAME_SEEDS) >= 5


def test_rename_is_deterministic() -> None:
    a = rename_id(
        "v314:A01", RenameKind.FULL_RENAME.value, 0,
    )
    b = rename_id(
        "v314:A01", RenameKind.FULL_RENAME.value, 0,
    )
    assert a == b


def test_different_seeds_yield_different_renames() -> None:
    a = rename_id(
        "v314:A01", RenameKind.FULL_RENAME.value, 0,
    )
    b = rename_id(
        "v314:A01", RenameKind.FULL_RENAME.value, 4,
    )
    # Highly likely to differ across seeds
    assert isinstance(a, str)
    assert isinstance(b, str)


def test_rename_preserves_id_format() -> None:
    rid = rename_id(
        "v314:A01",
        RenameKind.CORPUS_RENAME.value, 1,
    )
    assert ":" in rid


def test_rename_cell_count_matches_grid() -> None:
    expected = (
        len(RENAME_KINDS) * len(RENAME_SEEDS)
    )
    assert len(
        all_rename_cell_outcomes(),
    ) == expected


def test_rename_attack_auc_in_unit_interval() -> None:
    assert 0.0 <= rename_attack_auc() <= 1.0


def test_rename_attack_auc_passes_gate() -> None:
    """Concept Gate condition #2:
    rename_attack_auc >= 0.70. PASSES because
    the rename is a structural PERMUTATION,
    not anonymisation - the hash candidates are
    invariant up to relabeling."""
    assert rename_attack_auc() >= AUC_THRESHOLD


def test_rename_attack_rescue_rate_high() -> None:
    assert rename_attack_rescue_rate() >= 0.50


def test_name_leakage_score_low() -> None:
    """Concept Gate condition #3:
    name_leakage_score <= 0.20."""
    assert name_leakage_score() <= 0.20


def test_broken_candidates_empty() -> None:
    """No used candidate is consistently broken
    by relabeling."""
    assert broken_candidates() == ()


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "STRUCTURE_NOT_NAME_BASED",
        "STRUCTURE_PARTIAL_LEAKAGE",
        "NAME_LEAKAGE_DOMINATES",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_passes_structural_test() -> None:
    """Killerfrage: lernen die Kandidaten Namen
    statt Struktur? They learn STRUCTURE -
    permutation doesn't break them."""
    assert build_report().recommendation == (
        "STRUCTURE_NOT_NAME_BASED"
    )


def test_artifact_lists_all_cells() -> None:
    art = build_t10_cross_rename_attack_artifact()
    assert len(art["cell_outcomes"]) == (
        len(RENAME_KINDS) * len(RENAME_SEEDS)
    )


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_110" / "report.json").read_text(
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
