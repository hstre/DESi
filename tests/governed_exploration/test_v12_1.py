"""v12.1 - governed exploration tests."""
from __future__ import annotations

import json
import pathlib

from desi.governed_exploration.blindness import (
    blindness_share, covered_share, total_cells,
)
from desi.governed_exploration.compression import (
    compressed_groups, compression_count,
    redundancy_reduction,
)
from desi.governed_exploration.recoverability import (
    recoverability_index, recoverable_share,
)
from desi.governed_exploration.report import (
    build_governed_exploration_artifact,
    build_report,
)
from desi.governed_exploration.risk_control import (
    hallucination_containment,
    innovation_preservation, mean_risk,
    search_governance,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "open_math"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(
            encoding="utf-8",
        ),
    )


def test_redundancy_reduction_positive() -> None:
    """Pflichtfrage 1: wie stark sinkt
    Exploration Redundancy?"""
    assert redundancy_reduction() >= 0.30


def test_hallucination_containment_full() -> (
    None
):
    """Pflichtfrage 2: wie viele
    Halluzinationspfade werden gestoppt?"""
    assert hallucination_containment() == 1.0


def test_innovation_preservation_high() -> None:
    """Pflichtfrage 3 / 5: bleibt Innovation
    erhalten?"""
    assert innovation_preservation() >= 0.70


def test_search_governance_high() -> None:
    """Pflichtfrage 4: wie stark sinkt
    Suchchaos?"""
    assert search_governance() >= 0.95


def test_compression_groups_consistent() -> None:
    """Every governed hypothesis lands in
    exactly one group."""
    members: list[str] = []
    for _, ids in compressed_groups():
        members.extend(ids)
    assert len(members) == len(set(members))


def test_compression_count_positive() -> None:
    assert compression_count() >= 1


def test_recoverability_in_range() -> None:
    ri = recoverability_index()
    assert 0.0 <= ri <= 1.0


def test_recoverable_share_in_range() -> None:
    rs = recoverable_share()
    assert 0.0 <= rs <= 1.0


def test_blindness_share_in_range() -> None:
    bs = blindness_share()
    assert 0.0 <= bs <= 1.0


def test_covered_plus_blindness_one() -> None:
    assert abs(
        covered_share() + blindness_share()
        - 1.0,
    ) < 1e-6


def test_total_cells_closed_set() -> None:
    """6 statuses x 6 shapes = 36 cells."""
    assert total_cells() == 36


def test_mean_risk_in_range() -> None:
    mr = mean_risk()
    assert 0.0 <= mr <= 1.0


def test_replay_stability_one() -> None:
    assert build_report().replay_stability == (
        1.0
    )


def test_recommendation_in_closed_set() -> None:
    allowed = {
        "GOVERNED_BALANCED",
        "GOVERNED_HALLUCINATION_LEAK",
        "GOVERNED_GOVERNANCE_BREACH",
        "GOVERNED_OVER_PRUNED",
        "GOVERNED_NEGLIGIBLE_COMPRESSION",
        "HALT_REPLAY_DRIFT",
    }
    assert build_report().recommendation in (
        allowed
    )


def test_recommendation_is_balanced() -> None:
    """Killerfrage: kann DESi Kreativitaet
    domestizieren ohne sie zu zerstoeren?"""
    assert build_report().recommendation == (
        "GOVERNED_BALANCED"
    )


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


def test_artifact_present() -> None:
    art = _load(
        "v12_1_governed_exploration.json",
    )
    assert art["schema_version"] == (
        "v12_1_governed_exploration"
    )


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load(
        "v12_1_governed_exploration.json",
    )
    required = {
        "redundancy_reduction",
        "hallucination_containment",
        "innovation_preservation",
        "search_governance",
    }
    assert required.issubset(art.keys())


def test_artifact_report_matches_live_build() -> (
    None
):
    art = _load("v12_1_report.json")
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
    art = _load(
        "v12_1_governed_exploration.json",
    )
    live = (
        build_governed_exploration_artifact()
    )
    assert art == live
