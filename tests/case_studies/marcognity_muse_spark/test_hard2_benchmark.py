"""Tests for the HARD2 benchmark (8 flags, items, blind prompt, shared scorer)."""
from __future__ import annotations

from desi.case_studies.marcognity_muse_spark.redteam.hard import score
from desi.case_studies.marcognity_muse_spark.redteam.hard2 import prompt
from desi.case_studies.marcognity_muse_spark.redteam.hard2.items import HARD2_ITEMS, Flag2


def test_item_set_shape():
    assert len(HARD2_ITEMS) == 18
    clean = [i for i in HARD2_ITEMS if not i.gold]
    single = [i for i in HARD2_ITEMS if len(i.gold) == 1]
    multi = [i for i in HARD2_ITEMS if len(i.gold) >= 2]
    assert len(single) == 7          # one flag each
    assert len(multi) == 2           # entangled multi-flag items (the discriminator)
    assert len(clean) == 9           # adversarial-control heavy, to test false positives
    # every item's tell and difficulty are stated
    for it in HARD2_ITEMS:
        assert it.tell and it.difficulty in ("medium", "hard")


def test_uses_all_eight_flags():
    used = set().union(*(set(i.gold) for i in HARD2_ITEMS))
    assert used == set(Flag2)        # every flag appears in at least one gold label


def test_near_miss_pairs_differ_in_gold():
    by_id = {i.id: i for i in HARD2_ITEMS}
    pairs = {(i.id, i.pair) for i in HARD2_ITEMS if i.pair}
    assert pairs, "expected near-miss pairs"
    for a, b in pairs:
        assert by_id[a].gold != by_id[b].gold   # a pair separates a failure from a clean twin


def test_blind_prompt_leaks_no_gold():
    p = prompt.build_prompt()
    # neutral ids only; the original G.. ids and the answer key must not appear
    for it in HARD2_ITEMS:
        assert it.id not in p
        assert it.tell not in p
    assert "N1:" in p and "N18:" in p
    assert p.count("gold") == 0


def test_scorer_perfect_and_degenerate():
    perfect = {it.id: set(it.gold) for it in HARD2_ITEMS}
    s = score.score_runs("perfect", [perfect], HARD2_ITEMS)
    assert s["f1_mean"] == 1.0 and s["exact_match_mean"] == 1.0

    nothing = {it.id: set() for it in HARD2_ITEMS}
    n = score.score_runs("nothing", [nothing], HARD2_ITEMS)
    assert n["recall_mean"] == 0.0 and n["precision_mean"] == 1.0  # no FP, no TP
    assert n["exact_match_mean"] == round(9 / 18, 3)              # 9 clean items right

    allf = {it.id: set(Flag2) for it in HARD2_ITEMS}
    a = score.score_runs("all", [allf], HARD2_ITEMS)
    assert a["recall_mean"] == 1.0 and a["precision_mean"] < 0.2  # over-flagging punished


def test_scorer_reports_per_item_errors_and_is_deterministic():
    # a reviewer that misses one flag on a multi-flag item is caught per-item
    multi = next(i for i in HARD2_ITEMS if len(i.gold) == 2)
    partial = {it.id: (set(list(it.gold)[:1]) if it.id == multi.id else set(it.gold))
               for it in HARD2_ITEMS}
    s1 = score.score_runs("partial", [partial], HARD2_ITEMS)
    s2 = score.score_runs("partial", [partial], HARD2_ITEMS)
    assert s1 == s2                                    # deterministic
    assert s1["item_exact_rate"][multi.id] == 0.0      # the multi-flag item is not exact
    assert multi.id in s1["item_errors"]


def test_parse_answer_maps_neutral_ids_and_ignores_unknown():
    nmap = prompt.neutral_map()
    answer = '{"N1": ["causal_overreach", "bogus_flag"]}'
    parsed = prompt.parse_answer(answer)
    target_item = nmap["N1"]
    assert Flag2.CAUSAL_OVERREACH in parsed[target_item]
    assert all(isinstance(f, Flag2) for f in parsed[target_item])   # bogus dropped
