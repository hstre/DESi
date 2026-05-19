"""v15.3 - Audit Search Compression tests."""
from __future__ import annotations

import inspect
import json
import pathlib

from desi.financial_governance import (
    AUDIT_PRIORITIES, AuditPriority,
)
from desi.financial_audit_compression import (
    audit_search_reduction, audit_universe,
    build_compression_artifact, build_report,
    cost_reduction_proxy, critical_cells,
    critical_signal_preservation,
    ex_ante_critical_preservation,
    false_suppression_rate, selected_cells,
    suppressed_critical, universe_size,
)
from desi.financial_audit_compression import (
    audit_priority, compression,
    exploration_budget, report, risk_ranking,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "financial_governance"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


# --- gate-relevant compression properties -------
def test_search_reduction_meets_floor() -> None:
    assert audit_search_reduction() >= 0.30


def test_critical_preservation_meets_floor() -> None:
    assert critical_signal_preservation() >= 0.95


def test_false_suppression_under_ceiling() -> None:
    assert false_suppression_rate() <= 0.05


def test_no_critical_signal_suppressed() -> None:
    assert suppressed_critical() == ()


def test_cost_proxy_in_unit_interval() -> None:
    assert 0.0 <= cost_reduction_proxy() <= 1.0


def test_audited_fewer_than_universe() -> None:
    assert len(selected_cells()) < universe_size()


def test_critical_cells_present() -> None:
    assert len(critical_cells()) > 0


def test_all_critical_cells_selected_top() -> None:
    """Every critical cell should sit among the
    audited (top-priority) cells - that is what
    preservation = 1.0 means structurally."""
    sel = {
        (r.firm_id, r.axis) for r in selected_cells()
    }
    for c in critical_cells():
        assert (c.firm_id, c.axis) in sel


# --- ex-ante validation -------------------------
def test_ex_ante_critical_preservation_full() -> None:
    assert ex_ante_critical_preservation() == 1.0


# --- post-hoc isolation invariant ---------------
def test_scoring_modules_never_read_post_hoc() -> None:
    """CRITICAL: the compression machinery must
    never read ``.post_hoc_label``; only the
    ex-ante validator in report.py may."""
    for mod in (
        audit_priority, risk_ranking,
        exploration_budget, compression,
    ):
        src = inspect.getsource(mod)
        assert ".post_hoc_label" not in src, (
            mod.__name__
        )
    # In report.py only ex_ante_critical_preservation
    # (via _adverse_firm_ids) may consult post-hoc.
    safe_fns = (
        report.build_report,
        report._compression_is_safe,
    )
    for fn in safe_fns:
        src = inspect.getsource(fn)
        assert ".post_hoc_label" not in src, (
            fn.__name__
        )


# --- replay / determinism / recommendation ------
def test_replay_stability_one() -> None:
    assert build_report().replay_stability == 1.0


def test_recommendation_in_closed_set() -> None:
    assert (
        build_report().recommendation
        in set(AUDIT_PRIORITIES)
    )


def test_recommendation_not_unresolved_when_safe() -> None:
    """Compression is safe here, so the verdict
    should be a real audit priority, not the
    UNRESOLVED hand-off."""
    r = build_report()
    assert r.halt is False
    assert r.recommendation != (
        AuditPriority.UNRESOLVED.value
    )


def test_recommendation_never_says_fraud() -> None:
    rec = build_report().recommendation.lower()
    for word in ("fraud", "betrug", "buy", "sell"):
        assert word not in rec


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v15_3_compression.json")
    assert art["schema_version"] == (
        "v15_3_audit_search_compression"
    )


def test_artifact_carries_disclaimer() -> None:
    art = _load("v15_3_compression.json")
    disc = art["disclaimer"].lower()
    assert "synthetic" in disc
    assert "does not conclude fraud" in disc
    assert "never drops a critical signal" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v15_3_compression.json")
    required = {
        "audit_search_reduction",
        "critical_signal_preservation",
        "false_suppression_rate",
        "cost_reduction_proxy",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v15_3_compression.json")
    live = build_compression_artifact()
    assert art == live
