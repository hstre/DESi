"""v6.1 - adversarial claim injection tests."""
from __future__ import annotations

import json
import pathlib

from desi.adversarial_claims.adversarial import (
    TRAP_KINDS, TrapKind, detect_trap,
    trap_counts, trapped_claims,
)
from desi.adversarial_claims.ambiguity import (
    AMBIGUITY_KINDS, AmbiguityKind,
    detect_ambiguity, is_ambiguous,
)
from desi.adversarial_claims.conflict_injector import (
    CERTAINTY_LEVELS, Certainty,
    audited_claims,
)
from desi.adversarial_claims.report import (
    ambiguity_handling,
    build_adversarial_claims_artifact,
    build_report, deception_detection_rate,
    false_certainty_rate, governance_integrity,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "world_contact"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_trap_kinds_closed_set() -> None:
    assert TRAP_KINDS == tuple(
        t.value for t in TrapKind
    )


def test_ambiguity_kinds_closed_set() -> None:
    assert AMBIGUITY_KINDS == tuple(
        k.value for k in AmbiguityKind
    )


def test_certainty_levels_closed_set() -> None:
    assert CERTAINTY_LEVELS == tuple(
        c.value for c in Certainty
    )


def test_deception_detection_rate_full() -> None:
    """Pflichtfrage 1: erkennt DESi rhetorische
    Taeuschung?"""
    assert deception_detection_rate() == 1.0


def test_false_certainty_rate_zero() -> None:
    """Pflichtfrage 2: entsteht Overconfidence?
    NEIN - kein audited Claim haelt HIGH
    Certainty, wenn er trapped oder ambig ist.
    """
    assert false_certainty_rate() == 0.0


def test_governance_integrity_one() -> None:
    """Pflichtfrage 3: kollabiert Governance?
    NEIN - alle emittierten Werte sind in den
    closed enums."""
    assert governance_integrity() == 1.0


def test_ambiguity_handling_one() -> None:
    assert ambiguity_handling() == 1.0


def test_detect_trap_authority() -> None:
    assert detect_trap(
        "Trust me bro: it works.",
    ) == TrapKind.AUTHORITY_APPEAL


def test_detect_trap_circular() -> None:
    assert detect_trap(
        "X is true because of itself.",
    ) == TrapKind.CIRCULAR_REASONING


def test_detect_ambiguity_vague() -> None:
    assert detect_ambiguity(
        "Many models often work.",
    ) != AmbiguityKind.NONE


def test_detect_ambiguity_temporal() -> None:
    assert detect_ambiguity(
        "Recently, the trend reversed.",
    ) == AmbiguityKind.TEMPORAL_VAGUE


def test_is_ambiguous_concrete_false() -> None:
    assert not is_ambiguous(
        "The intervention reduced mortality "
        "by 4 percent.",
    )


def test_trap_counts_match_fixture() -> None:
    counts = trap_counts()
    assert sum(counts.values()) == len(
        trapped_claims(),
    )


def test_audited_claims_count() -> None:
    assert len(audited_claims()) == len(
        trapped_claims(),
    )


def test_certainty_low_for_trapped() -> None:
    """A claim with a non-NORMAL trap must
    receive LOW certainty."""
    for a in audited_claims():
        if a.detected_trap != (
            TrapKind.NORMAL.value
        ):
            assert a.certainty == (
                Certainty.LOW.value
            )


def test_certainty_not_high_for_ambiguous() -> (
    None
):
    """A claim flagged ambiguous in the ground
    truth must not exit with HIGH certainty."""
    for a in audited_claims():
        if a.ground_truth_ambiguous:
            assert a.certainty != (
                Certainty.HIGH.value
            )


def test_replay_stability_one() -> None:
    """Pflichtfrage 4: bleibt Replay stabil?"""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "ADVERSARIAL_ROBUST",
        "ADVERSARIAL_DECEPTION_LEAK",
        "ADVERSARIAL_AMBIGUITY_BLIND",
        "ADVERSARIAL_OVERCONFIDENT",
        "ADVERSARIAL_GOVERNANCE_BREACH",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_robust() -> None:
    """Killerfrage: bleibt DESi epistemisch
    ehrlich unter Taeuschung?"""
    assert build_report().recommendation == (
        "ADVERSARIAL_ROBUST"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v6_1_adversarial_claims.json")
    assert art["schema_version"] == (
        "v6_1_adversarial_claims"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v6_1_adversarial_claims.json")
    required = {
        "deception_detection_rate",
        "false_certainty_rate",
        "governance_integrity",
        "ambiguity_handling",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v6_1_report.json")
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
    art = _load("v6_1_adversarial_claims.json")
    live = build_adversarial_claims_artifact()
    assert art == live
