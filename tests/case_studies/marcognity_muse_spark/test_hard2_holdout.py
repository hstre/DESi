"""Tests for the blind hold-out set + the FROZEN rules' behaviour on it.

These pin the hold-out's shape, its blind batched prompt, and the frozen rules'
*intrinsic* behaviour on the new text — including the documented brittleness
(R1 recall drops from 1.0 on the dev set to 0.571 here). No rule tuning.
"""
from __future__ import annotations

from desi.case_studies.marcognity_muse_spark.redteam.hard2 import rules
from desi.case_studies.marcognity_muse_spark.redteam.hard2.items import Flag2
from desi.case_studies.marcognity_muse_spark.redteam.hard2_holdout import prompt
from desi.case_studies.marcognity_muse_spark.redteam.hard2_holdout.items import HOLDOUT_ITEMS

SIG = Flag2.SIGNIFICANCE_NOT_IMPORTANCE
_TEXT = {it.id: it.text for it in HOLDOUT_ITEMS}


def test_holdout_shape_and_all_flags():
    assert len(HOLDOUT_ITEMS) == 27
    assert set().union(*(set(i.gold) for i in HOLDOUT_ITEMS)) == set(Flag2)
    for it in HOLDOUT_ITEMS:
        assert it.tell and it.difficulty in ("medium", "hard")


def test_holdout_disjoint_from_dev_ids():
    from desi.case_studies.marcognity_muse_spark.redteam.hard2.items import HARD2_ITEMS
    assert not ({i.id for i in HOLDOUT_ITEMS} & {i.id for i in HARD2_ITEMS})


def test_batched_prompt_respects_k_and_leaks_nothing():
    ps = prompt.build_prompts()
    assert ps and all(len(idm) <= 10 for _, idm in ps)          # granite k*=10 band
    assert sum(len(idm) for _, idm in ps) == len(HOLDOUT_ITEMS)  # every item covered once
    for txt, _ in ps:
        assert "gold" not in txt.lower()
        for it in HOLDOUT_ITEMS:
            assert it.id not in txt and it.tell not in txt


def test_parse_answer_uses_batch_id_map():
    _, id_map = prompt.build_prompts()[0]
    nid = next(iter(id_map))
    parsed = prompt.parse_answer('{"%s": ["significance_not_importance", "junk"]}' % nid, id_map)
    assert SIG in parsed[id_map[nid]]
    assert all(isinstance(f, Flag2) for f in parsed[id_map[nid]])


def test_frozen_r1_high_precision_moderate_recall_on_holdout():
    fires = {it.id for it in HOLDOUT_ITEMS if rules.detect_significance_not_importance(it.text)}
    gold = {it.id for it in HOLDOUT_ITEMS if SIG in it.gold}
    # perfect precision: never fires on a non-SIG item (incl. hard negatives H06/H07/H08)
    assert fires <= gold
    for hn in ("H06", "H07", "H08"):
        assert not rules.detect_significance_not_importance(_TEXT[hn])
    # documented brittleness: catches canonical forms, misses lexicon-evading paraphrases
    assert {"H01", "H27"} <= fires
    assert {"H04", "H05"} & gold and not ({"H04", "H05"} & fires)
    # recall strictly between the dev-set 1.0 and 0 — it generalises partially
    assert 0.4 < len(fires) / len(gold) < 0.8
