"""Tests for v2.8 PatchCandidate + GuardDescriptor."""
from __future__ import annotations

from desi.rule_patch_protocol import GuardDescriptor, PatchCandidate


def test_candidate_carries_required_fields() -> None:
    c = PatchCandidate(
        name="x", target_rule="x", source_branch="b",
    )
    for f in (
        "name", "target_rule", "source_branch",
        "guards", "touched_files", "required_artifacts",
    ):
        assert hasattr(c, f)


def test_guard_descriptor_to_dict() -> None:
    g = GuardDescriptor(
        name="n", observable="premise_kind", forbidden_shape="x",
    )
    d = g.to_dict()
    assert d == {
        "name": "n",
        "observable": "premise_kind",
        "forbidden_shape": "x",
    }


def test_candidate_fingerprint_is_deterministic() -> None:
    c1 = PatchCandidate(
        name="x", target_rule="x", source_branch="b",
        guards=(
            GuardDescriptor("g", "premise_kind", "s"),
        ),
    )
    c2 = PatchCandidate(
        name="x", target_rule="x", source_branch="b",
        guards=(
            GuardDescriptor("g", "premise_kind", "s"),
        ),
    )
    assert c1.fingerprint() == c2.fingerprint()
    assert len(c1.fingerprint()) == 16


def test_candidate_fingerprint_changes_with_payload() -> None:
    c1 = PatchCandidate(name="x", target_rule="x", source_branch="b")
    c2 = PatchCandidate(name="y", target_rule="x", source_branch="b")
    assert c1.fingerprint() != c2.fingerprint()


def test_to_dict_round_trip_shape() -> None:
    c = PatchCandidate(
        name="x", target_rule="x", source_branch="b",
        guards=(GuardDescriptor("g", "premise_kind", "s"),),
        touched_files=("a.py",),
        required_artifacts=("v2_4/report.json",),
    )
    d = c.to_dict()
    for k in (
        "name", "target_rule", "source_branch", "guards",
        "touched_files", "required_artifacts",
    ):
        assert k in d
