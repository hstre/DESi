"""Targeted tests for the DESi Wikipedia epistemic-compression probe (offline, deterministic)."""
from __future__ import annotations

import random
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
_REPO = _HERE.parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "probes" / "wikipedia_epistemic_compression"))

import epistemic_state as es  # noqa: E402
from fetch import get_article  # noqa: E402
from freeze import SEED, load_frozen  # noqa: E402

_ART = {
    "title": "Test Topic", "pageid": 1,
    "plaintext": (
        "== Lead ==\n"
        "The Treaty of Foo was signed in 1920 by King Bar of Quux. "
        "Some scholars argue the date was actually 1921, however others contend it was 1919. "
        "The underlying cause remains uncertain and is thought to be disputed by historians. "
        "The Empire of Baz expanded across the region during the 13th century.\n"
        "== Legacy ==\n"
        "Later writers possibly exaggerated the importance of the Treaty of Foo.\n"),
    "wikitext": "Foo<ref>a</ref> bar<ref name=x>b</ref> baz {{cite book|title=Z}} {{sfn|Y|2020}}",
}


def test_token_count_deterministic_and_positive():
    t = es.token_count("The Treaty of Foo, signed in 1920.")
    assert t == es.token_count("The Treaty of Foo, signed in 1920.") and t > 0
    assert es.token_count("") == 0


def test_anchors_skip_initial_capital_and_catch_numbers():
    a = es.anchors("The Treaty of Foo was signed in 1920 by King Bar")
    assert {"treaty", "foo", "king", "bar"} <= a   # mid-sentence proper nouns captured
    assert "1920" in a                             # numeric anchor
    assert "the" not in a                          # index-0 word skipped
    # a sentence-initial proper noun (index 0) is skipped:
    assert "foo" not in es.anchors("Foo signed the treaty in 1920")


def test_cue_detection():
    assert es._has_cue("some scholars argue otherwise", es.BRANCH_CUES)
    assert es._has_cue("this however contradicts the record", es.CONFLICT_CUES)
    assert es._has_cue("the date remains uncertain", es.UNCERTAINTY_CUES)
    assert not es._has_cue("the cat sat on the mat", es.BRANCH_CUES)


def test_citation_counting():
    assert es.count_citations(_ART["wikitext"]) == 4   # 2x <ref + {{cite + {{sfn


def test_build_state_preserves_structure_existence():
    s = es.build_state(_ART, frame_fn=None)
    m = s["metrics"]
    assert m["branch_count"] >= 1 and m["conflict_count"] >= 1 and m["uncertainty_markers"] >= 1
    assert m["citation_anchors"] == 4
    # existence-level preservation flags hold; prose is NOT kept
    assert m["branches_preserved"] == 1.0 and m["conflicts_preserved"] == 1.0
    assert m["uncertainty_preserved"] == 1.0 and m["prose_tokens_in_state"] == 0
    assert 0.0 <= m["recoverability_proxy"] <= 1.0
    assert m["claims_kept"] <= es.CLAIM_BUDGET


def test_build_state_is_replay_deterministic():
    a = es.build_state(_ART, frame_fn=None)["metrics"]
    b = es.build_state(_ART, frame_fn=None)["metrics"]
    assert a == b


def test_selection_rule_is_seed_deterministic():
    pool = sorted(f"Article {i:03d}" for i in range(200))
    a = random.Random(SEED).sample(pool, 10)
    assert a == random.Random(SEED).sample(pool, 10)     # reproducible
    assert a != random.Random(1).sample(pool, 10)        # seed actually matters


def test_frozen_set_is_present_and_well_formed():
    fr = load_frozen()
    assert fr["seed"] == SEED and fr["n"] == 10 and len(fr["selected"]) == 10
    assert fr["pool_size"] > 0 and len(fr["pool_sha256"]) == 64
    for s in fr["selected"]:
        assert s["title"] and s["pageid"]


def test_real_cached_article_compresses():
    """Replay from the committed cache (offline): a real article compresses strongly."""
    fr = load_frozen()
    sel = fr["selected"][0]
    art = get_article(sel["requested_title"], live=False)   # cache hit, no network
    m = es.build_state(art, frame_fn=None)["metrics"]
    assert m["raw_tokens"] > m["desi_state_tokens"] > 0
    assert m["compression_ratio"] > 0.5                     # real articles are long -> strong compression
    assert 0.0 <= m["recoverability_proxy"] <= 1.0
