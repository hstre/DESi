"""Missing-opposition signal: the deterministic plausible-wrong-slice flag + its PWS benchmark."""
from __future__ import annotations

from desi_router.governance import select_mode
from desi_router.governance.benchmark.pws_metrics import evaluate_pws
from desi_router.governance.missing_opposition import omitted_opposition, partition_omitted
from desi_router.governance.report import report_from_snapshot


class _Snap:
    conflicts = ()
    provenance = type("P", (), {"snapshot_hash": "t"})()


def _clean(**extra):
    base = dict(selected_claim_ids=("c1",), selected_claim_texts=("a clean fact",),
                extraction_confidence=0.95, state_recall_estimate=1.0)
    base.update(extra)
    return report_from_snapshot("t", _Snap(), **base)


# --- the pure check --------------------------------------------------------------------------- #

def test_omitted_filters_surfaced_and_dedups():
    assert omitted_opposition(("c1",), ("g1", "g2", "g1")) == ("g1", "g2")
    assert omitted_opposition(("c1", "g1"), ("g1", "g2")) == ("g2",)   # g1 already surfaced
    assert omitted_opposition(("c1",), ()) == ()


def test_partition_keeps_classes():
    p = partition_omitted(("c1",), [("g1", "contested_by"), ("g2", "superseded_by"), ("c1", "x")])
    assert p == {"contested_by": ("g1",), "superseded_by": ("g2",)}


# --- report wiring ---------------------------------------------------------------------------- #

def test_no_scan_means_no_signal_and_prior_risk():
    r = _clean()
    assert r.omitted_opposition_ids == ()
    assert r.risk_scores["missing_opposition"] == 0.0


def test_omitted_opposition_surfaces_on_the_report():
    r = _clean(graph_opposition_ids=("g_obj",), graph_opposition_texts=("a known objection",))
    assert r.omitted_opposition_ids == ("g_obj",)
    assert r.omitted_opposition_texts == ("a known objection",)
    assert r.risk_scores["missing_opposition"] == 1.0


def test_surfaced_opposition_is_not_omitted():
    # the graph opposition is already in the slice -> nothing omitted -> stays clean
    r = report_from_snapshot("t", _Snap(), selected_claim_ids=("c1", "g_obj"),
                             selected_claim_texts=("fact", "the objection, included"),
                             extraction_confidence=0.95, state_recall_estimate=1.0,
                             graph_opposition_ids=("g_obj",))
    assert r.omitted_opposition_ids == ()
    assert r.risk_scores["missing_opposition"] == 0.0


# --- routing ---------------------------------------------------------------------------------- #

def test_plausible_wrong_slice_is_guarded_not_clean():
    r = _clean(graph_opposition_ids=("g_obj",), graph_opposition_texts=("objection",))
    d = select_mode(r)
    assert d.chosen_mode == "guarded_mode"
    assert d.validator_required is True
    assert d.persistent_state_update_allowed is False


def test_true_clean_slice_still_routes_clean():
    d = select_mode(_clean())
    assert d.chosen_mode == "state_slice_mode"
    assert d.persistent_state_update_allowed is True


# --- benchmark: the honest pair --------------------------------------------------------------- #

def test_benchmark_closes_every_subset_without_overblocking():
    blind = evaluate_pws(select_mode, aware=False)
    aware = evaluate_pws(select_mode, aware=True)
    # blind (no scans) lets the opposition + scope traps through as clean
    assert blind["false_clean_by_subset"]["missing_opposition"] == 1.0
    assert blind["false_clean_by_subset"]["scope_match"] == 1.0
    # aware closes all three subsets...
    aw = aware["false_clean_by_subset"]
    assert aw["missing_opposition"] == 0.0
    assert aw["provenance_entropy"] == 0.0
    assert aw["scope_match"] == 0.0
    assert aware["false_clean_rate"] == 0.0
    # ...while NOT escalating a single genuinely-clean control (absence of info is not a flag)
    assert aware["over_caution_rate"] == 0.0
    assert blind["over_caution_rate"] == 0.0
