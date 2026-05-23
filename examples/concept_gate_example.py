"""Minimal Concept Gate example.

Shows the closed six-condition gate semantics (a phase passes only if
ALL conditions hold) and reads one real per-phase gate.

    python examples/concept_gate_example.py
"""
from __future__ import annotations

from desi.gates.concept_gate import (
    GateCondition, evaluate, failing, passes_all, phase_gate,
)


def main() -> None:
    # A toy gate: all must pass.
    conds = [
        GateCondition("score", 0.91, 0.85, ">=",
                      evaluate(0.91, 0.85, ">=")),
        GateCondition("replay_stability", 1.0, 1.0, "==",
                      evaluate(1.0, 1.0, "==")),
        GateCondition("drift", 0.0, 0.0, "==",
                      evaluate(0.0, 0.0, "==")),
    ]
    print("toy gate passes_all:", passes_all(conds))
    print("toy gate failing:", failing(conds))

    # A real per-phase gate (in-place implementation, not copied).
    real = phase_gate("external_benchmarks")
    print("\nreal external-benchmark gate:")
    for c in real:
        print(f"  [{'PASS' if c.passed else 'FAIL'}] {c.name} "
              f"= {c.value} {c.comparator} {c.threshold}")
    print("real gate passes_all:", passes_all(real))


if __name__ == "__main__":
    main()
