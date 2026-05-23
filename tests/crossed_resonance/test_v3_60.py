"""v3.60 — crossed resonance tests."""
from __future__ import annotations

import json
import pathlib

from desi.crossed_resonance.conditions import (
    CROSSED_PROBE_RADIUS, CrossedCondition,
    best_explanation_model, interaction_effect,
    per_condition_results,
)
from desi.crossed_resonance.report import (
    build_crossed_resonance_artifact, build_report,
)
from desi.crossed_resonance.transfer import (
    MIN_ANCHORS_FOR_PAIRS,
    corpus_resonance_by_condition,
    crossed_transfer_rate, eligible_corpora,
)


def test_crossed_probe_radius_matches_v350() -> None:
    """Use the v3.50 probe radius (3.5) so the
    crossed test measures the same resonance
    structure under the closed factorial design."""
    assert CROSSED_PROBE_RADIUS == 3.5


def test_crossed_conditions_enum() -> None:
    expected = {
        "same_content_same_method",
        "same_content_diff_method",
        "diff_content_same_method",
        "diff_content_diff_method",
    }
    assert {c.value for c in CrossedCondition} == expected


def test_per_condition_results_count() -> None:
    results = per_condition_results()
    assert len(results) == 4


def test_per_condition_pair_counts_sum_to_190() -> None:
    """C(20, 2) = 190 plateau-anchor pairs distributed
    across the 4 cells."""
    results = per_condition_results()
    assert sum(r.pair_count for r in results) == 190


def test_pair_distribution_empirical() -> None:
    """Empirical: content and method are entangled
    (v3.57 overlap 0.994), so same_content / diff_method
    is empty - any pair sharing content cluster also
    shares method cluster."""
    by_cond = {
        r.condition: r for r in per_condition_results()
    }
    assert by_cond["same_content_same_method"].pair_count == 14
    assert by_cond["same_content_diff_method"].pair_count == 0
    assert by_cond["diff_content_same_method"].pair_count == 80
    assert by_cond["diff_content_diff_method"].pair_count == 96


def test_resonance_concentrated_in_diff_diff() -> None:
    """The killer finding: all 64 v3.50 resonant pairs
    sit in the diff_content / diff_method cell."""
    by_cond = {
        r.condition: r for r in per_condition_results()
    }
    assert by_cond[
        "diff_content_diff_method"
    ].resonant_pair_count == 64
    for cond in (
        "same_content_same_method",
        "same_content_diff_method",
        "diff_content_same_method",
    ):
        assert by_cond[cond].resonant_pair_count == 0


def test_interaction_effect_zero() -> None:
    """Both same-c and same-m cells have rate 0, so
    the interaction proxy is exactly 0."""
    assert interaction_effect(
        per_condition_results(),
    ) == 0.0


def test_best_explanation_model() -> None:
    """All non-same-c/same-m cells contribute except
    one — the verdict is 'INTERACTION_NEGATIVE'
    (resonance happens in the cell where neither
    feature matches, not in any single-matching cell
    or in the coupling cell)."""
    assert best_explanation_model(
        per_condition_results(),
    ) == "INTERACTION_NEGATIVE"


def test_resonance_by_condition_dict() -> None:
    r = build_report()
    expected = {
        "same_content_same_method": 0,
        "same_content_diff_method": 0,
        "diff_content_same_method": 0,
        "diff_content_diff_method": 64,
    }
    assert r.resonance_by_condition == expected


def test_crossed_transfer_rate_is_zero() -> None:
    """Per-corpus, all plateau anchors share both
    content and method cluster (because corpus is the
    dominant axis), so they all fall in cells with
    0 resonance. Hence per-corpus transfer = 0."""
    assert build_report().crossed_transfer_rate == 0.0


def test_eligible_corpora() -> None:
    """v23 (6 anchors) and v314 (3 anchors) are
    eligible; v315/v316 have only 1 anchor each."""
    assert eligible_corpora() == ("v23", "v314")


def test_per_corpus_resonance_empty() -> None:
    """All in-corpus pairs are same-c/same-m which
    produces 0 resonance."""
    r = build_report()
    for c in eligible_corpora():
        assert r.per_corpus_resonance[c] == {}


def test_corpus_resonance_by_condition_returns_dict() -> None:
    out = corpus_resonance_by_condition("v23")
    assert isinstance(out, dict)


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "CROSSED_RESONANCE_TRANSFERS",
        "CROSSED_RESONANCE_GLOBAL_ONLY",
        "CROSSED_RESONANCE_FALSIFIED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_global_only() -> None:
    """Global resonance exists (64 pairs in the
    diff/diff cell) but per-corpus transfer is 0."""
    assert build_report().recommendation == (
        "CROSSED_RESONANCE_GLOBAL_ONLY"
    )


def test_artifact_records_per_corpus() -> None:
    art = build_crossed_resonance_artifact()
    assert set(art["per_corpus_resonance"].keys()) == {
        "v23", "v314",
    }


def test_concept_gate_summary() -> None:
    """All five resonance v2 Concept Gates evaluated
    end-to-end."""
    from desi.content_method.report import (
        build_report as v357,
    )
    from desi.content_only_resonance.report import (
        build_report as v359,
    )
    from desi.method_only_resonance.report import (
        build_report as v358,
    )
    r57 = v357()
    r58 = v358()
    r59 = v359()
    r60 = build_report()
    # Gate 1: decomposition replay
    assert r57.decomposition_replay_stability == 1.0
    # Gate 2: overlap < 0.70 (FAILS empirically)
    assert r57.content_method_overlap >= 0.70
    # Gate 3: any transfer > 0 (FAILS empirically)
    assert (
        r58.method_pair_transfer_rate == 0.0
        and r59.content_pair_transfer_rate == 0.0
        and r60.crossed_transfer_rate == 0.0
    )
    # Gate 4: control_pairs near 0
    assert r58.method_control_pairs == 0
    assert r59.content_control_pairs == 0
    # Gate 5: replay stability across sprints
    assert r58.replay_stability == 1.0
    assert r59.replay_stability == 1.0
    assert r60.replay_stability == 1.0


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_60" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable
