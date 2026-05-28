"""Targeted tests for the DESi Wikipedia dual-layer v2 probe (offline, deterministic)."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "probes" / "wikipedia_dual_layer_v2"))
sys.path.insert(0, str(_REPO / "probes" / "wikipedia_dual_layer"))
sys.path.insert(0, str(_REPO / "probes" / "wikipedia_epistemic_compression"))

import dual_layer as v1dl  # noqa: E402
import dual_layer_v2 as v2  # noqa: E402
import freeze_v2  # noqa: E402
import preregistration as prereg  # noqa: E402
from fetch import get_article  # noqa: E402
from freeze import load_frozen as load_frozen_v1  # noqa: E402

# two BYTE-IDENTICAL claim sentences in different contexts -> bare-locator collision
_SHARED = "The widely shared historical sentence concerning Foo and Bar signed in 1920."
_DUP = {
    "title": "Dup", "pageid": 2,
    "plaintext": (
        "== A ==\n"
        f"Alpha opening context here today. {_SHARED} Beta closing tail one here.\n"
        "== B ==\n"
        f"Gamma different context here now. {_SHARED} Delta closing tail two here.\n"),
    "wikitext": "x<ref>a</ref>",
}


def test_preregistration_constants():
    assert prereg.LOCATOR_LEN == 6 and prereg.NEW_SEED == 20260601
    assert 0 < prereg.SECTION_BUDGET_FRAC < 1 and prereg.SECTION_BUDGET_MIN >= 1


def test_composite_anchor_fields():
    units = v1dl.segment(_DUP["plaintext"])
    a = v2.composite_anchor(units, 1)
    for k in ("span_hash", "locator", "prev_fp", "next_fp", "section_path", "start", "end"):
        assert k in a
    assert len(a["span_hash"]) == prereg.SPAN_HASH_HEX


def test_span_hash_deterministic_and_discriminating():
    assert v2._span_hash("alpha beta gamma") == v2._span_hash("alpha beta gamma")
    assert v2._span_hash("alpha beta gamma") != v2._span_hash("alpha beta delta")


def test_resolve_exact_matches_on_frozen_span():
    out = v2.build_dual_layer_v2(_DUP)
    cold, anchors = out["cold_text"], out["anchors"]
    assert anchors and all(v2.resolve_exact(a, cold) for a in anchors)
    assert out["metrics"]["offset_integrity"] == 1.0


def test_composite_anchor_beats_bare_locator_on_collision():
    """The key lever: neighbour fingerprints disambiguate identical sentences."""
    out = v2.build_dual_layer_v2(_DUP)
    units, anchors = out["units"], out["anchors"]
    shared = [a for a in anchors if "foo" in a["locator"] or "shared" in a["locator"]]
    assert len(shared) == 2                       # both duplicate claims are active
    bare_ok = sum(1 for a in shared if v1dl.resolve_locator(a, units)[1])
    comp_ok = sum(1 for a in shared if v2.resolve_fuzzy(a, units)[1])
    assert bare_ok < 2                            # bare locator collides on at least one
    assert comp_ok == 2                           # composite resolves both correctly


def test_section_budget_keeps_markers_and_is_proportional():
    units = v1dl.segment(_DUP["plaintext"])
    active = v2.build_active_state_v2(units)
    assert active["n_active_units"] <= active["n_total_units"]
    assert v2._section_budget(0) == 0
    assert v2._section_budget(100) <= prereg.SECTION_BUDGET_CAP
    assert v2._section_budget(1) >= prereg.SECTION_BUDGET_MIN


def test_metrics_ranges_and_navigable_complement():
    m = v2.build_dual_layer_v2(_DUP)["metrics"]
    for k in ("anchor_precision", "anchor_recoverability", "navigable_rate", "cold_scan_rate",
              "branch_survival", "conflict_survival", "uncertainty_survival"):
        assert 0.0 <= m[k] <= 1.0
    assert abs(m["navigable_rate"] + m["cold_scan_rate"] - 1.0) < 1e-6 or m["n_total_units"] == 0


def test_build_is_replay_deterministic():
    assert v2.build_dual_layer_v2(_DUP)["metrics"] == v2.build_dual_layer_v2(_DUP)["metrics"]


def test_new_held_out_sample_present_and_distinct():
    fr = freeze_v2.load_frozen()
    assert fr["seed"] == prereg.NEW_SEED and fr["n"] == 10 and len(fr["selected"]) == 10
    new_ids = {s["pageid"] for s in fr["selected"]}
    old_ids = {s["pageid"] for s in load_frozen_v1()["selected"]}
    assert new_ids.isdisjoint(old_ids)            # held-out: no overlap with v1 sample


def test_real_cached_articles_offline():
    old = get_article(load_frozen_v1()["selected"][0]["requested_title"], live=False)
    new = freeze_v2.get_article_v2(freeze_v2.load_frozen()["selected"][0]["requested_title"], live=False)
    for art in (old, new):
        m = v2.build_dual_layer_v2(art)["metrics"]
        assert m["offset_integrity"] == 1.0 and m["compression_ratio"] > 0.4 and m["anchor_count"] > 0
