"""Aufgaben 1 + 2 — corpus structure + independence."""
from __future__ import annotations

from collections import Counter

from desi.causal_redteam import (
    ALL_ADVERSARIAL_CASES,
    AttackFamily,
    run_independence_check,
)


def test_corpus_size_meets_minimum() -> None:
    assert len(ALL_ADVERSARIAL_CASES) >= 100


def test_corpus_distribution_matches_directive() -> None:
    counts = Counter(c.attack_family for c in ALL_ADVERSARIAL_CASES)
    assert counts[AttackFamily.A_HIDDEN_NEGATION] == 15
    assert counts[AttackFamily.B_QUANTIFIER_DRIFT] == 15
    assert counts[AttackFamily.C_AUTHORITY_INSERTION] == 15
    assert counts[AttackFamily.D_METAPHOR_INSERTION] == 15
    assert counts[AttackFamily.E_FRAME_SWITCH] == 15
    assert counts[AttackFamily.F_TOOL_CONTAMINATION] == 10
    assert counts[AttackFamily.G_CYCLE_DISGUISE] == 10
    assert counts[AttackFamily.H_SEMANTIC_LEAP] == 5


def test_case_ids_unique() -> None:
    ids = [c.case_id for c in ALL_ADVERSARIAL_CASES]
    assert len(ids) == len(set(ids))


def test_every_case_marked_expected_blocked() -> None:
    for c in ALL_ADVERSARIAL_CASES:
        assert c.expected_blocked is True, c.case_id


def test_required_fields_present() -> None:
    for c in ALL_ADVERSARIAL_CASES:
        d = c.to_dict()
        for f in (
            "case_id", "text", "attack_family", "attack_goal",
            "expected_blocked", "rationale",
        ):
            assert f in d, c.case_id


def test_independence_passes() -> None:
    r = run_independence_check()
    assert r.exact_overlap == 0
    assert r.independence_passed is True


def test_independence_against_v23_v26_v314() -> None:
    from desi.benchmark import ALL_CASES as ALL_MAIN_CASES
    from desi.benchmark_multistep import ALL_MULTISTEP_CASES
    from desi.heldout_causal import ALL_HELDOUT_CASES
    upstream = {c.text for c in ALL_MAIN_CASES}
    upstream |= {c.text for c in ALL_MULTISTEP_CASES}
    upstream |= {c.text for c in ALL_HELDOUT_CASES}
    for c in ALL_ADVERSARIAL_CASES:
        assert c.text not in upstream, (
            f"{c.case_id} reuses an upstream text verbatim"
        )
