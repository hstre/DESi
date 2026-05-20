"""v18.0 - Canonical & Polemical Topology tests."""
from __future__ import annotations

import re
import json
import pathlib

from desi.religious_pressure import (
    CLAIM_TYPES, INTERPRETATION_LAYERS, TRADITIONS,
    ClaimType, build_report, build_topology_artifact,
    claims, dogmatic_pressure, exclusivity_forcing_claims,
    historical_layering, layer_collisions,
    metaphysical_load, no_tradition_ranking,
    no_truth_determination, status_histogram,
    theological_meaning_not_empirical, tradition_standings,
    translation_drift_detection, truth_claim_density,
)
from desi.religious_pressure.report import (
    REPORT_VERDICTS, VERDICT_MAPPED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "religious_pressure"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- closed vocab / no-authority safety ---------
def test_claim_types_closed_set() -> None:
    assert CLAIM_TYPES == tuple(
        c.value for c in ClaimType
    )
    assert len(CLAIM_TYPES) == 8


def test_no_truth_or_ranking_vocab() -> None:
    forbidden = {
        "true", "truest", "superior", "proven",
        "debunked", "best", "divine",
    }
    tokens = set()
    for v in (
        list(CLAIM_TYPES) + list(REPORT_VERDICTS)
        + list(INTERPRETATION_LAYERS)
    ):
        tokens.update(re.split(r"[^a-z]+", v.lower()))
    assert not (tokens & forbidden)


def test_no_truth_determination() -> None:
    assert no_truth_determination() is True


def test_no_tradition_ranking() -> None:
    """Every tradition holds the SAME neutral standing -
    DESi ranks none."""
    assert no_tradition_ranking() is True
    standings = set(tradition_standings().values())
    assert len(standings) == 1


def test_theological_meaning_not_empirical() -> None:
    assert theological_meaning_not_empirical() is True


def test_report_has_no_truth_or_rank_field() -> None:
    d = build_report().to_dict()
    for forbidden in (
        "true_religion", "ranking", "winner",
        "best_tradition", "verified_truth",
    ):
        assert forbidden not in d


# --- pressure is detected -----------------------
def test_dogmatic_pressure_detected() -> None:
    """Killerfrage: DESi must SEE the metaphysical
    authority pressure."""
    assert dogmatic_pressure() > 0.0
    assert truth_claim_density() > 0.0
    assert len(exclusivity_forcing_claims()) >= 1


def test_metrics_in_unit_interval() -> None:
    for m in (
        dogmatic_pressure(), translation_drift_detection(),
        historical_layering(), truth_claim_density(),
        metaphysical_load(),
    ):
        assert 0.0 <= m <= 1.0


def test_translation_drift_detected() -> None:
    assert translation_drift_detection() == 1.0


def test_layering_is_plural() -> None:
    """Rich, multi-layer reading is preserved (not
    flattened) and collisions are surfaced."""
    assert historical_layering() >= 0.80
    assert len(layer_collisions()) >= 1


def test_all_claim_types_exercised() -> None:
    hist = status_histogram()
    for t in CLAIM_TYPES:
        assert hist[t] >= 1


def test_five_traditions() -> None:
    assert len(TRADITIONS) == 5


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


def test_recommendation_is_mapped() -> None:
    assert build_report().recommendation == VERDICT_MAPPED


def test_recommendation_never_asserts_truth() -> None:
    rec = build_report().recommendation.lower()
    for w in ("true", "proven", "superior", "divine"):
        assert w not in rec


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v18_0_topology.json")
    assert art["schema_version"] == (
        "v18_0_canonical_polemical_topology"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v18_0_topology.json")
    disc = art["disclaimer"].lower()
    assert "determines no true religion" in disc
    assert "ranks no tradition" in disc
    assert (
        "theological meaning != empirical verifiability"
        in disc
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v18_0_topology.json")
    required = {
        "dogmatic_pressure",
        "translation_drift_detection",
        "historical_layering",
        "truth_claim_density",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v18_0_topology.json")
    live = build_topology_artifact()
    assert art == live
