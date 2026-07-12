"""Tests for the significance corpus and the v1->v2 R1 hardening (LLM-free)."""
from __future__ import annotations

from desi.case_studies.marcognity_muse_spark.redteam.hard2 import rules
from desi.case_studies.marcognity_muse_spark.redteam.hard2.items import Flag2
from desi.case_studies.marcognity_muse_spark.redteam.sig_corpus.items import SIG_CORPUS, split


def _pr(items, det):
    tp = fp = fn = 0
    for it in items:
        pred = det(it.text)
        tp += pred and it.is_sig
        fp += pred and not it.is_sig
        fn += (not pred) and it.is_sig
    p = tp / (tp + fp) if tp + fp else 1.0
    r = tp / (tp + fn) if tp + fn else 1.0
    return p, r


def test_corpus_shape_and_balance():
    assert len(SIG_CORPUS) == 48
    for name in ("dev", "test"):
        s = split(name)
        assert len(s) == 24
        assert sum(i.is_sig for i in s) == 12          # balanced
    # test split must not reuse dev item ids
    assert not ({i.id for i in split("dev")} & {i.id for i in split("test")})


def test_v1_is_frozen_high_precision_low_generalisation():
    # v1 never false-fires, but barely generalises to novel phrasing (the finding)
    p_dev, r_dev = _pr(split("dev"), rules.detect_significance_not_importance)
    p_test, r_test = _pr(split("test"), rules.detect_significance_not_importance)
    assert p_dev == 1.0 and p_test == 1.0
    assert r_test < 0.2                                # near-zero recall on held-out phrasing


def test_v2_hardened_generalises_on_held_out_test():
    p_dev, r_dev = _pr(split("dev"), rules.detect_significance_not_importance_v2)
    p_test, r_test = _pr(split("test"), rules.detect_significance_not_importance_v2)
    assert r_dev == 1.0                                # fit on dev
    # blind test split: big recall gain, precision fully retained
    assert r_test >= 0.9
    assert p_test == 1.0


def test_v2_no_regression_on_hard2_significance():
    from desi.case_studies.marcognity_muse_spark.redteam.hard2.items import HARD2_ITEMS
    SIG = Flag2.SIGNIFICANCE_NOT_IMPORTANCE
    for it in HARD2_ITEMS:
        # v2 must still flag exactly the gold-SIG items on the dev benchmark
        assert rules.detect_significance_not_importance_v2(it.text) == (SIG in it.gold)
