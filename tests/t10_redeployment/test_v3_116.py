"""v3.116 - T10 structural redeployment tests."""
from __future__ import annotations

import json
import pathlib

from desi.t10_redeployment.decision import (
    REDEPLOY_STRATEGIES,
    RedeployStrategy,
    all_strategy_outcomes,
    best_strategy,
)
from desi.t10_redeployment.report import (
    build_report,
    build_t10_structural_redeployment_artifact,
)


def test_three_strategies() -> None:
    assert len(REDEPLOY_STRATEGIES) == 3


def test_strategy_enum_matches() -> None:
    vals = {s.value for s in RedeployStrategy}
    assert vals == set(REDEPLOY_STRATEGIES)


def test_each_strategy_has_outcome() -> None:
    outs = all_strategy_outcomes()
    assert len(outs) == 3


def test_canonical_has_zero_recovery() -> None:
    canon = next(
        o for o in all_strategy_outcomes()
        if o.strategy
        == RedeployStrategy.CANONICAL_9D.value
    )
    assert canon.recovery_score == 0.0


def test_canonical_has_zero_proxy() -> None:
    canon = next(
        o for o in all_strategy_outcomes()
        if o.strategy
        == RedeployStrategy.CANONICAL_9D.value
    )
    assert canon.proxy_score == 0.0


def test_proxy_alphabet_has_full_recovery() -> None:
    pa = next(
        o for o in all_strategy_outcomes()
        if o.strategy
        == RedeployStrategy.PROXY_ALPHABET.value
    )
    assert pa.recovery_score == 1.0


def test_proxy_alphabet_has_high_proxy_score() -> None:
    pa = next(
        o for o in all_strategy_outcomes()
        if o.strategy
        == RedeployStrategy.PROXY_ALPHABET.value
    )
    # 2 of 3 dims are proxies.
    assert pa.proxy_score >= 0.5


def test_structural_alphabet_has_zero_recovery() -> None:
    sa = next(
        o for o in all_strategy_outcomes()
        if o.strategy
        == RedeployStrategy
        .STRUCTURAL_ALPHABET.value
    )
    assert sa.recovery_score == 0.0


def test_structural_alphabet_has_zero_proxy() -> None:
    sa = next(
        o for o in all_strategy_outcomes()
        if o.strategy
        == RedeployStrategy
        .STRUCTURAL_ALPHABET.value
    )
    assert sa.proxy_score == 0.0


def test_best_strategy_is_proxy_alphabet() -> None:
    """Killerfrage: kann T10 durch echte Struktur
    statt Abkuerzungen ueberleben? NEIN -
    proxy_alphabet wins on ROI because it is the
    only strategy with any recovery."""
    assert best_strategy().strategy == (
        RedeployStrategy.PROXY_ALPHABET.value
    )


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "STRUCTURAL_REDEPLOYMENT",
        "CANONICAL_HELD",
        "PROXY_RETAINED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_proxy_retained() -> None:
    assert build_report().recommendation == (
        "PROXY_RETAINED"
    )


def test_artifact_lists_all_strategies() -> None:
    art = build_t10_structural_redeployment_artifact()
    assert len(art["strategy_outcomes"]) == 3


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_116" / "report.json").read_text(
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
