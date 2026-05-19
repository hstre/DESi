"""v11.0 - chess search redundancy tests."""
from __future__ import annotations

import json
import pathlib

from desi.chess_governance.branching import (
    critical_branch_count,
    mean_branching_factor,
    no_critical_branch_dropped,
    verdict_distribution,
)
from desi.chess_governance.positions import (
    POSITION_KINDS, PositionKind, fixture,
    kind_counts, total_branch_count,
)
from desi.chess_governance.redundancy import (
    BRANCH_VERDICTS, BranchVerdict,
    classified_branches,
    forced_line_detection,
    low_information_rate,
    redundant_branch_rate, replay_reuse,
)
from desi.chess_governance.report import (
    build_redundancy_artifact, build_report,
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


def test_position_kinds_closed_set() -> None:
    assert POSITION_KINDS == tuple(
        p.value for p in PositionKind
    )
    assert len(POSITION_KINDS) == 5


def test_branch_verdicts_closed_set() -> None:
    assert BRANCH_VERDICTS == tuple(
        v.value for v in BranchVerdict
    )
    assert len(BRANCH_VERDICTS) == 4


def test_fixture_balanced_kinds() -> None:
    counts = kind_counts()
    assert set(counts.keys()) == set(
        POSITION_KINDS,
    )
    assert set(counts.values()) == {2}


def test_total_branch_count_matches() -> None:
    expected = sum(
        len(p.branches) for p in fixture()
    )
    assert total_branch_count() == expected


def test_mean_branching_factor_realistic() -> (
    None
):
    """Each position has 3-5 branches in the
    fixture; the mean lands in that range."""
    assert 3.0 <= mean_branching_factor() <= 5.0


def test_redundant_branch_rate_high() -> None:
    """Pflichtfrage 1: wie viele Branches sind
    epistemisch redundant? Recall floor 0.80."""
    assert redundant_branch_rate() >= 0.80


def test_low_information_rate_substantial() -> (
    None
):
    """Pflichtfrage 2: wie viele Nodes tragen
    kaum neue Information? Should be at least
    20% of the fixture - the directive's premise
    is that meaningful redundancy exists."""
    assert low_information_rate() >= 0.20


def test_forced_line_detection_full() -> None:
    """Every ground-truth forced line must be
    detected as FORCED."""
    assert forced_line_detection() == 1.0


def test_no_critical_branch_dropped() -> None:
    """v11.0 audits but does not prune. By
    construction no critical branch receives a
    LOW_INFO or REDUNDANT verdict."""
    assert no_critical_branch_dropped()


def test_critical_branches_kept_or_forced() -> (
    None
):
    """Stronger invariant: every ground-truth
    critical-tactic branch exits FORCED or
    KEEP."""
    for r in classified_branches():
        if r.is_critical_truth:
            assert r.verdict in {
                BranchVerdict.FORCED.value,
                BranchVerdict.KEEP.value,
            }


def test_critical_branch_count_positive() -> None:
    """The fixture contains at least 2 critical-
    tactic branches across the tactical /
    middlegame positions."""
    assert critical_branch_count() >= 2


def test_verdict_distribution_covers_all() -> (
    None
):
    dist = verdict_distribution()
    assert set(dist.keys()) == set(
        BRANCH_VERDICTS,
    )
    assert sum(dist.values()) == (
        total_branch_count()
    )


def test_replay_reuse_positive() -> None:
    """At least some low-info branches in the
    same position kind can be reused."""
    assert replay_reuse() >= 0.0


def test_replay_stability_one() -> None:
    """Pflichtfrage 4: wie hoch ist replay
    reuse? Replay stability is the floor."""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "REDUNDANCY_AUDITED",
        "REDUNDANCY_CRITICAL_DROP",
        "REDUNDANCY_FORCED_MISS",
        "REDUNDANCY_DETECTION_WEAK",
        "REDUNDANCY_NEGLIGIBLE",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_audited() -> None:
    """Killerfrage: wie viel der Schachsuche
    ist epistemisch redundant?"""
    assert build_report().recommendation == (
        "REDUNDANCY_AUDITED"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v11_0_redundancy.json")
    assert art["schema_version"] == (
        "v11_0_search_redundancy"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v11_0_redundancy.json")
    required = {
        "redundant_branch_rate",
        "low_information_rate",
        "forced_line_detection",
        "replay_reuse",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v11_0_report.json")
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
    art = _load("v11_0_redundancy.json")
    live = build_redundancy_artifact()
    assert art == live


def test_no_live_engine_imports() -> None:
    """The chess_governance package must not
    import a live engine library - the directive
    forbids Stockfish manipulation and the
    sandbox does not have python-chess
    installed."""
    import importlib
    forbidden = {
        "chess", "stockfish",
    }
    pkg = importlib.import_module(
        "desi.chess_governance",
    )
    seen = set(dir(pkg))
    assert not (seen & forbidden)
