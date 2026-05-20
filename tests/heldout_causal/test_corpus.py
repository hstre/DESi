"""Aufgaben 1 + 2 — corpus structure + independence."""
from __future__ import annotations

from collections import Counter

from desi.heldout_causal import (
    ALL_HELDOUT_CASES,
    HeldoutCategory,
    MAX_LEXICAL_MEAN,
    MAX_LEXICAL_PEAK,
    run_independence_check,
)


def test_corpus_size_meets_minimum() -> None:
    assert len(ALL_HELDOUT_CASES) >= 60


def test_each_category_count_matches_directive() -> None:
    counts = Counter(c.category for c in ALL_HELDOUT_CASES)
    assert counts[HeldoutCategory.A_LINEAR_CAUSAL] == 15
    assert counts[HeldoutCategory.B_CONDITIONAL_CHAIN] == 15
    assert counts[HeldoutCategory.C_CONTRADICTION_TRAP] == 10
    assert counts[HeldoutCategory.D_CYCLE_TRAP] == 10
    assert counts[HeldoutCategory.E_FALSE_CAUSAL_TRAP] == 10


def test_case_ids_unique() -> None:
    ids = [c.case_id for c in ALL_HELDOUT_CASES]
    assert len(ids) == len(set(ids))


def test_every_case_has_required_fields() -> None:
    for c in ALL_HELDOUT_CASES:
        d = c.to_dict()
        for field in (
            "case_id", "text", "expected_final_state",
            "expected_rule", "expected_blocked", "trap_type",
            "rationale",
        ):
            assert field in d, c.case_id


def test_independence_passes_all_gates() -> None:
    report = run_independence_check()
    assert report.exact_text_overlap == 0
    assert report.lexical_overlap_mean <= MAX_LEXICAL_MEAN
    assert report.lexical_overlap_max <= MAX_LEXICAL_PEAK
    assert report.therefore_pattern_overlap == 0
    assert report.independence_passed is True


def test_held_out_texts_disjoint_from_v23() -> None:
    from desi.benchmark_multistep import ALL_MULTISTEP_CASES
    v23_texts = {c.text for c in ALL_MULTISTEP_CASES}
    for c in ALL_HELDOUT_CASES:
        assert c.text not in v23_texts, (
            f"{c.case_id} reuses a v2.3 text verbatim"
        )
