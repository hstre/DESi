"""Aufgaben 3 + 4 — corpus + simulator."""
from __future__ import annotations

from desi.gate_ablation import (
    ALL_NCS,
    Gate,
    all_chains,
    ablated_gates,
    run_ablation,
    run_baseline,
    transitions_per_chain,
)


def test_chain_count_meets_minimum() -> None:
    chains = all_chains()
    assert len(chains) + len(ALL_NCS) >= 600


def test_attack_count_meets_minimum() -> None:
    attacks = sum(1 for c in all_chains() if c.is_attack)
    assert attacks >= 100


def test_transition_count_meets_minimum() -> None:
    total = (len(all_chains()) + len(ALL_NCS)) * transitions_per_chain()
    assert total >= 2500


def test_seven_gates_under_test() -> None:
    assert len(ablated_gates()) == 7
    assert set(ablated_gates()) == {
        Gate.G1_PREMISE_EXTRACTOR,
        Gate.G2_SPL,
        Gate.G3_FRAME_DECLARATION,
        Gate.G4_FRAME_TENSION,
        Gate.G5_ROUTER,
        Gate.G6_CAUSAL_CHAIN,
        Gate.G7_SUSPENSION_GATE,
    }


def test_baseline_emits_one_outcome_per_chain() -> None:
    chains = all_chains()
    metrics, outs = run_baseline(chains)
    assert len(outs) == len(chains)
    assert metrics.gate == "BASELINE"


def test_ablation_deterministic_per_gate() -> None:
    chains = all_chains()
    _, baselines = run_baseline(chains)
    a = run_ablation(Gate.G4_FRAME_TENSION, chains, baselines)
    b = run_ablation(Gate.G4_FRAME_TENSION, chains, baselines)
    assert a.to_dict() == b.to_dict()
