"""v3.106 - T10 transfer test tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_transfer.inject import (
    all_transfer_outcomes,
)
from desi.t10_transfer.report import (
    TRANSFER_THRESHOLD,
    build_report,
    build_t10_transfer_test_artifact,
)
from desi.t10_transfer.transfer import (
    failed_cases,
    mean_auc_gain,
    rescued_cases,
    transfer_rate,
)


def test_transfer_outcome_per_entanglement_instance() -> None:
    """One TransferOutcome per v3.105 instance."""
    from desi.t10_generalization.census import (
        all_entanglement_instances,
    )
    assert len(all_transfer_outcomes()) == len(
        all_entanglement_instances(),
    )


def test_transfer_outcome_count_is_thirty_one() -> None:
    assert len(all_transfer_outcomes()) == 31


def test_transfer_rate_in_unit_interval() -> None:
    assert 0.0 <= transfer_rate() <= 1.0


def test_transfer_rate_is_zero() -> None:
    """Killerfrage: ist contradiction_type
    universell? No - it rescues zero of the 31
    hidden entanglements."""
    assert transfer_rate() == 0.0


def test_transfer_rate_below_concept_gate() -> None:
    """Concept Gate condition #2: transfer_rate
    >= 0.50 - this FAILS, confirming T10 is
    G/E-specific."""
    assert transfer_rate() < TRANSFER_THRESHOLD


def test_mean_auc_gain_is_zero() -> None:
    """Adding contradiction_type=0 to every
    member (because the syllogism families
    contain no circular predicates) is a
    constant slot ⇒ pairwise distances are
    unchanged ⇒ AUC unchanged."""
    assert mean_auc_gain() == 0.0


def test_rescued_cases_empty() -> None:
    assert rescued_cases() == ()


def test_failed_cases_covers_all() -> None:
    assert len(failed_cases()) == len(
        all_transfer_outcomes(),
    )


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_ge_specific() -> None:
    assert build_report().recommendation == (
        "T10_GE_SPECIFIC"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "T10_TRANSFERS_BROADLY",
        "T10_TRANSFERS_PARTIAL",
        "T10_GE_SPECIFIC",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_lists_all_outcomes() -> None:
    art = build_t10_transfer_test_artifact()
    assert len(art["transfer_outcomes"]) == 31


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_106" / "report.json").read_text(
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
