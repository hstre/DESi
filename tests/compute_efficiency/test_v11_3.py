"""v11.3 - compute efficiency tests."""
from __future__ import annotations

import json
import pathlib

from desi.compute_efficiency.compression import (
    per_position_compression,
)
from desi.compute_efficiency.costs import (
    baseline_energy, baseline_time_ms,
    guided_energy, guided_time_ms,
)
from desi.compute_efficiency.efficiency import (
    branch_compression, compute_reduction,
    elo_delta_proxy, quality_preservation,
)
from desi.compute_efficiency.report import (
    build_efficiency_artifact, build_report,
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


def test_compute_reduction_meets_gate() -> None:
    """Pflichtfrage 1: wie viel Compute spart
    DESi?"""
    assert compute_reduction() >= 0.50


def test_quality_preservation_full() -> None:
    """Pflichtfrage 3: bleibt Spielstaerke
    erhalten?"""
    assert quality_preservation() >= 0.95


def test_elo_delta_proxy_bounded() -> None:
    """The directive's gate is implicit: a
    significant Elo regression would mean DESi
    lost playing strength. Floor at -50."""
    assert elo_delta_proxy() >= -50.0


def test_elo_delta_proxy_actually_zero() -> None:
    """With tactical_miss_rate == 0 the proxy
    is exactly 0."""
    assert elo_delta_proxy() == 0.0


def test_branch_compression_meets_gate() -> None:
    """Pflichtfrage 2: wie stark sinken
    Suchkosten?"""
    assert branch_compression() >= 0.50


def test_time_consistent_with_nodes() -> None:
    """time_ms = nodes * 1 ms in the synthetic
    cost model."""
    assert baseline_time_ms() == (
        4300.0
    )
    assert guided_time_ms() == 2010.0


def test_energy_lower_under_governance() -> None:
    """Energy MUST drop under DESi - SKIP costs
    zero and REPLAY only 30% of full energy."""
    assert guided_energy() < baseline_energy()


def test_per_position_compression_covers_all() -> (
    None
):
    from desi.chess_governance.positions import (
        fixture,
    )
    comp = per_position_compression()
    assert set(comp.keys()) == {
        p.position_id for p in fixture()
    }


def test_replay_stability_one() -> None:
    """Pflichtfrage 4: wie hoch ist
    Compute-vs-Quality?"""
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "EFFICIENCY_COMPRESSED",
        "EFFICIENCY_QUALITY_LOSS",
        "EFFICIENCY_ELO_REGRESSION",
        "EFFICIENCY_NEGLIGIBLE",
        "EFFICIENCY_LOW_COMPRESSION",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_compressed() -> None:
    """Killerfrage: erzeugt DESi echte
    epistemische Suchkompression?"""
    assert build_report().recommendation == (
        "EFFICIENCY_COMPRESSED"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load("v11_3_efficiency.json")
    assert art["schema_version"] == (
        "v11_3_compute_efficiency"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v11_3_efficiency.json")
    required = {
        "compute_reduction",
        "elo_delta_proxy",
        "quality_preservation",
        "branch_compression",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v11_3_report.json")
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
    art = _load("v11_3_efficiency.json")
    live = build_efficiency_artifact()
    assert art == live
