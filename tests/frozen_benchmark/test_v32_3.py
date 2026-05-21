"""v32.3 - Evolution Utility Analysis tests."""
from __future__ import annotations

import json
import pathlib

from desi.frozen_benchmark_utility import (
    baseline_novelty_per_runtime, build_report,
    build_utility_artifact, distinct_outputs, evolution_features,
    evolution_utility, feature_efficiency, local_attractors,
    memory_utility, novelty_per_runtime, novelty_per_runtime_gain,
    overengineered_features, overengineering_detection,
    replay_stability,
)
from desi.frozen_benchmark_utility.report import (
    REPORT_VERDICTS, VERDICT_MIXED,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "frozen_benchmark"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- real measured utility ----------------------
def test_evolution_utility_positive() -> None:
    assert evolution_utility() > 0.0


def test_five_evolution_features() -> None:
    names = {f.name for f in evolution_features()}
    assert names == {
        "replay_cache", "evolution_ecology", "mutation_memory",
        "neo4j_evolution_graph", "wild_brother",
    }


def test_memory_utility_is_epistemic() -> None:
    assert memory_utility() == 1.0


# --- novelty per runtime ------------------------
def test_novelty_per_runtime_improved() -> None:
    assert novelty_per_runtime() > baseline_novelty_per_runtime()
    assert novelty_per_runtime_gain() > 0.0


def test_distinct_outputs_count() -> None:
    assert distinct_outputs() == 4


# --- overengineering detection ------------------
def test_overengineering_detection_full() -> None:
    assert overengineering_detection() == 1.0


def test_local_attractor_flagged() -> None:
    # the neo4j projection layer adds complexity without a measured
    # runtime benefit - an honest local attractor
    assert "neo4j_evolution_graph" in overengineered_features()
    assert local_attractors() == overengineered_features()


def test_useful_features_not_flagged() -> None:
    flagged = set(overengineered_features())
    assert "replay_cache" not in flagged
    assert "evolution_ecology" not in flagged
    assert "mutation_memory" not in flagged


def test_feature_efficiency_signs() -> None:
    eff = feature_efficiency()
    assert eff["replay_cache"] > 0.0
    assert eff["neo4j_evolution_graph"] < 0.0


# --- governance / replay ------------------------
def test_governance_identity_full() -> None:
    assert build_report().governance_identity == 1.0


def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_metrics_in_unit_interval() -> None:
    for m in (
        evolution_utility(), novelty_per_runtime(),
        overengineering_detection(), replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_mixed() -> None:
    # real utility, but one local attractor was honestly flagged
    assert build_report().recommendation == VERDICT_MIXED


def test_report_not_halt() -> None:
    assert build_report().halt is False


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v32_3_utility.json")
    assert art["schema_version"] == "v32_3_evolution_utility"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v32_3_utility.json")
    disc = art["disclaimer"].lower()
    assert "real, measured" in disc
    assert "not projected" in disc
    assert "local attractors" in disc


def test_artifact_lists_attractors() -> None:
    art = _load("v32_3_utility.json")
    assert "neo4j_evolution_graph" in art["local_attractors"]
    assert len(art["features"]) == 5


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v32_3_utility.json")
    required = {
        "evolution_utility", "novelty_per_runtime",
        "overengineering_detection", "governance_identity",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_full_matches_live_build() -> None:
    art = _load("v32_3_utility.json")
    live = build_utility_artifact()
    assert art == live
