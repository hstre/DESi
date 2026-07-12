"""CLSP wired into the governance gate: CLSP -> EIR (report) -> select_mode, end to end.

Proves the cross-lingual findings flow through the SAME deterministic gate as any other claim, with
the lead-language rule preserved: anchored invariant claims are trusted, weakly-anchored (emergent)
ones force a verifier, and probe-only claims never become trusted state.
"""
from __future__ import annotations

from desi_router.governance import clsp, report_from_snapshot, select_mode
from desi_router.governance.clsp import Cluster


class _Snap:
    conflicts = ()
    provenance = type("P", (), {"snapshot_hash": "clsp"})()


def _decide(clusters):
    rep = report_from_snapshot("t", _Snap(), **clsp.to_report_inputs(clusters))
    return rep, select_mode(rep, retrieval_available=True)


def test_invariant_core_slice_is_trusted_and_may_update():
    rep, d = _decide([
        Cluster("anchored A", ("de", "en"), clsp.STRONG, original_span="verankert a"),
        Cluster("anchored B", ("de", "en", "fr"), clsp.STRONG, original_span="verankert b"),
    ])
    assert rep.selected_claim_ids and rep.has_usable_state
    assert d.chosen_mode == "state_slice_mode"
    assert d.persistent_state_update_allowed is True


def test_emergent_candidate_forces_a_verifier_no_update():
    _, d = _decide([
        Cluster("anchored", ("de", "en"), clsp.STRONG, original_span="verankert"),
        Cluster("weakly anchored, emergent", ("en", "fr"), clsp.WEAK),   # needs verification
    ])
    assert d.validator_required is True
    assert d.persistent_state_update_allowed is False


def test_probe_only_never_becomes_trusted_state():
    # nothing anchorable in the lead source -> no selected claims -> no usable state to answer from
    rep, d = _decide([
        Cluster("moral reading", ("fr",), clsp.NONE),
        Cluster("artefact", ("en",), clsp.WEAK, original_span="könnte sein",
                projected_claim="this proves it"),   # over-amplification -> rejected
    ])
    assert rep.selected_claim_ids == ()
    assert rep.has_usable_state is False
    assert d.chosen_mode == "retrieval_mode"          # must look it up, not trust a probe-only claim


def test_bridge_excludes_held_clusters_from_the_slice():
    clusters = [
        Cluster("keep", ("de", "en"), clsp.STRONG, original_span="behalten"),
        Cluster("drop probe-only", ("fr",), clsp.NONE),
    ]
    inp = clsp.to_report_inputs(clusters)
    assert inp["selected_claim_texts"] == ("keep",)   # only the anchored one enters EIR
