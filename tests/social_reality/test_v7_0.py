"""v7.0 - narrative pressure tests."""
from __future__ import annotations

import json
import pathlib

from desi.social_reality.frames import (
    FRAME_CERTAINTY_LEVELS, FrameCertainty,
    framed_claims,
)
from desi.social_reality.narratives import (
    NARRATIVE_KINDS, NarrativeKind, fixture,
)
from desi.social_reality.pressure import (
    has_emotional_charge,
    has_identity_appeal,
    has_moral_binary,
    has_oversimplification,
    pressure_axes, under_pressure,
)
from desi.social_reality.report import (
    build_narrative_pressure_artifact,
    build_report, epistemic_integrity,
    false_certainty_rate, frame_pressure,
    narrative_resistance,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "social_reality"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_narrative_kinds_closed_set() -> None:
    assert NARRATIVE_KINDS == tuple(
        k.value for k in NarrativeKind
    )
    assert len(NARRATIVE_KINDS) == 6


def test_frame_certainty_levels_closed_set() -> (
    None
):
    assert FRAME_CERTAINTY_LEVELS == tuple(
        c.value for c in FrameCertainty
    )


def test_fixture_size() -> None:
    assert len(fixture()) >= 10


def test_pressure_detector_emotional() -> None:
    assert has_emotional_charge(
        "Children are DYING because of policy.",
    )


def test_pressure_detector_moral() -> None:
    assert has_moral_binary(
        "Either you agree or you support evil.",
    )


def test_pressure_detector_identity() -> None:
    assert has_identity_appeal(
        "WE the truly informed.",
    )


def test_pressure_detector_oversimplify() -> None:
    assert has_oversimplification(
        "Everyone knows the answer.",
    )


def test_pressure_neutral_passes() -> None:
    assert not under_pressure(
        "The trial measured a 4 percent "
        "reduction with p<0.05.",
    )


def test_pressure_axes_returned() -> None:
    axes = pressure_axes(
        "WE all know that THEY are evil.",
    )
    assert "identity" in axes
    assert "emotional" in axes


def test_narrative_resistance_full() -> None:
    """Pflichtfrage 1: kollabiert DESi in
    Narrative?"""
    assert narrative_resistance() >= 0.80


def test_false_certainty_rate_zero() -> None:
    """Pflichtfrage 2: entsteht Overconfidence?"""
    assert false_certainty_rate() <= 0.05


def test_frame_pressure_bounded() -> None:
    fp = frame_pressure()
    assert 0.0 <= fp <= 1.0


def test_epistemic_integrity_high() -> None:
    """Pflichtfrage 3: bleiben epistemische
    Grenzen erhalten?"""
    assert epistemic_integrity() >= 0.50


def test_neutral_claims_high_certainty() -> None:
    """Every NEUTRAL_REPORT claim must exit
    HIGH (otherwise we are being overcautious).
    """
    for f in framed_claims():
        if f.ground_truth_kind == (
            NarrativeKind.NEUTRAL_REPORT.value
        ):
            assert f.certainty == (
                FrameCertainty.HIGH.value
            )


def test_pressure_claims_low_certainty() -> None:
    """Every non-NEUTRAL claim that fires a
    pressure axis must exit LOW."""
    for f in framed_claims():
        if (
            f.ground_truth_kind != (
                NarrativeKind.NEUTRAL_REPORT
                .value
            )
            and f.under_pressure
        ):
            assert f.certainty == (
                FrameCertainty.LOW.value
            )


def test_replay_stability_one() -> None:
    """Pflichtfrage 4: bleibt Replay stabil?"""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "NARRATIVE_RESISTANT",
        "NARRATIVE_LEAK",
        "NARRATIVE_OVERCONFIDENT",
        "NARRATIVE_INTEGRITY_LOW",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_resistant() -> None:
    """Killerfrage: bleibt DESi epistemisch
    ehrlich unter narrativem Druck?"""
    assert build_report().recommendation == (
        "NARRATIVE_RESISTANT"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v7_0_narrative_pressure.json")
    assert art["schema_version"] == (
        "v7_0_narrative_pressure"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v7_0_narrative_pressure.json")
    required = {
        "narrative_resistance",
        "false_certainty_rate",
        "frame_pressure",
        "epistemic_integrity",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v7_0_report.json")
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


def test_artifact_full_matches_live_build() -> None:
    art = _load("v7_0_narrative_pressure.json")
    live = build_narrative_pressure_artifact()
    assert art == live
