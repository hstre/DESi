"""Tests for ExplicitClaim + ClaimVerdict / ClaimKind."""
from __future__ import annotations

from desi.self_audit import (
    ClaimKind,
    ClaimVerdict,
    ExplicitClaim,
    ReplayedClaim,
    make_claim_id,
)


def test_claim_kind_has_four_values() -> None:
    assert len(list(ClaimKind)) == 4


def test_claim_kind_set() -> None:
    assert {k.value for k in ClaimKind} == {
        "hash", "numeric", "count", "phase",
    }


def test_claim_verdict_has_five_values() -> None:
    assert len(list(ClaimVerdict)) == 5


def test_claim_verdict_set() -> None:
    assert {v.value for v in ClaimVerdict} == {
        "verified", "missing_artifact", "hash_mismatch",
        "value_mismatch", "ambiguous_reference",
    }


def test_make_claim_id_is_deterministic() -> None:
    a = make_claim_id("x.md", 1, ClaimKind.HASH, "k", "v")
    b = make_claim_id("x.md", 1, ClaimKind.HASH, "k", "v")
    assert a == b
    assert a.startswith("cl_")
    assert len(a) == 15  # "cl_" + 12 hex


def test_make_claim_id_changes_with_inputs() -> None:
    a = make_claim_id("x.md", 1, ClaimKind.HASH, "k", "v")
    b = make_claim_id("x.md", 2, ClaimKind.HASH, "k", "v")
    assert a != b


def test_explicit_claim_to_dict_shape() -> None:
    c = ExplicitClaim(
        claim_id="cl_x", doc_id="doc_x", doc_path="x.md",
        line_number=1, line_text="x",
        kind=ClaimKind.NUMERIC, key="precision", value="1.000",
    )
    d = c.to_dict()
    for k in (
        "claim_id", "doc_id", "doc_path", "line_number", "line_text",
        "kind", "key", "value", "referenced_artifact",
    ):
        assert k in d


def test_replayed_claim_to_dict_shape() -> None:
    c = ExplicitClaim(
        claim_id="cl_x", doc_id="doc_x", doc_path="x.md",
        line_number=1, line_text="x",
        kind=ClaimKind.HASH, key="replay_hash", value="0" * 16,
    )
    r = ReplayedClaim(c, ClaimVerdict.VERIFIED, reason="ok")
    d = r.to_dict()
    assert "claim" in d and "verdict" in d and "reason" in d
