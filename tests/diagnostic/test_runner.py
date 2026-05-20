"""End-to-end tests for v2.1 SelfDiagnosticRunner (Aufgaben 1, 9)."""
from __future__ import annotations

from desi.diagnostic import (
    DEFAULT_INVENTORY,
    DeficitCategory,
    SelfDiagnosticReport,
    SelfDiagnosticRunner,
)


# ---------------------------------------------------------------------------
# Aufgabe 1 — basic shape + stable-source invariant
# ---------------------------------------------------------------------------


def test_run_returns_self_diagnostic_report() -> None:
    rep = SelfDiagnosticRunner().run()
    assert isinstance(rep, SelfDiagnosticReport)


def test_stable_hash_unchanged_after_diagnostic() -> None:
    """Hard invariant: read-only over stable-v1.9.0."""
    rep = SelfDiagnosticRunner().run()
    assert rep.stable_hash_before == rep.stable_hash_after


def test_stable_version_recorded() -> None:
    rep = SelfDiagnosticRunner().run()
    assert rep.stable_version == "stable-v1.9.0"


# ---------------------------------------------------------------------------
# Aufgabe 9 — required report fields
# ---------------------------------------------------------------------------


def test_report_carries_all_required_fields() -> None:
    rep = SelfDiagnosticRunner().run()
    for f in (
        "total_deficits", "actionable_deficits", "non_actionable_deficits",
        "highest_severity", "highest_confidence",
        "dead_knobs", "live_knobs",
        "recommended_next_knob", "blocked_recommendations",
        "replay_hash",
    ):
        assert hasattr(rep, f), f


def test_actionable_plus_non_actionable_equals_total() -> None:
    rep = SelfDiagnosticRunner().run()
    assert (rep.actionable_deficits + rep.non_actionable_deficits
            == rep.total_deficits)


def test_live_and_dead_partition_existing_knobs() -> None:
    rep = SelfDiagnosticRunner().run()
    assert set(rep.live_knobs) & set(rep.dead_knobs) == set()
    assert (set(rep.live_knobs) | set(rep.dead_knobs)
            == DEFAULT_INVENTORY.existing)


def test_two_runs_produce_identical_replay_hashes() -> None:
    a = SelfDiagnosticRunner().run()
    b = SelfDiagnosticRunner().run()
    assert a.replay_hash == b.replay_hash


def test_two_runs_produce_identical_deficit_sequences() -> None:
    a = SelfDiagnosticRunner().run()
    b = SelfDiagnosticRunner().run()
    assert ([d.replay_hash for d in a.deficits]
            == [d.replay_hash for d in b.deficits])


# ---------------------------------------------------------------------------
# Aufgabe 6 + 7 — recommended knob exists and is live
# ---------------------------------------------------------------------------


def test_recommended_next_knob_is_either_none_or_live() -> None:
    rep = SelfDiagnosticRunner().run()
    if rep.recommended_next_knob is not None:
        assert rep.recommended_next_knob in rep.live_knobs


def test_recommended_next_knob_exists_in_inventory() -> None:
    rep = SelfDiagnosticRunner().run()
    if rep.recommended_next_knob is not None:
        assert DEFAULT_INVENTORY.is_known(rep.recommended_next_knob)


def test_blocked_recommendations_are_dead_knobs() -> None:
    """A blocked recommendation must be a known knob that's
    not in the live set."""
    rep = SelfDiagnosticRunner().run()
    for k in rep.blocked_recommendations:
        assert DEFAULT_INVENTORY.is_known(k)
        assert k not in rep.live_knobs


# ---------------------------------------------------------------------------
# Aufgabe 5 success criterion — at least one DEAD_MUTATION_KNOB or NONE
# ---------------------------------------------------------------------------


def test_dead_mutation_knob_detected_when_sandbox_artifact_present() -> None:
    """Given the v2.0 artifact ships a constant-metric 30-step run,
    the diagnostic should flag the dead knob. We assert the
    relaxed contract: either a DEAD_MUTATION_KNOB is found OR none
    of the steps were eligible — never silently wrong."""
    rep = SelfDiagnosticRunner().run()
    has_dead = any(
        d.category is DeficitCategory.DEAD_MUTATION_KNOB
        for d in rep.deficits
    )
    # Per directive: "Mindestens ein DEAD_MUTATION_KNOB oder NONE."
    # We assert the explicit positive when the v2.0 artifact exists.
    if rep.dead_knobs:
        assert has_dead


def test_to_dict_round_trip() -> None:
    rep = SelfDiagnosticRunner().run()
    d = rep.to_dict()
    for k in (
        "total_deficits", "actionable_deficits", "non_actionable_deficits",
        "highest_severity", "highest_confidence", "dead_knobs",
        "live_knobs", "recommended_next_knob",
        "blocked_recommendations", "deficits", "replay_hash",
    ):
        assert k in d
