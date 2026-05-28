"""Targeted tests for the DESi Wikipedia dual-layer retrieval probe (offline, deterministic)."""
from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "probes" / "wikipedia_dual_layer"))
sys.path.insert(0, str(_REPO / "probes" / "wikipedia_epistemic_compression"))

import dual_layer as dl  # noqa: E402
from fetch import get_article  # noqa: E402
from freeze import load_frozen  # noqa: E402

_ART = {
    "title": "T", "pageid": 1,
    "plaintext": (
        "== Lead ==\n"
        "The Treaty of Foo was signed in 1920 by King Bar of Quux. "
        "Some scholars argue the date was 1921, however others contend it was 1919. "
        "The underlying cause remains uncertain to historians.\n"
        "== Body ==\n"
        "The Empire of Baz expanded across the region in the 13th century. "
        "The Empire of Baz expanded across the region in the 13th century.\n"),  # duplicate -> collision
    "wikitext": "x<ref>a</ref>",
}


def test_segment_offsets_are_exact():
    units = dl.segment(_ART["plaintext"])
    assert units
    for u in units:
        assert _ART["plaintext"][u["start"]:u["end"]].strip() == u["text"]
    # section indices: Lead (0) then Body (1)
    assert {u["section_idx"] for u in units} == {0, 1}


def test_classify_detects_kinds():
    assert "claim" in dl.classify("The Treaty of Foo was signed in 1920 by King Bar")
    assert "branch" in dl.classify("Some scholars argue the opposite")
    assert "conflict" in dl.classify("This however contradicts the record")
    assert "uncertainty" in dl.classify("The date remains uncertain")
    assert dl.classify("the cat sat") == []


def test_active_state_keeps_markers_and_budget():
    units = dl.segment(_ART["plaintext"])
    active = dl.build_active_state(units)
    assert active["n_active_units"] <= active["n_total_units"]
    # every branch/conflict/uncertainty unit is kept active
    kinds = [a["kinds"] for a in active["anchors"]]
    flat = {k for ks in kinds for k in ks}
    assert {"branch", "conflict", "uncertainty"} <= flat


def test_offset_retrieval_is_exact():
    units = dl.segment(_ART["plaintext"])
    a = dl.build_active_state(units)["anchors"][0]
    assert dl.resolve_offset(a, _ART["plaintext"]) == _ART["plaintext"][a["start"]:a["end"]]


def test_locator_collision_is_detected():
    """The duplicated sentence must cause at least one locator mis-resolution."""
    out = dl.build_dual_layer(_ART)
    units, anchors = out["units"], out["anchors"]
    results = [dl.resolve_locator(a, units)[1] for a in anchors]
    assert out["metrics"]["offset_integrity"] == 1.0      # offsets always exact
    assert not all(results)                               # the duplicate collides -> some incorrect
    assert 0.0 <= out["metrics"]["anchor_precision"] < 1.0


def test_metrics_shape_and_ranges():
    m = dl.build_dual_layer(_ART)["metrics"]
    for k in ("anchor_precision", "anchor_recoverability", "cold_access_rate",
              "branch_survival", "conflict_survival", "uncertainty_survival"):
        assert 0.0 <= m[k] <= 1.0
    # cold_access_rate is the no-anchor fallback fraction
    assert m["cold_access_rate"] == round((m["n_total_units"] - m["n_active_units"]) / m["n_total_units"], 3)


def test_build_dual_layer_is_replay_deterministic():
    a = dl.build_dual_layer(_ART)["metrics"]
    b = dl.build_dual_layer(_ART)["metrics"]
    assert a == b


def test_reuses_same_frozen_set():
    fr = load_frozen()
    assert fr["seed"] == 20260528 and fr["n"] == 10 and len(fr["selected"]) == 10


def test_real_cached_article_dual_layer():
    """Replay from the committed cache (offline): offsets exact, strong compression."""
    sel = load_frozen()["selected"][0]
    art = get_article(sel["requested_title"], live=False)
    out = dl.build_dual_layer(art)
    m = out["metrics"]
    assert m["offset_integrity"] == 1.0
    assert m["compression_ratio"] > 0.5 and m["anchor_count"] > 0
    # every anchor offset resolves to a non-empty span inside cold text
    for a in out["anchors"][:20]:
        assert dl.resolve_offset(a, out["cold_text"]).strip()
