"""Tests for the hard epistemic-failure benchmark (items, blind prompt, scorer)."""
from __future__ import annotations

from desi.case_studies.marcognity_muse_spark.redteam.failure_modes import Flag
from desi.case_studies.marcognity_muse_spark.redteam.hard import prompt, score
from desi.case_studies.marcognity_muse_spark.redteam.hard.items import HARD_ITEMS


def test_item_set_shape():
    assert len(HARD_ITEMS) == 14
    clean = [i for i in HARD_ITEMS if not i.gold]
    multi = [i for i in HARD_ITEMS if len(i.gold) >= 2]
    assert len(clean) == 7           # adversarial-control heavy, to test false positives
    assert len(multi) == 2           # entangled multi-flag items (the discriminator)
    # every failure item's tell and difficulty are stated
    for it in HARD_ITEMS:
        assert it.tell and it.difficulty in ("medium", "hard")


def test_near_miss_pairs_differ_in_gold():
    by_id = {i.id: i for i in HARD_ITEMS}
    pairs = {(i.id, i.pair) for i in HARD_ITEMS if i.pair}
    assert pairs, "expected near-miss pairs"
    for a, b in pairs:
        assert by_id[a].gold != by_id[b].gold   # a pair separates a failure from a clean twin


def test_blind_prompt_leaks_no_gold():
    p = prompt.build_prompt()
    # neutral ids only; the original H.. ids and the answer key must not appear
    for it in HARD_ITEMS:
        assert it.id not in p
        assert it.tell not in p
    assert "N1:" in p and "N14:" in p
    # the rubric names the five flags (definitions), but not per-item labels
    assert p.count("gold") == 0


def test_scorer_perfect_and_degenerate():
    perfect = {it.id: set(it.gold) for it in HARD_ITEMS}
    s = score.score_runs("perfect", [perfect])
    assert s["f1_mean"] == 1.0 and s["exact_match_mean"] == 1.0

    nothing = {it.id: set() for it in HARD_ITEMS}
    n = score.score_runs("nothing", [nothing])
    assert n["recall_mean"] == 0.0 and n["precision_mean"] == 1.0  # no FP, no TP
    assert n["exact_match_mean"] == round(7 / 14, 3)               # 7 clean items right

    allf = {it.id: set(Flag) for it in HARD_ITEMS}
    a = score.score_runs("all", [allf])
    assert a["recall_mean"] == 1.0 and a["precision_mean"] < 0.2   # over-flagging punished


def test_scorer_reports_per_item_errors_and_is_deterministic():
    # a reviewer that misses one flag on a multi-flag item is caught per-item
    multi = next(i for i in HARD_ITEMS if len(i.gold) == 2)
    partial = {it.id: (set(list(it.gold)[:1]) if it.id == multi.id else set(it.gold))
               for it in HARD_ITEMS}
    s1 = score.score_runs("partial", [partial])
    s2 = score.score_runs("partial", [partial])
    assert s1 == s2                                    # deterministic
    assert s1["item_exact_rate"][multi.id] == 0.0      # the multi-flag item is not exact
    assert multi.id in s1["item_errors"]


def test_parse_answer_maps_neutral_ids_and_ignores_unknown():
    # build a fake answer keyed by neutral ids
    nmap = prompt.neutral_map()
    first_nid = "N1"
    answer = '{"%s": ["overclaim", "bogus_flag"]}' % first_nid
    parsed = prompt.parse_answer(answer)
    target_item = nmap[first_nid]
    assert Flag.OVERCLAIM in parsed[target_item]
    assert all(isinstance(f, Flag) for f in parsed[target_item])   # bogus dropped
