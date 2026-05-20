"""Tests for the v2.8 RulePatchProtocol orchestrator (Aufgaben 4 + 5)."""
from __future__ import annotations

from desi.rule_patch_protocol import (
    PatchPhase,
    RulePatchProtocol,
    causal_chain_v2_7_candidate,
    fake_rule_without_guards_candidate,
)


# ---------------------------------------------------------------------------
# Aufgabe 4 — v2.7 reconstruction
# ---------------------------------------------------------------------------


def test_v27_reconstruction_completes() -> None:
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert rec.phase is PatchPhase.COMPLETE
    assert rec.passed is True


def test_v27_reconstruction_records_seven_guards() -> None:
    """Aufgabe 4: guards >= 2 — v2.7 actually declares seven."""
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert len(rec.created_guards) >= 2
    assert len(rec.created_guards) == 7


def test_v27_reconstruction_carries_no_fail_reason() -> None:
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert rec.fail_reason == ""


def test_v27_reconstruction_records_six_phase_outcomes() -> None:
    """Every phase except the terminal COMPLETE sentinel produces
    an outcome on a successful run."""
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert len(rec.phase_outcomes) == 6
    assert all(o.passed for o in rec.phase_outcomes)


def test_v27_reconstruction_before_equals_after() -> None:
    """The protocol is read-only — between baseline and replay
    every benchmark hash matches."""
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    assert rec.benchmark_hash_before
    assert rec.benchmark_hash_after
    assert rec.benchmark_hash_before == rec.benchmark_hash_after


# ---------------------------------------------------------------------------
# Aufgabe 5 — fake patch rejection
# ---------------------------------------------------------------------------


def test_fake_rule_rejected_at_guard_synthesis() -> None:
    rec = RulePatchProtocol().run(fake_rule_without_guards_candidate())
    assert rec.phase is PatchPhase.GUARD_SYNTHESIS
    assert rec.passed is False


def test_fake_rule_fail_reason_starts_with_missing_guards() -> None:
    rec = RulePatchProtocol().run(fake_rule_without_guards_candidate())
    assert rec.fail_reason.startswith("missing_guards")


def test_fake_rule_record_phase_value() -> None:
    rec = RulePatchProtocol().run(fake_rule_without_guards_candidate())
    assert rec.phase.value == "guard_synthesis"


# ---------------------------------------------------------------------------
# Replay determinism (Aufgabe 7)
# ---------------------------------------------------------------------------


def test_two_runs_of_v27_reconstruction_match() -> None:
    proto = RulePatchProtocol()
    a = proto.run(causal_chain_v2_7_candidate())
    b = proto.run(causal_chain_v2_7_candidate())
    assert a.replay_hash == b.replay_hash


def test_two_runs_of_fake_rule_match() -> None:
    proto = RulePatchProtocol()
    a = proto.run(fake_rule_without_guards_candidate())
    b = proto.run(fake_rule_without_guards_candidate())
    assert a.replay_hash == b.replay_hash


def test_v27_and_fake_records_have_distinct_replay_hashes() -> None:
    proto = RulePatchProtocol()
    a = proto.run(causal_chain_v2_7_candidate())
    b = proto.run(fake_rule_without_guards_candidate())
    assert a.replay_hash != b.replay_hash


# ---------------------------------------------------------------------------
# Aufgabe 8 — Report fields
# ---------------------------------------------------------------------------


def test_record_to_dict_includes_phase_outcomes() -> None:
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    d = rec.to_dict()
    assert "phase_outcomes" in d
    assert len(d["phase_outcomes"]) >= 1


def test_record_to_dict_includes_required_eleven_fields() -> None:
    rec = RulePatchProtocol().run(causal_chain_v2_7_candidate())
    d = rec.to_dict()
    for k in (
        "patch_id", "target_rule", "source_branch", "phase",
        "passed", "created_guards", "touched_files",
        "benchmark_hash_before", "benchmark_hash_after",
        "replay_hash", "timestamp",
    ):
        assert k in d
