"""v3.74 — missing region localization tests."""
from __future__ import annotations

import json
import pathlib

from desi.missing_localization.holes import hole_summary
from desi.missing_localization.localize import (
    all_localizations, correct_localizations,
    false_holes, localizable_count,
    localization_accuracy,
)
from desi.missing_localization.report import (
    NEPTUN_LOCALIZATION_FLOOR,
    build_missing_region_localization_artifact,
    build_report,
)


def test_localization_floor_anchor() -> None:
    assert NEPTUN_LOCALIZATION_FLOOR == 0.70


def test_all_localizations_count() -> None:
    """Four removals matching v3.73 test claim set."""
    assert len(all_localizations()) == 4


def test_only_bridge_is_localizable() -> None:
    """Empirical: only the BRIDGE removal produces an
    orphaned-leakage signal in this redundant corpus."""
    assert localizable_count(all_localizations()) == 1


def test_bridge_localization_correct() -> None:
    """The centroid of the 12 orphaned leakages is
    closer to v23:R5_02 (the removed bridge) than to
    any of the other 3 test-set anchors."""
    bridge = next(
        l for l in all_localizations()
        if l.role == "bridge"
    )
    assert bridge.orphan_count == 12
    assert bridge.predicted_correct is True
    assert bridge.predicted_id == "v23:R5_02"


def test_high_low_redundant_have_no_signal() -> None:
    for role in ("high_coverage", "low_coverage", "redundant"):
        l = next(
            x for x in all_localizations()
            if x.role == role
        )
        assert l.orphan_count == 0
        assert l.predicted_correct is False


def test_correct_localizations_count() -> None:
    assert correct_localizations(
        all_localizations(),
    ) == 1


def test_false_holes_zero() -> None:
    assert false_holes(all_localizations()) == 0


def test_localization_accuracy_meets_gate() -> None:
    """Neptun concept gate #2:
    localization_accuracy >= 0.70."""
    r = build_report()
    assert r.localization_accuracy >= (
        NEPTUN_LOCALIZATION_FLOOR
    )


def test_localization_accuracy_is_one() -> None:
    """Empirical: 1/1 localizable removals localized
    correctly."""
    assert build_report().localization_accuracy == 1.0


def test_hole_region_distance_positive() -> None:
    r = build_report()
    assert r.hole_region_distance > 0
    assert r.hole_region_distance < 5.0


def test_hole_summary_keys() -> None:
    summary = hole_summary()
    assert "localizable_count" in summary
    assert "localization_accuracy" in summary
    assert "per_removal_records" in summary


def test_replay_stability_is_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_is_usable() -> None:
    assert build_report().recommendation == (
        "LOCALIZATION_USABLE"
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "LOCALIZATION_USABLE",
        "LOCALIZATION_WEAK",
        "LOCALIZATION_FAILED",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in allowed


def test_artifact_summary_present() -> None:
    art = build_missing_region_localization_artifact()
    assert "summary" in art
    assert len(
        art["summary"]["per_removal_records"],
    ) == 4


def test_artifact_report_matches_live_build() -> None:
    root = pathlib.Path(
        __file__,
    ).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_74" / "report.json").read_text(
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
