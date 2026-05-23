"""Aufgabe 7 — verify the v3.3 result + agreement schemas."""
from __future__ import annotations

from ._helpers import load_agreement, load_corrupted, load_results


_RESULT_FIELDS = {
    "reviewer_id", "model_name", "timestamp",
    "hash_verified", "replay_verified",
    "unverifiable_claims", "hidden_assumptions",
    "contamination_risks",
    "falsifiability_score", "raw_output_hash",
}


_AGREEMENT_FIELDS = {
    "total_reviewers",
    "hash_agreement_rate",
    "replay_agreement_rate",
    "shared_hidden_assumptions",
    "shared_contamination_risks",
    "mean_falsifiability",
    "std_falsifiability",
}


def test_results_has_required_top_level_fields() -> None:
    r = load_results()
    for k in ("schema_version", "reviewer_prompt_hash",
              "questions_hash", "reviewers"):
        assert k in r


def test_at_least_three_reviewers() -> None:
    r = load_results()
    assert len(r["reviewers"]) >= 3


def test_every_reviewer_has_required_fields() -> None:
    r = load_results()
    for rev in r["reviewers"]:
        missing = _RESULT_FIELDS - set(rev.keys())
        assert not missing, (
            f"reviewer {rev.get('reviewer_id')!r} missing {missing}"
        )


def test_reviewer_ids_unique() -> None:
    r = load_results()
    ids = [rev["reviewer_id"] for rev in r["reviewers"]]
    assert len(set(ids)) == len(ids)


def test_falsifiability_scores_are_integers_in_0_10() -> None:
    r = load_results()
    for rev in r["reviewers"]:
        s = rev["falsifiability_score"]
        assert isinstance(s, int)
        assert 0 <= s <= 10


def test_agreement_has_required_fields() -> None:
    a = load_agreement()
    missing = _AGREEMENT_FIELDS - set(a.keys())
    assert not missing, f"agreement_report missing {missing}"


def test_corrupted_has_three_corruptions() -> None:
    c = load_corrupted()
    assert len(c["corruption_inventory"]) == 3
    kinds = {item["kind"] for item in c["corruption_inventory"]}
    assert kinds == {
        "wrong_hash", "wrong_artifact_path", "wrong_factual_claim",
    }


def test_corrupted_results_lists_three_reviewers() -> None:
    c = load_corrupted()
    assert len(c["reviewers"]) >= 3
