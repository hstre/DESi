"""Tests for v1.2 ProofChain — premise_ids, rule_type, bridge_ids, replay_hash."""
from __future__ import annotations

import pytest

from desi.logic import (
    InferenceRule,
    LogicalAuditor,
    LogicalState,
    ProofChain,
)


# ---------------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------------


def test_proof_chain_exposes_required_fields() -> None:
    chain = ProofChain(
        claim_id="ac_x",
        rule_type=InferenceRule.SYLLOGISM,
        premise_ids=("pr_a", "pr_b"),
        bridge_ids=(),
    )
    assert chain.claim_id == "ac_x"
    assert chain.rule_type is InferenceRule.SYLLOGISM
    assert chain.premise_ids == ("pr_a", "pr_b")
    assert chain.bridge_ids == ()
    assert chain.replay_hash.startswith("rh_")


# ---------------------------------------------------------------------------
# replay_hash is deterministic
# ---------------------------------------------------------------------------


def test_same_chain_yields_same_replay_hash() -> None:
    a = ProofChain(
        claim_id="ac_x", rule_type=InferenceRule.SYLLOGISM,
        premise_ids=("pr_a", "pr_b"),
    )
    b = ProofChain(
        claim_id="ac_x", rule_type=InferenceRule.SYLLOGISM,
        premise_ids=("pr_a", "pr_b"),
    )
    assert a.replay_hash == b.replay_hash


def test_replay_hash_independent_of_premise_id_order() -> None:
    """Sorting inside replay_hash → reorderings of the inputs hash
    to the same value."""
    a = ProofChain(
        claim_id="ac_x", rule_type=InferenceRule.SYLLOGISM,
        premise_ids=("pr_a", "pr_b"),
    )
    b = ProofChain(
        claim_id="ac_x", rule_type=InferenceRule.SYLLOGISM,
        premise_ids=("pr_b", "pr_a"),
    )
    assert a.replay_hash == b.replay_hash


def test_replay_hash_changes_when_rule_type_changes() -> None:
    a = ProofChain(claim_id="ac_x", rule_type=InferenceRule.SYLLOGISM,
                    premise_ids=("pr_a", "pr_b"))
    b = ProofChain(claim_id="ac_x", rule_type=InferenceRule.IMPLICATION,
                    premise_ids=("pr_a", "pr_b"))
    assert a.replay_hash != b.replay_hash


def test_replay_hash_changes_when_premise_ids_differ() -> None:
    a = ProofChain(claim_id="ac_x", rule_type=InferenceRule.SYLLOGISM,
                    premise_ids=("pr_a", "pr_b"))
    b = ProofChain(claim_id="ac_x", rule_type=InferenceRule.SYLLOGISM,
                    premise_ids=("pr_a", "pr_c"))
    assert a.replay_hash != b.replay_hash


# ---------------------------------------------------------------------------
# replay_hash is independent of claim_id (the chain identifier)
# ---------------------------------------------------------------------------


def test_replay_hash_does_not_depend_on_claim_id() -> None:
    """The hash is over the *chain content*; relabelling the
    audit record must not change the hash."""
    a = ProofChain(claim_id="ac_x", rule_type=InferenceRule.SYLLOGISM,
                    premise_ids=("pr_a", "pr_b"))
    b = ProofChain(claim_id="ac_y", rule_type=InferenceRule.SYLLOGISM,
                    premise_ids=("pr_a", "pr_b"))
    assert a.replay_hash == b.replay_hash


# ---------------------------------------------------------------------------
# Bridge ids participate in the hash
# ---------------------------------------------------------------------------


def test_replay_hash_changes_with_bridge_ids() -> None:
    a = ProofChain(claim_id="x", rule_type=InferenceRule.IMPLICATION,
                    premise_ids=("pr_a",), bridge_ids=())
    b = ProofChain(claim_id="x", rule_type=InferenceRule.IMPLICATION,
                    premise_ids=("pr_a",), bridge_ids=("br_z",))
    assert a.replay_hash != b.replay_hash


# ---------------------------------------------------------------------------
# Auditor produces a chain on success
# ---------------------------------------------------------------------------


def test_supported_audit_returns_a_proof_chain() -> None:
    r = LogicalAuditor().audit(
        "All men are mortal. Socrates is a man. "
        "Therefore Socrates is mortal."
    )
    assert r.state == LogicalState.LOGICALLY_SUPPORTED
    assert r.proof_chain is not None
    assert r.proof_chain.rule_type == InferenceRule.SYLLOGISM
    assert len(r.proof_chain.premise_ids) == 2
    assert r.proof_chain.replay_hash.startswith("rh_")


def test_rejected_audit_does_not_carry_a_proof_chain() -> None:
    r = LogicalAuditor().audit("a -> b. b -> c. Therefore a -> d.")
    assert r.state == LogicalState.LOGICALLY_REJECTED
    assert r.proof_chain is None


# ---------------------------------------------------------------------------
# to_dict shape
# ---------------------------------------------------------------------------


def test_proof_chain_to_dict_has_all_required_fields() -> None:
    chain = ProofChain(claim_id="x", rule_type=InferenceRule.SYLLOGISM,
                        premise_ids=("pr_a", "pr_b"))
    d = chain.to_dict()
    for k in ("claim_id", "rule_type", "premise_ids", "bridge_ids",
              "replay_hash"):
        assert k in d
