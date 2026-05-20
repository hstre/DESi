"""v5.3 — full bias-audit report + recommendation gate."""
from __future__ import annotations

import json
import pathlib

from desi.corpus_bias_audit.enums import (
    BiasRecommendation,
)
from desi.corpus_bias_audit.report import (
    build_diff_artifact, build_report,
)


def test_build_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_recommendation_is_closed_enum() -> None:
    allowed = {r.value for r in BiasRecommendation}
    assert build_report().recommendation in allowed


def test_recommendation_is_fit_to_taxonomy() -> None:
    """v5.3's whole point: surfacing v5.2's corpus
    engineering. The audit must call CORPUS_FIT_TO_TAXONOMY
    because v5.2's probe_gain_from_rewrites >> 0.20."""
    r = build_report()
    assert r.recommendation == (
        BiasRecommendation.FIT_TO_TAXONOMY.value
    ), r.rationale


def test_rationale_explains_every_gate() -> None:
    r = build_report()
    assert len(r.rationale) >= 12
    for reason in r.rationale:
        assert reason.startswith(("PASS:", "FAIL:"))


def test_raw_recovery_rate_is_one() -> None:
    assert build_report().raw_recovery_rate == 1.0


def test_label_preservation_rate_is_one() -> None:
    assert build_report().label_preservation_rate == 1.0


def test_nc_count_meets_floor() -> None:
    assert build_report().nc_count >= 100


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    artifact = json.loads(
        (root / "artifacts" / "v5_3" / "report.json")
        .read_text(encoding="utf-8"),
    )
    live = build_report().to_dict()
    assert artifact == live


def test_artifact_rewrite_diff_matches_live() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    artifact = json.loads(
        (root / "artifacts" / "v5_3"
         / "rewrite_diff.json")
        .read_text(encoding="utf-8"),
    )
    live = build_diff_artifact()
    assert artifact == live


def test_report_records_known_probe_gain() -> None:
    """The honest finding: probe_gain_from_rewrites is
    materially above the 0.20 trigger."""
    r = build_report()
    assert (
        r.rewrite_influence.probe_gain_from_rewrites > 0.20
    )
