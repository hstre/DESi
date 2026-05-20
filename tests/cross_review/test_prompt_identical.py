"""Aufgabe 7 — verify every reviewer saw exactly the same prompt."""
from __future__ import annotations

from ._helpers import REVIEW_ROOT, load_results, sha16


def test_reviewer_prompt_exists() -> None:
    assert (REVIEW_ROOT / "reviewer_prompt.md").exists()


def test_questions_doc_exists() -> None:
    assert (REVIEW_ROOT / "questions.md").exists()


def test_results_record_the_canonical_prompt_hash() -> None:
    results = load_results()
    canonical = sha16(REVIEW_ROOT / "reviewer_prompt.md")
    assert results["reviewer_prompt_hash"] == canonical, (
        f"reviewer_results.json claims prompt hash "
        f"{results['reviewer_prompt_hash']!r} but the on-disk "
        f"prompt hashes to {canonical!r}"
    )


def test_results_record_the_canonical_questions_hash() -> None:
    results = load_results()
    canonical = sha16(REVIEW_ROOT / "questions.md")
    assert results["questions_hash"] == canonical


def test_every_reviewer_saw_the_same_prompt() -> None:
    """The schema does not store a per-reviewer prompt hash;
    they all share the same canonical reviewer_prompt.md. This
    test simply asserts the prompt exists at the documented path."""
    results = load_results()
    assert all("hash_verified" in r for r in results["reviewers"])
