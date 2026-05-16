"""Aufgabe 7 — verify every reviewer's raw_output_hash is reproducible
from the on-disk markdown."""
from __future__ import annotations

from ._helpers import (
    CORRUPT_ROOT,
    REVIEW_ROOT,
    load_corrupted,
    load_results,
    sha16,
)


def test_each_reviewer_raw_output_hash_matches_file() -> None:
    results = load_results()
    for rev in results["reviewers"]:
        rid = rev["reviewer_id"]
        p = REVIEW_ROOT / "reviews" / f"{rid}_review.md"
        assert p.exists(), f"missing review file for {rid}"
        actual = sha16(p)
        assert rev["raw_output_hash"] == actual, (
            f"{rid}: results hash {rev['raw_output_hash']!r} "
            f"does not match file hash {actual!r}"
        )


def test_corrupted_reviewer_raw_output_hash_matches_file() -> None:
    c = load_corrupted()
    for rev in c["reviewers"]:
        rid = rev["reviewer_id"]
        p = CORRUPT_ROOT / "reviews" / f"{rid}_review.md"
        assert p.exists(), f"missing corrupted review for {rid}"
        actual = sha16(p)
        assert rev["raw_output_hash"] == actual


def test_corrupted_prompt_hash_matches_file() -> None:
    c = load_corrupted()
    actual = sha16(CORRUPT_ROOT / "reviewer_prompt.md")
    assert c["corrupted_prompt_hash"] == actual


def test_runtime_v28_replay_hashes_still_pinned() -> None:
    """Aufgabe 7 — the cross-review work must not have moved the
    canonical v2.8 hashes the bundle promises."""
    import sys
    sys.path.insert(0, str(REVIEW_ROOT.parents[1] / "src"))
    from desi.rule_patch_protocol import (
        RulePatchProtocol,
        causal_chain_v2_7_candidate,
        fake_rule_without_guards_candidate,
    )
    proto = RulePatchProtocol()
    assert (proto.run(causal_chain_v2_7_candidate()).replay_hash
            == "1f4d9dfe44cb16e1")
    assert (proto.run(fake_rule_without_guards_candidate()).replay_hash
            == "d83d81ab8417c022")
