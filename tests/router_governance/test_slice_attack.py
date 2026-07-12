"""#5 supersession, #2 k-stability, and #7 the unified slice-attack pass."""
from __future__ import annotations

from desi_router.governance import attack_slice, select_mode, verdict_unstable
from desi_router.governance.benchmark.pws_metrics import evaluate_pws
from desi_router.governance.report import report_from_snapshot
from desi_router.governance.supersession import omitted_newer_siblings


class _Snap:
    conflicts = ()
    provenance = type("P", (), {"snapshot_hash": "t"})()


def _rep(**extra):
    base = dict(selected_claim_ids=("c1",), selected_claim_texts=("a fact",),
                extraction_confidence=0.95, state_recall_estimate=1.0)
    base.update(extra)
    return report_from_snapshot("t", _Snap(), **base)


# --- #5 supersession --------------------------------------------------------------------------- #

def test_omitted_newer_siblings_filters_surfaced():
    assert omitted_newer_siblings(("c1",), ("g1", "g2", "g1")) == ("g1", "g2")
    assert omitted_newer_siblings(("c1", "g1"), ("g1",)) == ()


def test_newer_sibling_routes_to_caution():
    r = _rep(newer_sibling_ids=("g_newer",), newer_sibling_texts=("newer same-scope version",))
    assert r.omitted_supersession_ids == ("g_newer",)
    assert r.risk_scores["stale_supersession"] == 0.6
    assert select_mode(r).persistent_state_update_allowed is False
    assert _rep().risk_scores["stale_supersession"] == 0.0     # absent unless supplied


# --- #2 k-stability ---------------------------------------------------------------------------- #

def test_verdict_unstable_on_escalation():
    narrow = select_mode(_rep())                                           # clean -> state_slice/update
    wide = select_mode(_rep(graph_opposition_ids=("g",)))                  # opposition -> guarded
    assert verdict_unstable(narrow, wide)["unstable"] is True
    assert verdict_unstable(narrow, narrow)["unstable"] is False


# --- #7 unified attack ------------------------------------------------------------------------- #

def test_attack_fires_the_right_vectors():
    r = _rep(graph_opposition_ids=("g_opp",), newer_sibling_ids=("g_new",),
             provenance_sources=("s", "s"), selected_claim_ids=("c1", "c2"),
             selected_claim_texts=("a", "b"), task_scope="A", claim_scopes=("B", "A"))
    res = attack_slice(r)
    assert set(res.fired) >= {"omitted_opposition", "same_scope_newer",
                              "thin_provenance", "scope_mismatch"}
    assert res.survived is False
    assert res.decision.persistent_state_update_allowed is False


def test_clean_slice_survives_the_attack():
    res = attack_slice(_rep())
    assert res.survived is True and res.fired == ()
    assert res.decision.persistent_state_update_allowed is True


def test_k_unstable_vector_uses_the_wide_report():
    narrow = _rep()                                            # clean
    wide = _rep(graph_opposition_ids=("g",))                   # widened -> opposition
    res = attack_slice(narrow, wide_report=wide)
    assert "k_unstable" in res.fired and res.survived is False


# --- benchmark: all five vectors close, no over-caution ---------------------------------------- #

def test_benchmark_all_vectors_close():
    blind = evaluate_pws(aware=False)
    aware = evaluate_pws(aware=True)
    for v in ("missing_opposition", "provenance_entropy", "scope_match",
              "supersession", "k_stability"):
        assert blind["false_clean_by_subset"][v] == 1.0
        assert aware["false_clean_by_subset"][v] == 0.0
    assert aware["false_clean_rate"] == 0.0
    assert aware["over_caution_rate"] == 0.0
