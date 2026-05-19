"""v10.2 - path dependence tests."""
from __future__ import annotations

import json
import pathlib

from desi.path_dependence.memory import (
    PRECEDENT_KINDS, PrecedentKind, fixture,
    kind_counts,
)
from desi.path_dependence.norms import (
    norm_drift, path_rigidity,
)
from desi.path_dependence.precedent import (
    bad_precedent_persistence,
    epistemic_flexibility, overturn_rate,
    precedent_verdicts,
)
from desi.path_dependence.report import (
    build_path_dependence_artifact,
    build_report,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "institutional_governance"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_precedent_kinds_closed_set() -> None:
    assert PRECEDENT_KINDS == tuple(
        k.value for k in PrecedentKind
    )
    assert len(PRECEDENT_KINDS) == 4


def test_kind_counts_consistent() -> None:
    counts = kind_counts()
    assert sum(counts.values()) == len(fixture())


def test_bad_precedent_persistence_zero() -> None:
    """Pflichtfrage 2: verfestigen sich
    schlechte Regeln?"""
    assert bad_precedent_persistence() == 0.0


def test_overturn_rate_full() -> None:
    """Every invalid decision has been
    overturned. No persistent bad precedent."""
    assert overturn_rate() == 1.0


def test_path_rigidity_bounded() -> None:
    """Pflichtfrage 1: entsteht institutionelle
    Traegheit?"""
    assert path_rigidity() <= 0.95


def test_norm_drift_bounded() -> None:
    """Pflichtfrage 3: driftet Normbildung?"""
    assert norm_drift() <= 1.0


def test_epistemic_flexibility_high() -> None:
    """Pflichtfrage 4: bleibt epistemische
    Flexibilitaet erhalten?"""
    assert epistemic_flexibility() >= 0.90


def test_at_least_one_overturn_event() -> None:
    """Sanity: the fixture must contain at
    least one overturn event so flexibility is
    demonstrated."""
    rows = fixture()
    assert any(
        d.overturned_by is not None
        for d in rows
    )


def test_overturning_decision_is_later() -> None:
    """If X is overturned by Y, then Y's
    timestamp is strictly greater than X's."""
    by_id = {
        d.decision_id: d for d in fixture()
    }
    for d in fixture():
        if d.overturned_by is None:
            continue
        successor = by_id[d.overturned_by]
        assert (
            successor.timestamp > d.timestamp
        )


def test_no_overturned_decision_still_valid() -> (
    None
):
    """If a decision was overturned, it must
    not be flagged is_currently_valid=True."""
    for d in fixture():
        if d.overturned_by is not None:
            assert not d.is_currently_valid


def test_precedent_verdicts_match_fixture() -> (
    None
):
    assert len(precedent_verdicts()) == len(
        fixture(),
    )


def test_replay_stability_one() -> None:
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PATH_HEALTHY",
        "PATH_RIGIDIFIED",
        "PATH_BAD_PRECEDENT",
        "PATH_INFLEXIBLE",
        "PATH_NORM_DRIFT",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_healthy() -> None:
    """Killerfrage: kann DESi institutionelles
    Gedaechtnis haben, ohne epistemisch zu
    verkrusten?"""
    assert build_report().recommendation == (
        "PATH_HEALTHY"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v10_2_path_dependence.json")
    assert art["schema_version"] == (
        "v10_2_path_dependence"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v10_2_path_dependence.json")
    required = {
        "path_rigidity",
        "bad_precedent_persistence",
        "norm_drift",
        "epistemic_flexibility",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v10_2_report.json")
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
    art = _load("v10_2_path_dependence.json")
    live = build_path_dependence_artifact()
    assert art == live
