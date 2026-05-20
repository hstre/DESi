"""v3.58 — method-only resonance tests."""
from __future__ import annotations

import json
import pathlib

from desi.method_only_resonance.probe import (
    METHOD_PROBE_RADIUS, MIN_ANCHORS_FOR_PAIRS,
    eligible_corpora, global_control_summary,
    global_plateau_summary, ineligible_corpora,
    per_corpus_control_summary,
    per_corpus_plateau_summary,
)
from desi.method_only_resonance.report import (
    build_method_resonance_artifact, build_report,
)


def test_method_probe_radius_anchor() -> None:
    """r=2.5 lies inside the method-space
    discrimination band (per-anchor coverage spreads
    across {0, 12, 121} at this radius)."""
    assert METHOD_PROBE_RADIUS == 2.5


def test_global_plateau_summary_resonant_count() -> None:
    """Empirical: 96 resonant pairs in method-only
    space at r=2.5 (vs 64 in full 9-d at r=3.5)."""
    s = global_plateau_summary()
    assert s.scope == "global"
    assert s.anchor_count == 20
    assert s.pair_count == 190
    assert s.resonant_pair_count == 96


def test_global_control_summary_no_resonance() -> None:
    s = global_control_summary()
    assert s.scope == "global"
    assert s.resonant_pair_count == 0


def test_global_subadditivity_positive() -> None:
    s = global_plateau_summary()
    assert s.subadditivity_score > 0


def test_eligible_corpora_for_pair_analysis() -> None:
    assert eligible_corpora() == ("v23", "v314")


def test_ineligible_corpora() -> None:
    assert ineligible_corpora() == ("v315", "v316")


def test_per_corpus_plateau_resonance_is_zero() -> None:
    """Per-corpus: same finding as v3.54 (no resonance
    inside any individual corpus)."""
    for c in eligible_corpora():
        s = per_corpus_plateau_summary(c)
        assert s.resonant_pair_count == 0


def test_per_corpus_control_resonance_is_zero() -> None:
    for c in eligible_corpora():
        s = per_corpus_control_summary(c)
        assert s.resonant_pair_count == 0


def test_method_pair_resonance_global() -> None:
    r = build_report()
    assert r.method_pair_resonance == 96


def test_method_control_pairs_global() -> None:
    assert build_report().method_control_pairs == 0


def test_method_pair_transfer_rate_is_zero() -> None:
    """Honest finding: 0/2 eligible corpora show
    method-space resonance exceeding control. The
    method-only sprint reproduces the v3.54 per-corpus
    failure - resonance is still a global aggregation
    artifact, not corpus-local."""
    assert build_report().method_pair_transfer_rate == 0.0


def test_method_subadditivity_score_positive() -> None:
    assert build_report().method_subadditivity_score > 0


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "METHOD_RESONANCE_TRANSFERS",
        "METHOD_RESONANCE_GLOBAL_ONLY",
        "METHOD_RESONANCE_FALSIFIED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_recommendation_is_global_only() -> None:
    """Global plateau resonance (96) > control (0) but
    per-corpus transfer rate is 0 - the verdict is
    METHOD_RESONANCE_GLOBAL_ONLY."""
    assert build_report().recommendation == (
        "METHOD_RESONANCE_GLOBAL_ONLY"
    )


def test_artifact_records_per_corpus_summaries() -> None:
    art = build_method_resonance_artifact()
    assert len(art["per_corpus_plateau"]) == 2
    assert len(art["per_corpus_control"]) == 2


def test_artifact_has_global_summaries() -> None:
    art = build_method_resonance_artifact()
    assert "global_plateau" in art
    assert "global_control" in art


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_58" / "report.json").read_text(
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
