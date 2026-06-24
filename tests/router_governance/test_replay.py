"""Phase-2 replay tests: the router routed against the REAL ablation artefacts.

Assert the load-bearing finding, not a headline number: structural risks (no usable state, open
conflict) are caught whether or not Layer-9 signals them; a plausible-wrong slice is caught ONLY in
the signaled pass — so the router's protection against undetectable wrong state equals its input
signal, no better."""
from __future__ import annotations

from desi_router.governance.benchmark.replay import replay


def test_replay_runs_over_real_artifacts():
    r = replay()
    assert r["points"] > 0
    assert any("sonnet" in m for m in r["models"])


def test_signaled_pass_is_fully_concordant():
    r = replay()
    assert r["concordance"]["signaled"] == 1.0


def test_structural_risks_caught_in_both_passes():
    r = replay()
    for ps in ("signaled", "unsignaled"):
        fam = r["by_family"][ps]
        assert fam["no_state/retrieval"] == 1.0, ps
        assert fam["open_conflict"] == 1.0, ps
        assert fam["clean"] == 1.0, ps


def test_plausible_wrong_slice_depends_on_the_signal():
    r = replay()
    assert r["by_family"]["signaled"]["plausible_wrong_slice"] == 1.0
    assert r["by_family"]["unsignaled"]["plausible_wrong_slice"] == 0.0
    # and the misses are exactly the plausible-wrong conditions, nothing structural
    missed = {d["condition"] for d in r["discordant"]["unsignaled"]}
    assert missed <= {"C_wrong_slice", "G_neutral_irrelevant"}
    assert not r["discordant"]["signaled"]
