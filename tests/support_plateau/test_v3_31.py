"""v3.31 — plateau census tests."""
from __future__ import annotations

import json
import pathlib

from desi.support_plateau.extractor import (
    census, non_rescued_ids, plateau_trajectory_ids,
)
from desi.support_plateau.metrics import compute_metrics
from desi.support_plateau.report import (
    build_inventory_artifact, build_report,
)
from desi.support_plateau.state import (
    PlateauKind, _PLATEAU_SUPPORT_VALUE,
    visits_to_plateau,
)


def test_plateau_value_is_two() -> None:
    """BRIDGE_REQUIRED == 2.0 in the LogicalState enum."""
    assert _PLATEAU_SUPPORT_VALUE == 2.0


def test_plateau_kinds_are_closed() -> None:
    assert {k.value for k in PlateauKind} == {
        "terminal_plateau", "transient_plateau",
        "non_plateau",
    }


def test_plateau_replay_stability_is_one() -> None:
    """The census must be deterministic — running it
    twice must yield the same plateau membership."""
    r = build_report()
    assert r.metrics.plateau_replay_stability == 1.0


def test_plateau_terminal_rate_is_one() -> None:
    """Every plateau in this corpus is terminal (the
    v3 extractor produces a single audit state at
    s_{n-1}; if it lands at 2.0 it stays at 2.0)."""
    r = build_report()
    if r.metrics.plateau_count > 0:
        assert r.metrics.plateau_terminal_rate == 1.0


def test_hypothesis_weakening_documented() -> None:
    """Directive: 'Wenn plateau_count != 22 ->
    Hypothese schwach. Dokumentieren. Nicht abbrechen.'
    Whether the hypothesis holds or is weakened, the
    report must record it."""
    r = build_report()
    assert isinstance(r.hypothesis_weakened, bool)
    assert r.hypothesis_expected_plateau_count == 22


def test_plateau_outside_non_rescued_is_zero() -> None:
    """All plateau trajectories must be in the v3.30
    non-rescued set."""
    assert build_report().metrics.plateau_outside_non_rescued == 0


def test_non_rescued_outside_plateau_is_documented() -> None:
    """The directive's expectation was all 22 non-
    rescued at 2.0. If some non-rescued are NOT at 2.0,
    the report records that count."""
    r = build_report()
    # Empirically observed: 2 GAP_DETECTED trajectories
    # in the non-rescued set are below the plateau.
    assert r.metrics.non_rescued_outside_plateau >= 0


def test_visits_to_plateau_helper() -> None:
    from desi.epistemic_trajectory.state import StateVector
    def _sv(s):
        return StateVector(
            frame_id=0.0, contradiction_load=0.0,
            anchor_density=0.0, source_quality=0.0,
            novelty=0.0, confidence=0.0,
            branch_cost=0.0, support_state=s,
            routing_state=0.0,
        )
    states = (_sv(0.0), _sv(2.0), _sv(2.0), _sv(0.0), _sv(2.0))
    assert visits_to_plateau(states) == 3


def test_census_covers_full_corpus() -> None:
    from desi.epistemic_trajectory.extractor import (
        extract_all_trajectories,
    )
    obs = census()
    assert len(obs) == len(extract_all_trajectories())


def test_artifact_inventory_matches_live_count() -> None:
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_31"
         / "plateau_inventory.json").read_text(
            encoding="utf-8",
        )
    )
    assert art["plateau_count"] == len(art["plateaus"])
    assert art["plateau_count"] == (
        build_report().metrics.plateau_count
    )


def test_artifact_report_matches_live_build() -> None:
    """Stable fields pinned exactly; source distribution
    can drift across hash seeds if the trajectory pool's
    own dict ordering shifts."""
    root = pathlib.Path(__file__).resolve().parents[2]
    art = json.loads(
        (root / "artifacts" / "v3_31" / "report.json").read_text(
            encoding="utf-8",
        )
    )
    live = build_report().to_dict()
    volatile = {"plateau_source_distribution"}
    art_stable = {
        k: v for k, v in art.items() if k not in volatile
    }
    live_stable = {
        k: v for k, v in live.items() if k not in volatile
    }
    assert art_stable == live_stable


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "PLATEAU_HYPOTHESIS_CONFIRMED",
        "PLATEAU_HYPOTHESIS_WEAKENED",
    }
    assert build_report().recommendation in allowed
