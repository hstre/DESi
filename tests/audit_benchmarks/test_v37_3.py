"""v37.3 - Adversarial Financial Semantics tests."""
from __future__ import annotations

import json
import pathlib

from desi.audit_benchmarks_adversarial import (
    adversarial_metrics, adversarial_scenarios,
    build_adversarial_artifact, build_report, detect_conflicts,
    footnote_conflict_detection, management_spin_detection,
    no_false_conflicts, replay_stability,
    semantic_conflict_visibility, warning_zone_preservation,
    warning_zones,
)
from desi.audit_benchmarks_adversarial.report import (
    REPORT_VERDICTS, VERDICT_PASSED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "artifacts" / "audit_benchmarks"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- conflict visibility ------------------------
def test_semantic_conflict_visibility_full() -> None:
    assert semantic_conflict_visibility() == 1.0


def test_all_expected_conflicts_detected() -> None:
    for s in adversarial_scenarios():
        detected = set(detect_conflicts(s.get("signals", {})))
        assert set(s["expected_conflicts"]).issubset(detected)


def test_management_spin_detection_full() -> None:
    assert management_spin_detection() == 1.0


def test_footnote_conflict_detection_full() -> None:
    assert footnote_conflict_detection() == 1.0


# --- no hallucination on clean control ----------
def test_no_false_conflicts() -> None:
    assert no_false_conflicts() is True


def test_clean_control_raises_nothing() -> None:
    by = {s["scenario_id"]: s for s in adversarial_scenarios()}
    clean = by["ad_005"]
    assert detect_conflicts(clean.get("signals", {})) == ()


# --- warning zones preserved --------------------
def test_warning_zone_preservation_full() -> None:
    assert warning_zone_preservation() == 1.0


def test_warning_zones_not_smoothed() -> None:
    zones = warning_zones()
    assert zones
    for z in zones:
        assert z.preserved is True
        assert z.smoothed is False


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for v in adversarial_metrics().values():
        assert 0.0 <= v <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_passed() -> None:
    assert build_report().recommendation == VERDICT_PASSED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_governance_identity() -> None:
    assert build_report().governance_identity == 1.0


def test_report_is_deterministic() -> None:
    assert build_report().to_dict() == build_report().to_dict()


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v37_3_adversarial_semantics.json")
    assert art["schema_version"] == (
        "v37_3_adversarial_semantics_run"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v37_3_adversarial_semantics.json")
    disc = art["disclaimer"].lower()
    assert "never smoothed over" in disc
    assert "does not hallucinate" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v37_3_adversarial_semantics.json")
    required = {
        "semantic_conflict_visibility", "management_spin_detection",
        "footnote_conflict_detection", "warning_zone_preservation",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v37_3_adversarial_semantics.json")
    assert art == build_adversarial_artifact()
