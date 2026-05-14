"""Tests for v0.9 GenerationMetadata — every instance carries metadata."""
from __future__ import annotations

import pytest

from desi.eval import (
    GenerationMetadata,
    SeededScenarioEngine,
    seed_variant_scenarios,
)


@pytest.fixture
def engine() -> SeededScenarioEngine:
    return SeededScenarioEngine()


# ---------------------------------------------------------------------------
# Metadata is attached to every instance
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("scenario_id",
                         ["ADV_BRANCH_EXPLOSION", "S2", "S6", "S5"])
def test_every_instance_has_generation_metadata(
    engine: SeededScenarioEngine, scenario_id: str,
) -> None:
    inst = engine.instantiate(scenario_id, 42)
    assert inst.generation_metadata is not None
    assert isinstance(inst.generation_metadata, GenerationMetadata)


def test_metadata_seed_matches_request(engine: SeededScenarioEngine) -> None:
    inst = engine.instantiate("ADV_BRANCH_EXPLOSION", 43)
    assert inst.generation_metadata.seed == 43


def test_metadata_scenario_id_matches_request(
    engine: SeededScenarioEngine,
) -> None:
    inst = engine.instantiate("S2", 44)
    assert inst.generation_metadata.scenario_id == "S2"


# ---------------------------------------------------------------------------
# Metadata contents reflect the variant's choices
# ---------------------------------------------------------------------------


def test_adv_branch_explosion_metadata_records_branch_order(
    engine: SeededScenarioEngine,
) -> None:
    inst = engine.instantiate("ADV_BRANCH_EXPLOSION", 42)
    meta = inst.generation_metadata
    assert len(meta.branch_order) >= 3
    # The branch_order entries must match focus_claim_ids in the trajectory.
    focuses = {s.focus_claim_id for s in inst.trajectory.steps
               if s.focus_claim_id is not None}
    for claim_id in meta.branch_order:
        assert claim_id in focuses


def test_s2_metadata_records_contradiction_order(
    engine: SeededScenarioEngine,
) -> None:
    inst = engine.instantiate("S2", 42)
    meta = inst.generation_metadata
    assert len(meta.contradiction_order) == 2
    for pair in meta.contradiction_order:
        assert len(pair) == 2


def test_s6_metadata_records_merge_order(
    engine: SeededScenarioEngine,
) -> None:
    inst = engine.instantiate("S6", 42)
    meta = inst.generation_metadata
    assert len(meta.merge_order) == 2
    assert set(meta.merge_order) == {"C_alpha", "C_alpha_prime"}


# ---------------------------------------------------------------------------
# permutation_id is deterministic and short
# ---------------------------------------------------------------------------


def test_permutation_id_has_perm_prefix(
    engine: SeededScenarioEngine,
) -> None:
    inst = engine.instantiate("ADV_BRANCH_EXPLOSION", 42)
    assert inst.generation_metadata.permutation_id.startswith("perm_")


def test_static_permutation_id_for_non_variant_scenarios(
    engine: SeededScenarioEngine,
) -> None:
    inst = engine.instantiate("S5", 42)
    assert inst.generation_metadata.permutation_id == "static"


# ---------------------------------------------------------------------------
# Export shape
# ---------------------------------------------------------------------------


def test_metadata_to_dict_is_serialisable(engine: SeededScenarioEngine) -> None:
    inst = engine.instantiate("ADV_BRANCH_EXPLOSION", 42)
    d = inst.generation_metadata.to_dict()
    for k in ("seed", "permutation_id", "scenario_id",
              "noise_claims", "branch_order",
              "contradiction_order", "merge_order"):
        assert k in d
    assert d["seed"] == 42
    assert d["scenario_id"] == "ADV_BRANCH_EXPLOSION"
