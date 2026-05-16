"""v5.4 — full split-evaluation report + recommendation
gate."""
from __future__ import annotations

import json
import pathlib

from desi.raw_generalization.enums import RawRecommendation
from desi.raw_generalization.report import (
    build_report, build_split_eval_artifact,
)


def test_build_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_recommendation_is_closed_enum() -> None:
    allowed = {r.value for r in RawRecommendation}
    assert build_report().recommendation in allowed


def test_recommendation_is_taxonomy_only() -> None:
    """v5.4's central finding: taxonomy passes on the
    RAW corpus; probes do not."""
    r = build_report()
    assert r.recommendation == (
        RawRecommendation.TAXONOMY_ONLY.value
    ), r.rationale


def test_taxonomy_passes_probes_fail() -> None:
    r = build_report()
    assert r.taxonomy_passes is True
    assert r.probes_pass is False


def test_rationale_labels_channels_explicitly() -> None:
    """Aufgabe 5 — every claim must declare
    taxonomy_only or probe_only."""
    r = build_report()
    for reason in r.rationale:
        # Every rationale line tags its channel or is the
        # NC line.
        assert (
            "[taxonomy_only]" in reason
            or "[probe_only]" in reason
            or reason.startswith(("PASS: nc_accuracy",
                                   "FAIL: nc_accuracy"))
        ), reason


def test_nc_count_meets_floor() -> None:
    assert build_report().nc_count >= 100


def test_report_to_json_round_trips() -> None:
    r = build_report()
    obj = json.loads(r.to_json())
    assert obj["recommendation"] == r.recommendation


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    artifact = json.loads(
        (root / "artifacts" / "v5_4" / "report.json")
        .read_text(encoding="utf-8"),
    )
    live = build_report().to_dict()
    assert artifact == live


def test_artifact_split_eval_matches_live() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    artifact = json.loads(
        (root / "artifacts" / "v5_4" / "split_eval.json")
        .read_text(encoding="utf-8"),
    )
    live = build_split_eval_artifact()
    assert artifact == live
