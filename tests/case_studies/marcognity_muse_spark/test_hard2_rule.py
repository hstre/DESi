"""Tests for the deterministic hard2 rules (rules.py) and the +rule accuracy gain."""
from __future__ import annotations

import glob
from pathlib import Path

from desi.case_studies.marcognity_muse_spark.redteam.hard import score
from desi.case_studies.marcognity_muse_spark.redteam.hard2 import prompt, rules
from desi.case_studies.marcognity_muse_spark.redteam.hard2.items import HARD2_ITEMS, Flag2

_TEXT = {it.id: it.text for it in HARD2_ITEMS}
_RUNS = (Path(__file__).resolve().parents[3]
         / "src/desi/case_studies/marcognity_muse_spark/redteam/hard2/external_runs")


def test_r1_fires_exactly_on_significance_items():
    fired = {it.id for it in HARD2_ITEMS
             if rules.detect_significance_not_importance(it.text)}
    gold_sig = {it.id for it in HARD2_ITEMS if Flag2.SIGNIFICANCE_NOT_IMPORTANCE in it.gold}
    assert fired == gold_sig == {"G03", "G15"}
    # the effect-size qualifier in G04 must block R1 (clean near-miss twin)
    assert not rules.detect_significance_not_importance(_TEXT["G04"])


def test_r2_declines_on_overreaching_items_and_holds_on_supported():
    # over-generalisation ("should replace" / "national") blocks suppression
    assert not rules.suppress_overclaim(_TEXT["G03"])
    assert not rules.suppress_overclaim(_TEXT["G16"])
    # well-supported / scope-limited clean items would be suppressed if flagged
    assert rules.suppress_overclaim(_TEXT["G17"])
    assert rules.suppress_overclaim(_TEXT["G18"])


def test_apply_rules_adds_sig_and_is_idempotent():
    flags = rules.apply_rules(_TEXT["G03"], set())
    assert Flag2.SIGNIFICANCE_NOT_IMPORTANCE in flags
    assert rules.apply_rules(_TEXT["G03"], flags) == flags        # idempotent
    # a clean, unrelated item is left untouched
    assert rules.apply_rules(_TEXT["G10"], set()) == set()


def test_apply_rules_suppresses_only_when_overclaim_present():
    assert Flag2.OVERCLAIM not in rules.apply_rules(_TEXT["G17"], {Flag2.OVERCLAIM})
    # nothing to suppress if the model never raised overclaim
    assert rules.apply_rules(_TEXT["G17"], set()) == set()


def test_rule_improves_granite_8b_baseline():
    runs = []
    for f in sorted(glob.glob(str(_RUNS / "granite_8b" / "run_*.txt"))):
        t = Path(f).read_text()
        if "{" in t:
            runs.append(prompt.parse_answer(t))
    assert runs, "expected stored granite_8b runs"
    aug = [{iid: rules.apply_rules(_TEXT[iid], fl) for iid, fl in r.items()} for r in runs]
    b = score.score_runs("granite", runs, HARD2_ITEMS)
    a = score.score_runs("granite+rule", aug, HARD2_ITEMS)
    # deterministic rule adds accuracy without hurting precision (regression guard)
    assert a["f1_mean"] > b["f1_mean"] + 0.05
    assert a["recall_mean"] > b["recall_mean"]
    assert a["precision_mean"] >= b["precision_mean"]
