"""v11.1 - DESi-guided search tests."""
from __future__ import annotations

import json
import pathlib

from desi.desi_guided_search.governance import (
    GOVERNANCE_ACTIONS, GovernanceAction,
    action_counts, governed_branches,
)
from desi.desi_guided_search.prioritization import (
    priority_order, pv_stability,
)
from desi.desi_guided_search.report import (
    build_guided_search_artifact, build_report,
)
from desi.desi_guided_search.search_budget import (
    baseline_node_count, compute_saving,
    guided_node_count, node_reduction,
    tactical_recall,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "chess_governance"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_governance_actions_closed_set() -> None:
    assert GOVERNANCE_ACTIONS == tuple(
        a.value for a in GovernanceAction
    )
    assert len(GOVERNANCE_ACTIONS) == 3


def test_node_reduction_meets_gate() -> None:
    """Pflichtfrage 1: wie viele Nodes spart
    DESi? Concept Gate floor: >= 0.50."""
    assert node_reduction() >= 0.50


def test_tactical_recall_full() -> None:
    """Pflichtfrage 2: bleibt taktischer Recall
    erhalten? Every critical-tactic branch must
    be SEARCHed, never REPLAYed or SKIPped."""
    assert tactical_recall() == 1.0


def test_no_critical_branch_skipped_or_replayed() -> (
    None
):
    """Stronger invariant: every is_critical_
    truth branch has action == SEARCH."""
    for g in governed_branches():
        if g.is_critical_truth:
            assert g.action == (
                GovernanceAction.SEARCH.value
            )


def test_pv_stability_full() -> None:
    """Pflichtfrage 3: bleibt die Principal
    Variation stabil? PV branch must rank
    first in every position."""
    assert pv_stability() == 1.0


def test_compute_saving_meets_gate() -> None:
    """Pflichtfrage 4: wie stark sinkt
    Suchaufwand?"""
    assert compute_saving() >= 0.50


def test_baseline_vs_guided_consistent() -> None:
    """node_reduction = 1 - guided/baseline."""
    base = baseline_node_count()
    guided = guided_node_count()
    expected = 1.0 - (guided / base)
    assert abs(
        node_reduction() - expected,
    ) < 1e-6


def test_action_counts_consistent() -> None:
    counts = action_counts()
    assert sum(counts.values()) == len(
        governed_branches(),
    )


def test_priority_order_first_is_pv() -> None:
    """In every position, the first ranked
    branch is the PV branch."""
    from desi.chess_governance.positions import (
        fixture,
    )
    first_in: dict[str, str] = {}
    for pos_id, bid in priority_order():
        if pos_id not in first_in:
            first_in[pos_id] = bid
    for p in fixture():
        assert first_in[
            p.position_id
        ] == p.pv_branch_id


def test_skip_action_is_zero_cost_basis() -> None:
    """Sanity: every governed branch with action
    SKIP must NOT be critical (otherwise
    tactical_recall would fail)."""
    for g in governed_branches():
        if g.action == (
            GovernanceAction.SKIP.value
        ):
            assert not g.is_critical_truth


def test_replay_stability_one() -> None:
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "GUIDED_COMPRESSED",
        "GUIDED_TACTICAL_LEAK",
        "GUIDED_PV_DISPLACED",
        "GUIDED_NEGLIGIBLE_SAVING",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_compressed() -> None:
    """Killerfrage: kann DESi Suchkosten
    reduzieren ohne relevante Varianten zu
    verlieren?"""
    assert build_report().recommendation == (
        "GUIDED_COMPRESSED"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v11_1_guided_search.json")
    assert art["schema_version"] == (
        "v11_1_desi_guided_search"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v11_1_guided_search.json")
    required = {
        "node_reduction", "tactical_recall",
        "pv_stability", "compute_saving",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v11_1_report.json")
    live = build_report().to_dict()
    volatile = {"rationale"}
    art_stable = {
        k: v for k, v in art.items()
        if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items()
        if k not in volatile
    }
    assert art_stable == live_stable


def test_artifact_full_matches_live_build() -> None:
    art = _load("v11_1_guided_search.json")
    live = build_guided_search_artifact()
    assert art == live
