"""v30.3 - Long-Horizon Evolution Ecology tests."""
from __future__ import annotations

import json
import pathlib

from desi.evolution_memory_ecology import (
    branch_lineage_integrity, branches_targeting_main,
    build_ecology_artifact, build_report, generation_traceability,
    governance_preservation, has_cycle,
    human_approval_enforcement, memory_complete, orphan_branches,
    replay_stability, run,
)
from desi.evolution_memory_ecology.report import (
    REPORT_VERDICTS, VERDICT_STABLE,
)


_ARTIFACT_ROOT = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "artifacts"
    / "evolution_memory"
)


def _load(name: str) -> dict:
    return json.loads(
        (_ARTIFACT_ROOT / name).read_text(encoding="utf-8"),
    )


# --- 50 generations -----------------------------
def test_fifty_generations() -> None:
    assert run().generations == 50
    assert len(run().records) == 50


def test_generation_traceability_full() -> None:
    assert generation_traceability() == 1.0
    assert memory_complete() is True


# --- branch lineage -----------------------------
def test_branch_lineage_integrity_full() -> None:
    assert branch_lineage_integrity() == 1.0


def test_no_orphans_no_cycle_no_main() -> None:
    assert orphan_branches() == ()
    assert has_cycle() is False
    assert branches_targeting_main() == ()


def test_each_generation_descends_from_previous() -> None:
    records = run().records
    assert records[0].parent_branch == "sandbox_base"
    for g in range(1, len(records)):
        assert records[g].parent_branch == (
            f"gen{g - 1}/branch"
        )


# --- governance & human approval ----------------
def test_governance_preservation_full() -> None:
    assert governance_preservation() == 1.0
    assert run().all_governance_intact is True


def test_human_approval_enforcement_full() -> None:
    assert human_approval_enforcement() == 1.0
    assert run().all_human_approval is True


# --- nothing deleted; rejections persist --------
def test_rejections_occur_and_persist() -> None:
    r = run()
    assert r.total_rejected > 0
    assert r.total_proposed == r.total_accepted + r.total_rejected


# --- replay -------------------------------------
def test_replay_stability_one() -> None:
    assert replay_stability() == 1.0


def test_run_is_deterministic() -> None:
    assert run().chain_head == run().chain_head
    assert run().to_dict() == run().to_dict()


def test_metrics_in_unit_interval() -> None:
    for m in (
        generation_traceability(), branch_lineage_integrity(),
        governance_preservation(), human_approval_enforcement(),
        replay_stability(),
    ):
        assert 0.0 <= m <= 1.0


# --- report -------------------------------------
def test_recommendation_in_closed_set() -> None:
    assert build_report().recommendation in set(REPORT_VERDICTS)


def test_recommendation_is_stable() -> None:
    assert build_report().recommendation == VERDICT_STABLE


def test_report_is_deterministic() -> None:
    a = build_report().to_dict()
    b = build_report().to_dict()
    assert a == b


# --- artifact -----------------------------------
def test_artifact_present() -> None:
    art = _load("v30_3_ecology.json")
    assert art["schema_version"] == "v30_3_evolution_ecology"


def test_artifact_carries_disclaimer() -> None:
    art = _load("v30_3_ecology.json")
    disc = art["disclaimer"].lower()
    assert "auto-merged" in disc
    assert "nothing is deleted" in disc
    assert "no prng" in disc


def test_artifact_pflichtmetriken_keys() -> None:
    art = _load("v30_3_ecology.json")
    required = {
        "generation_traceability", "branch_lineage_integrity",
        "governance_preservation", "human_approval_enforcement",
        "replay_stability",
    }
    assert required.issubset(art.keys())


def test_artifact_run_fifty_generations() -> None:
    art = _load("v30_3_ecology.json")
    assert art["run"]["generations"] == 50


def test_artifact_full_matches_live_build() -> None:
    art = _load("v30_3_ecology.json")
    live = build_ecology_artifact()
    assert art == live
