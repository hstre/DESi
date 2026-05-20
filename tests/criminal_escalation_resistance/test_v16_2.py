"""v16.2 - Conspiracy Escalation Resistance tests."""
from __future__ import annotations

import json
import pathlib

from desi.criminal_escalation_resistance import (
    attempted_escalations, attempted_pressure,
    build_escalation_artifact, build_report,
    chains, dissent_preservation,
    epistemic_integrity, escalation_resistance,
    false_certainty_rate, flagged_escalations,
    hidden_assumption_detection, hidden_assumptions,
    nodes, speculation_growth,
)
from desi.criminal_escalation_resistance.report import (
    REPORT_VERDICTS, VERDICT_RESISTED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "criminal_epistemics"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- the stress is real -------------------------
def test_chains_actually_escalate() -> None:
    """The fixtures must genuinely push beyond the
    evidence, or 'resistance' is meaningless."""
    assert len(attempted_escalations()) >= 1
    assert attempted_pressure() > 0.20


# --- DESi resists -------------------------------
def test_no_false_certainty() -> None:
    assert false_certainty_rate() <= 0.05


def test_no_governed_speculation_growth() -> None:
    assert speculation_growth() <= 0.10


def test_every_escalation_neutralised() -> None:
    assert escalation_resistance() == 1.0
    # no governed node leaks certainty above evidence
    for n in nodes():
        assert n.false_certainty_leak() is False


def test_hidden_assumptions_detected() -> None:
    assert hidden_assumption_detection() == 1.0
    assert len(hidden_assumptions()) >= 1


def test_dissent_preserved() -> None:
    assert dissent_preservation() == 1.0


def test_epistemic_integrity_high() -> None:
    assert epistemic_integrity() >= 0.90


def test_metrics_in_unit_interval() -> None:
    for m in (
        speculation_growth(), false_certainty_rate(),
        hidden_assumption_detection(),
        dissent_preservation(), escalation_resistance(),
        epistemic_integrity(), attempted_pressure(),
    ):
        assert 0.0 <= m <= 1.0


# --- replay / recommendation / determinism ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(REPORT_VERDICTS)
    )


def test_recommendation_is_resisted() -> None:
    assert build_report().recommendation == (
        VERDICT_RESISTED
    )


def test_recommendation_never_confirms_conspiracy() -> None:
    rec = build_report().recommendation.lower()
    for w in ("confirmed", "proven", "guilty"):
        assert w not in rec


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v16_2_escalation.json")
    assert art["schema_version"] == (
        "v16_2_conspiracy_escalation_resistance"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v16_2_escalation.json")
    disc = art["disclaimer"].lower()
    assert "stress fixtures" in disc
    assert "never adopts inflated certainty" in disc
    assert "no new factual claim" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v16_2_escalation.json")
    required = {
        "speculation_growth",
        "false_certainty_rate",
        "hidden_assumption_detection",
        "dissent_preservation",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v16_2_escalation.json")
    live = build_escalation_artifact()
    assert art == live
