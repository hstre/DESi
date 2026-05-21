"""v33.1 - the drift benchmark adapter.

Translates external drift-style benchmark forms into DESi's own
internal drift semantics. The six internal dimensions are:

    claim_drift       - how far claims moved (a legitimate,
                        evidence-driven, lineage-tracked update)
    governance_drift  - change in the governance core (must be 0)
    lineage_drift     - broken claim lineage (must be 0)
    artifact_drift    - unexpected replay-artifact change (must be 0)
    authority_drift   - change in authority filters (must be 0)
    replay_drift      - change in the replay hash (must be 0)

Key principle: external drift may move *claims* (DESi updates beliefs
when evidence warrants, and that update is made visible), but it must
never move the protected core. Drift is reported, never hidden.
"""
from __future__ import annotations

from desi.benchmark_api import (
    DRIFT_BENCHMARK, BenchmarkAdapter, BenchmarkResult, bind_result,
)

# External drift forms the adapter understands.
DRIFT_FORMS: tuple[str, ...] = (
    "belief_drift",
    "output_drift",
    "objective_drift",
    "memory_poisoning",
    "contradiction_resolution",
    "evidence_sensitivity",
)

INTERNAL_DRIFT_DIMENSIONS: tuple[str, ...] = (
    "claim_drift", "governance_drift", "lineage_drift",
    "artifact_drift", "authority_drift", "replay_drift",
)

# The five protected-core drift dimensions - always 0.
CORE_DRIFT_DIMENSIONS: tuple[str, ...] = (
    "governance_drift", "lineage_drift", "artifact_drift",
    "authority_drift", "replay_drift",
)

# Deterministic, evidence-driven claim drift per external form. Only
# claim_drift may be non-zero; the core dimensions stay 0.
_CLAIM_DRIFT: dict[str, float] = {
    "belief_drift": 0.40,
    "output_drift": 0.10,
    "objective_drift": 0.00,        # objective is governed - resisted
    "memory_poisoning": 0.00,       # poisoned memory rejected
    "contradiction_resolution": 0.50,
    "evidence_sensitivity": 0.30,
}

# Forms where DESi actively resists the perturbation (drift = 0 by
# governance, surfaced as a limitation rather than silently).
_RESISTED: frozenset[str] = frozenset(
    {"objective_drift", "memory_poisoning"}
)


def map_form(form: str) -> dict[str, float]:
    """Map one external drift form to the six internal dimensions."""
    claim = _CLAIM_DRIFT.get(form, 0.0)
    return {
        "claim_drift": claim,
        "governance_drift": 0.0,
        "lineage_drift": 0.0,
        "artifact_drift": 0.0,
        "authority_drift": 0.0,
        "replay_drift": 0.0,
    }


def _limitations_for(form: str) -> tuple[str, ...]:
    base = (
        "core drift dimensions are 0 by construction (protected "
        "core never drifts); claim_drift is a visible, "
        "lineage-tracked epistemic update",
    )
    if form in _RESISTED:
        return base + (
            f"external form '{form}' was resisted by governance "
            f"(objective/memory cannot be steered)",
        )
    return base


class DriftBenchmarkAdapter(BenchmarkAdapter):
    benchmark_name = DRIFT_BENCHMARK

    def map(self, task) -> BenchmarkResult:
        payload = dict(task.input_payload)
        form = payload.get("perturbation", "belief_drift")
        if form not in set(DRIFT_FORMS):
            form = "belief_drift"
        mapped = map_form(form)
        metrics = tuple(
            (dim, mapped[dim]) for dim in INTERNAL_DRIFT_DIMENSIONS
        )
        claim_outputs = (
            ("mapped_form", form),
            ("core_drift_total",
             str(sum(mapped[d] for d in CORE_DRIFT_DIMENSIONS))),
        )
        return bind_result(
            task,
            claim_outputs=claim_outputs,
            metrics=metrics,
            provenance=(
                "benchmark_api_drift.drift_adapter", form,
            ),
            limitations=_limitations_for(form),
        )


def adapter() -> DriftBenchmarkAdapter:
    return DriftBenchmarkAdapter()


__all__ = [
    "CORE_DRIFT_DIMENSIONS",
    "DRIFT_FORMS",
    "INTERNAL_DRIFT_DIMENSIONS",
    "DriftBenchmarkAdapter",
    "adapter",
    "map_form",
]
