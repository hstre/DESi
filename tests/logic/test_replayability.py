"""Tests for v1.2 INV-L4 — every LOGICALLY_SUPPORTED claim is replayable."""
from __future__ import annotations

import json

from desi.logic import (
    InferenceRule,
    LogicalAuditor,
    LogicalState,
    ProofChain,
    replay,
)


def _supported_audit():
    return LogicalAuditor().audit(
        "All men are mortal. Socrates is a man. "
        "Therefore Socrates is mortal."
    )


# ---------------------------------------------------------------------------
# Same audit twice → identical replay_hash
# ---------------------------------------------------------------------------


def test_same_text_audited_twice_yields_identical_replay_hash() -> None:
    a = _supported_audit()
    b = _supported_audit()
    assert a.proof_chain is not None and b.proof_chain is not None
    assert a.proof_chain.replay_hash == b.proof_chain.replay_hash


def test_replay_helper_returns_chain_hash() -> None:
    r = _supported_audit()
    assert r.proof_chain is not None
    assert replay(r.proof_chain) == r.proof_chain.replay_hash


# ---------------------------------------------------------------------------
# Round-tripping the chain through dict + reconstruction
# ---------------------------------------------------------------------------


def test_chain_round_trips_through_to_dict() -> None:
    r = _supported_audit()
    assert r.proof_chain is not None
    d = r.proof_chain.to_dict()
    rebuilt = ProofChain(
        claim_id=d["claim_id"],
        rule_type=InferenceRule(d["rule_type"]),
        premise_ids=tuple(d["premise_ids"]),
        bridge_ids=tuple(d["bridge_ids"]),
    )
    assert rebuilt.replay_hash == r.proof_chain.replay_hash


def test_chain_dict_serialises_with_canonical_json() -> None:
    """The proof-chain dict must be json-encodable as is."""
    r = _supported_audit()
    assert r.proof_chain is not None
    raw = json.dumps(r.proof_chain.to_dict(), sort_keys=True)
    assert "rh_" in raw
    assert "syllogism" in raw


# ---------------------------------------------------------------------------
# Audit twice on the same auditor produces the same chain (no hidden state)
# ---------------------------------------------------------------------------


def test_auditor_is_stateless_across_calls() -> None:
    auditor = LogicalAuditor()
    a = auditor.audit("All men are mortal. Socrates is a man. "
                      "Therefore Socrates is mortal.")
    # Run an unrelated audit in between.
    auditor.audit("Some other proposition.")
    b = auditor.audit("All men are mortal. Socrates is a man. "
                      "Therefore Socrates is mortal.")
    assert a.proof_chain is not None and b.proof_chain is not None
    assert a.proof_chain.replay_hash == b.proof_chain.replay_hash


# ---------------------------------------------------------------------------
# INV-L4: every LOGICALLY_SUPPORTED claim must carry a chain
# ---------------------------------------------------------------------------


def test_every_supported_audit_has_a_proof_chain() -> None:
    for text in (
        "All men are mortal. Socrates is a man. Therefore Socrates is mortal.",
        "It rains. If it rains then the street is wet. "
        "Therefore the street is wet.",
        "a -> b. b -> c. Therefore a -> c.",
    ):
        r = LogicalAuditor().audit(text)
        assert r.state == LogicalState.LOGICALLY_SUPPORTED
        assert r.proof_chain is not None
        assert r.proof_chain.premise_ids
        assert r.proof_chain.replay_hash.startswith("rh_")


# ---------------------------------------------------------------------------
# INV-L4 corollary: the chain hash does not drift between processes
# ---------------------------------------------------------------------------


def test_chain_hash_does_not_carry_a_timestamp() -> None:
    """Two audits at different wall-clock times must hash identically."""
    import time
    a = _supported_audit()
    time.sleep(0.01)  # different wall-clock
    b = _supported_audit()
    assert a.proof_chain.replay_hash == b.proof_chain.replay_hash
