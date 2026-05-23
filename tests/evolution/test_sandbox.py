"""Tests for CloneSandbox — isolation contract."""
from __future__ import annotations

import pytest

from desi.evolution import CloneSandbox, MutationProposal, MutationTarget
from desi.evolution.sandbox import SandboxIsolationError, default_stable


def _proposal_for(stable_version: str) -> MutationProposal:
    return MutationProposal(
        parent_version=stable_version,
        problem="x",
        hypothesis="y",
        target=MutationTarget.GUARD_THRESHOLDS,
        config_delta={"guard_thresholds.merge_similarity_min": 0.90},
        expected_improvement="more conservative merges",
        rollback_conditions=("revert if false-merge rate rises",),
    )


def test_clone_starts_identical_to_stable() -> None:
    stable = default_stable()
    clone = CloneSandbox(stable)
    assert clone.config == stable.as_dict


def test_clone_apply_modifies_clone_only(stable=None) -> None:
    stable = default_stable()
    snapshot_before = dict(stable.as_dict)
    clone = CloneSandbox(stable)
    p = _proposal_for(stable.version)
    clone.apply(p)
    # Clone changed.
    assert clone.config["guard_thresholds.merge_similarity_min"] == 0.90
    # Stable unchanged — both as dataclass and as_dict snapshot.
    assert stable.as_dict == snapshot_before
    assert dict(stable.knobs) == snapshot_before


def test_clone_records_applied_proposals() -> None:
    stable = default_stable()
    clone = CloneSandbox(stable)
    p = _proposal_for(stable.version)
    clone.apply(p)
    assert p.mutation_id in clone.applied_proposals


def test_clone_rejects_proposals_targeting_different_stable_version() -> None:
    stable = default_stable()
    clone = CloneSandbox(stable)
    p = _proposal_for("stable-v9.9.9")
    with pytest.raises(SandboxIsolationError):
        clone.apply(p)


def test_clone_write_to_stable_raises() -> None:
    stable = default_stable()
    clone = CloneSandbox(stable)
    with pytest.raises(SandboxIsolationError):
        clone.write_to_stable("anything")


def test_clone_diff_lists_only_changed_knobs() -> None:
    stable = default_stable()
    clone = CloneSandbox(stable)
    p = _proposal_for(stable.version)
    clone.apply(p)
    diff = clone.diff()
    assert set(diff.keys()) == {"guard_thresholds.merge_similarity_min"}
    before, after = diff["guard_thresholds.merge_similarity_min"]
    assert before == 0.85
    assert after == 0.90


def test_two_clones_from_same_stable_are_independent() -> None:
    stable = default_stable()
    a = CloneSandbox(stable)
    b = CloneSandbox(stable)
    a.apply(_proposal_for(stable.version))
    # b's config remains the stable defaults; a's does not.
    assert b.config == stable.as_dict
    assert a.config != stable.as_dict


def test_stable_id_is_deterministic() -> None:
    a = default_stable()
    b = default_stable()
    assert a.stable_id == b.stable_id


def test_clone_returns_copy_of_config_not_internal_dict() -> None:
    stable = default_stable()
    clone = CloneSandbox(stable)
    cfg1 = clone.config
    cfg1["guard_thresholds.merge_similarity_min"] = 0.99
    cfg2 = clone.config
    # External mutation of the returned dict must not bleed in.
    assert cfg2["guard_thresholds.merge_similarity_min"] == 0.85
