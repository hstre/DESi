"""Tests for the standalone wrong-slice strict matcher.

The matcher is the load-bearing control of the wrong-slice ablation
(see experiments/wrong_slice/PREREGISTRATION.md): a matched wrong slice must be
indistinguishable from the correct slice on length, claim count, status schema,
provenance schema, and format — and must actually differ in content. These
tests check that each criterion fails when (and only when) it should.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "experiments" / "wrong_slice"))

from slice_matcher import (  # noqa: E402
    Claim,
    Slice,
    content_hash,
    is_admissible_wrong_slice,
    match,
)


def _claim(text: str, pass_id: str) -> Claim:
    return Claim(
        text=text,
        status={"validity": "verified", "role": "evidence", "scope": "local"},
        provenance={"source": "doc7", "pass_id": pass_id, "ts": "t0"},
    )


def _correct() -> Slice:
    return Slice(
        claims=[_claim("alpha beta gamma", "p1"), _claim("delta epsilon zeta", "p1")],
        pass_id="p1",
    )


def _matched_wrong() -> Slice:
    # same shape, same schemas, same token length; different content + pass
    return Slice(
        claims=[_claim("eta theta iota", "p2"), _claim("kappa lambda mu", "p2")],
        pass_id="p2",
    )


def test_matched_wrong_is_admissible():
    rep = match(_correct(), _matched_wrong())
    assert rep.ok, str(rep)
    assert is_admissible_wrong_slice(_correct(), _matched_wrong())


def test_identical_slice_is_not_actually_wrong():
    # a "wrong" slice identical to the correct one must be rejected
    rep = match(_correct(), _correct())
    assert not rep.ok
    failed = {c.name for c in rep.failed()}
    assert "actually_different" in failed


def test_different_token_length_fails():
    cand = _matched_wrong()
    cand.claims[0].text = "eta theta iota nu xi omicron pi rho"  # longer
    rep = match(_correct(), cand)
    assert not rep.ok
    assert "token_length" in {c.name for c in rep.failed()}


def test_token_tolerance_allows_small_drift():
    cand = _matched_wrong()
    cand.claims[0].text = "eta theta iota nu"  # one extra whitespace token
    # exact (tol=0) must fail; a tolerance must let it through
    exact = match(_correct(), cand)
    assert not exact.ok
    assert "token_length" in {c.name for c in exact.failed()}
    assert match(_correct(), cand, token_tolerance=5).ok


def test_different_claim_count_fails():
    cand = _matched_wrong()
    cand.claims.append(_claim("nu xi omicron", "p2"))
    rep = match(_correct(), cand)
    assert not rep.ok
    assert "claim_count" in {c.name for c in rep.failed()}


def test_different_status_schema_fails():
    cand = _matched_wrong()
    # drop a status field -> schema differs even if count-of-fields is rebalanced
    del cand.claims[0].status["scope"]
    rep = match(_correct(), cand)
    assert not rep.ok
    assert "status_field_schema" in {c.name for c in rep.failed()}


def test_extra_status_key_fails_even_with_equal_count():
    # equal *number* of status fields but a different key set must still fail:
    # the multiset check is stronger than a bare count.
    cand = _matched_wrong()
    cand.claims[0].status = {"validity": "v", "role": "r", "EXTRA": "x"}
    rep = match(_correct(), cand)
    assert not rep.ok
    assert "status_field_schema" in {c.name for c in rep.failed()}


def test_different_provenance_schema_fails():
    cand = _matched_wrong()
    del cand.claims[0].provenance["ts"]
    rep = match(_correct(), cand)
    assert not rep.ok
    assert "provenance_field_schema" in {c.name for c in rep.failed()}


def test_provenance_values_may_differ():
    # only provenance *keys* must match; values (e.g. pass_id) differ by design
    rep = match(_correct(), _matched_wrong())
    assert rep.ok
    ok_names = {c.name for c in rep.criteria if c.ok}
    assert "provenance_field_schema" in ok_names


def test_different_format_fails():
    cand = _matched_wrong()
    cand.fmt = "desi.slice.v2"
    rep = match(_correct(), cand)
    assert not rep.ok
    assert "format" in {c.name for c in rep.failed()}


def test_different_outline_fails():
    correct = _correct()
    correct.outline = ["intro", "evidence"]
    cand = _matched_wrong()
    cand.outline = ["evidence", "intro"]  # same labels, different order
    rep = match(correct, cand)
    assert not rep.ok
    assert "structure_outline" in {c.name for c in rep.failed()}


def test_different_section_assignment_fails():
    correct = _correct()
    correct.claims[0].section = "intro"
    cand = _matched_wrong()
    cand.claims[0].section = "evidence"  # claim placed in a different section
    rep = match(correct, cand)
    assert not rep.ok
    assert "structure_outline" in {c.name for c in rep.failed()}


def test_matching_outline_and_sections_pass():
    correct = _correct()
    correct.outline = ["intro", "evidence"]
    correct.claims[0].section = "intro"
    correct.claims[1].section = "evidence"
    cand = _matched_wrong()
    cand.outline = ["intro", "evidence"]
    cand.claims[0].section = "intro"
    cand.claims[1].section = "evidence"
    assert match(correct, cand).ok


def test_content_hash_is_deterministic_and_distinguishing():
    assert content_hash(_correct()) == content_hash(_correct())
    assert content_hash(_correct()) != content_hash(_matched_wrong())


def test_report_str_is_readable():
    s = str(match(_correct(), _matched_wrong()))
    assert "ADMISSIBLE" in s
    s2 = str(match(_correct(), _correct()))
    assert "REJECTED" in s2
