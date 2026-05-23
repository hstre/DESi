"""v3.56 — cross-corpus phase transition tests."""
from __future__ import annotations

import json
import pathlib

from desi.cross_corpus.corpus_loader import (
    corpus_plateau_anchors,
)
from desi.cross_corpus_phase.phase_transfer import (
    per_corpus_summary, transfer_rate, transfers_at,
)
from desi.cross_corpus_phase.report import (
    PAPER11_TRANSFER_FLOOR,
    build_cross_corpus_phase_artifact, build_report,
)
from desi.cross_corpus_phase.transition import (
    MIN_ANCHORS_FOR_DISCONTINUITY, PROBE_RADIUS,
    coupling_strength, discontinuity_score,
    eligible_corpora, ineligible_corpora,
    per_corpus_phase_curve, saturation_point,
)


def test_probe_radius_is_three_point_five() -> None:
    assert PROBE_RADIUS == 3.5


def test_min_anchors_for_discontinuity() -> None:
    assert MIN_ANCHORS_FOR_DISCONTINUITY == 2


def test_eligible_corpora() -> None:
    assert eligible_corpora() == ("v23", "v314")


def test_ineligible_corpora() -> None:
    assert ineligible_corpora() == ("v315", "v316")


def test_per_corpus_phase_curve_v23() -> None:
    curve = per_corpus_phase_curve("v23")
    by_k = {p.mass_level: p.leakage_count for p in curve}
    assert by_k[0] == 0
    assert by_k[1] == 0
    assert by_k[2] == 6   # jump
    assert by_k[3] == 6
    assert by_k[4] == 6


def test_per_corpus_phase_curve_v314() -> None:
    curve = per_corpus_phase_curve("v314")
    by_k = {p.mass_level: p.leakage_count for p in curve}
    assert by_k[1] == 0
    assert by_k[2] == 30  # jump


def test_discontinuity_score_per_corpus() -> None:
    for c in eligible_corpora():
        score = discontinuity_score(
            per_corpus_phase_curve(c),
        )
        assert score > 0
        assert score == 1.0  # single dominant jump


def test_saturation_point_per_corpus() -> None:
    """Both eligible corpora saturate at k=2."""
    for c in eligible_corpora():
        sat = saturation_point(
            per_corpus_phase_curve(c),
        )
        assert sat == 2


def test_coupling_strength_positive() -> None:
    for c in eligible_corpora():
        coup = coupling_strength(
            per_corpus_phase_curve(c),
        )
        assert coup > 0


def test_transfers_at_each_eligible_corpus() -> None:
    for c in eligible_corpora():
        assert transfers_at(c) is True


def test_phase_transfer_rate_is_one() -> None:
    """Paper-11 v2 gate #4: every eligible corpus
    transfers."""
    assert build_report().phase_transfer_rate == 1.0


def test_phase_transfer_rate_meets_gate() -> None:
    assert build_report().phase_transfer_rate >= (
        PAPER11_TRANSFER_FLOOR
    )


def test_per_corpus_summary_keys() -> None:
    for c in eligible_corpora():
        s = per_corpus_summary(c)
        assert s["corpus"] == c
        assert "phase_curve" in s
        assert "discontinuity_score" in s
        assert "saturation_point" in s
        assert "coupling_strength" in s


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_transfers() -> None:
    assert build_report().recommendation == (
        "PHASE_TRANSITION_TRANSFERS"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PHASE_TRANSITION_TRANSFERS",
        "PHASE_TRANSITION_PARTIAL",
        "PHASE_TRANSITION_LOCAL",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_per_corpus_count() -> None:
    """Artifact includes summaries for ALL 4 reference
    corpora (eligible AND ineligible)."""
    art = build_cross_corpus_phase_artifact()
    assert len(art["per_corpus_summaries"]) == 4


def test_paper11_v2_gate_summary() -> None:
    """All five cross-corpus gates evaluated end-to-end."""
    from desi.cross_corpus.report import (
        build_report as v353,
    )
    from desi.cross_corpus_anti_anchor.report import (
        build_report as v355,
    )
    from desi.cross_corpus_resonance.report import (
        build_report as v354,
    )
    r53 = v353()
    r54 = v354()
    r55 = v355()
    r56 = build_report()
    # Gate 1: radius transfer
    assert r53.radius_transfer_rate >= 0.75
    # Gate 2: pair transfer (FAILS empirically; the
    # assertion is the empirical pinning, not the
    # gate evaluation)
    assert r54.pair_transfer_rate == 0.0
    # Gate 3: anti-anchor transfer
    assert r55.anti_anchor_transfer_rate >= 0.75
    # Gate 4: phase transfer
    assert r56.phase_transfer_rate >= 0.75
    # Gate 5: replay stability across all sprints
    assert r53.replay_stability == 1.0
    assert r54.replay_stability == 1.0
    assert r55.replay_stability == 1.0
    assert r56.replay_stability == 1.0


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_56" / "report.json").read_text(
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
