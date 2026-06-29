"""Provenance-entropy (#4) and scope-match (#6) checks — the non-opposition plausible-wrong families."""
from __future__ import annotations

from desi_router.governance import select_mode
from desi_router.governance.provenance import assess_provenance
from desi_router.governance.report import report_from_snapshot
from desi_router.governance.scope import scope_mismatches


class _Snap:
    conflicts = ()
    provenance = type("P", (), {"snapshot_hash": "t"})()


def _rep(**extra):
    base = dict(selected_claim_ids=("c1",), selected_claim_texts=("a fact",),
                extraction_confidence=0.95, state_recall_estimate=1.0)
    base.update(extra)
    return report_from_snapshot("t", _Snap(), **base)


# --- provenance check ------------------------------------------------------------------------- #

def test_absence_of_provenance_info_is_not_a_flag():
    # two claims, no source info -> "unknown", must NOT be read as thin
    a = assess_provenance(n_claims=2, source_families=(), derived_flags=(), stale=False)
    assert a["under_support"] is False


def test_many_claims_one_root_source_is_thin():
    a = assess_provenance(n_claims=3, source_families=("r", "r", "r"))
    assert a["under_support"] is True and "many_claims_one_root_source" in a["reasons"]


def test_all_derived_and_stale_flag():
    assert assess_provenance(n_claims=2, source_families=("a", "b"),
                             derived_flags=(True, True))["under_support"] is True
    assert assess_provenance(n_claims=1, source_families=("a",), stale=True)["under_support"] is True


def test_well_sourced_slice_is_clean():
    a = assess_provenance(n_claims=2, source_families=("a", "b"), derived_flags=(False, False))
    assert a["under_support"] is False


def test_thin_provenance_routes_to_caution_not_clean():
    r = _rep(selected_claim_ids=("c1", "c2"), selected_claim_texts=("a", "b"),
             provenance_sources=("root", "root"))
    assert r.risk_scores["thin_provenance"] == 0.6
    d = select_mode(r)
    assert d.persistent_state_update_allowed is False        # not treated as clean
    r2 = _rep(provenance_sources=("s1",))                     # single claim, one source -> fine
    assert select_mode(r2).persistent_state_update_allowed is True


# --- scope check ------------------------------------------------------------------------------ #

def test_scope_mismatch_detection():
    assert scope_mismatches("proj-A", ("proj-B",)) == ("proj-B",)
    assert scope_mismatches("proj-A", ("proj-A",)) == ()
    assert scope_mismatches(None, ("proj-B",)) == ()         # no task scope -> no constraint


def test_out_of_scope_claim_routes_to_caution():
    r = _rep(task_scope="proj-A", claim_scopes=("proj-B",))
    assert r.scope_mismatch_scopes == ("proj-B",)
    assert r.risk_scores["scope_mismatch"] == 0.6
    assert select_mode(r).persistent_state_update_allowed is False


def test_in_scope_claim_stays_clean():
    r = _rep(task_scope="proj-A", claim_scopes=("proj-A",))
    assert r.scope_mismatch_scopes == ()
    assert select_mode(r).persistent_state_update_allowed is True


def test_no_inputs_keeps_prior_behaviour():
    r = _rep()
    assert r.risk_scores["thin_provenance"] == 0.0 and r.risk_scores["scope_mismatch"] == 0.0
    assert select_mode(r).persistent_state_update_allowed is True
