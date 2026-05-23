"""v3.59 — content-only resonance tests."""
from __future__ import annotations

import json
import pathlib

from desi.content_only_resonance.probe import (
    CONTENT_PROBE_RADIUS, MIN_ANCHORS_FOR_PAIRS,
    eligible_corpora, global_control_summary,
    global_plateau_summary, ineligible_corpora,
    per_corpus_control_summary,
    per_corpus_plateau_summary,
)
from desi.content_only_resonance.report import (
    build_content_resonance_artifact, build_report,
)


def test_content_probe_radius_anchor() -> None:
    """r=2.0 lies inside the content-space
    discrimination band - the only radius producing
    non-zero global resonant_pair_count."""
    assert CONTENT_PROBE_RADIUS == 2.0


def test_global_plateau_resonant_count() -> None:
    """Empirical: 8 resonant pairs in content-only
    space at r=2.0 (vs 96 for method-only at r=2.5)."""
    s = global_plateau_summary()
    assert s.scope == "global"
    assert s.anchor_count == 20
    assert s.resonant_pair_count == 8


def test_global_control_no_resonance() -> None:
    s = global_control_summary()
    assert s.resonant_pair_count == 0


def test_global_subadditivity_positive() -> None:
    s = global_plateau_summary()
    assert s.subadditivity_score > 0


def test_eligible_corpora() -> None:
    assert eligible_corpora() == ("v23", "v314")


def test_ineligible_corpora() -> None:
    assert ineligible_corpora() == ("v315", "v316")


def test_per_corpus_plateau_resonance_is_zero() -> None:
    for c in eligible_corpora():
        s = per_corpus_plateau_summary(c)
        assert s.resonant_pair_count == 0


def test_per_corpus_control_resonance_is_zero() -> None:
    for c in eligible_corpora():
        s = per_corpus_control_summary(c)
        assert s.resonant_pair_count == 0


def test_content_pair_resonance_global() -> None:
    r = build_report()
    assert r.content_pair_resonance == 8


def test_content_control_pairs_global() -> None:
    assert build_report().content_control_pairs == 0


def test_content_pair_transfer_rate_is_zero() -> None:
    assert build_report().content_pair_transfer_rate == 0.0


def test_content_subadditivity_score_positive() -> None:
    assert build_report().content_subadditivity_score > 0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "CONTENT_RESONANCE_TRANSFERS",
        "CONTENT_RESONANCE_GLOBAL_ONLY",
        "CONTENT_RESONANCE_FALSIFIED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_global_only() -> None:
    """Global plateau (8) > control (0) but per-corpus
    transfer = 0."""
    assert build_report().recommendation == (
        "CONTENT_RESONANCE_GLOBAL_ONLY"
    )


def test_content_resonance_weaker_than_method() -> None:
    """Content-only's 8 resonant pairs vs method-only's
    96 - method carries more of the resonance signal
    in the aggregated universe."""
    from desi.method_only_resonance.report import (
        build_report as v358,
    )
    r58 = v358()
    r59 = build_report()
    assert (
        r59.content_pair_resonance
        < r58.method_pair_resonance
    )


def test_artifact_records_per_corpus_summaries() -> None:
    art = build_content_resonance_artifact()
    assert len(art["per_corpus_plateau"]) == 2
    assert len(art["per_corpus_control"]) == 2


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_59" / "report.json").read_text(
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
