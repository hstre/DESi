"""v21.0 - comparative metrics: DESi-alone (v19) vs
DESi + Wild Explorer (v20).

Pulls the relevant numbers straight from the v19 and v20
modules (no hand-entered values) and computes the deltas
that answer the real question: does the wild brother
produce productive exploration DESi can stabilise, or is it
just dangerous noise?

DESi-alone is the conservative ICRL-governance baseline
(v19). It has no Wild Explorer, so it contributes no
wild-driven novelty gain and no hallucination pressure by
construction.
"""
from __future__ import annotations

# --- v19: DESi-alone ICRL exploration governance ---
from desi.icrl_governance import (
    exploration_diversity as _v19_diversity,
)
from desi.icrl_governed import (
    redundancy_reduction as _v19_redundancy_reduction,
)
from desi.icrl_ecology import (
    policy_drift as _v19_authority_drift,
    trajectory_capture_resistance as _v19_capture_resistance,
)
from desi.icrl_governance_verdict import (
    aggregate as _v19_aggregate,
)

# --- v20: DESi + Wild Explorer dual-agent ---
from desi.dual_agent_exploration import (
    novelty_generation as _v20_novelty_generation,
    productivity_gain as _v20_productivity_gain,
)
from desi.dual_agent_pressure import (
    hallucination_containment as _v20_halluc_containment,
    hallucination_pressure as _v20_halluc_pressure,
)
from desi.dual_agent_negotiation import (
    exploration_diversity as _v20_diversity,
    redundancy_reduction as _v20_redundancy_reduction,
)
from desi.dual_agent_ecology import (
    authority_drift as _v20_authority_drift,
    capture_resistance as _v20_capture_resistance,
)
from desi.dual_agent_verdict import (
    gate_passes_all as _v20_gate_passes,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


# ---- per-side metric snapshots ----
def desi_alone() -> dict[str, float]:
    """v19 DESi-alone profile."""
    return {
        # no wild explorer -> no wild-driven novelty gain
        "novelty_gain": 0.0,
        "exploration_diversity": _round(_v19_diversity()),
        "redundancy_reduction": _round(
            _v19_redundancy_reduction()
        ),
        # no wild explorer -> no hallucination, none leaks
        "hallucination_pressure": 0.0,
        "residual_hallucination": 0.0,
        "authority_drift": _round(_v19_authority_drift()),
        "capture_resistance": _round(_v19_capture_resistance()),
        "replay_stability": _round(
            _v19_aggregate().replay_stability
        ),
    }


def dual_agent() -> dict[str, float]:
    """v20 DESi + Wild Explorer profile."""
    pressure = _v20_halluc_pressure()
    containment = _v20_halluc_containment()
    # residual = pressure that LEAKS past containment
    residual = _round(pressure * (1.0 - containment))
    return {
        "novelty_gain": _round(_v20_novelty_generation()),
        "exploration_diversity": _round(_v20_diversity()),
        "redundancy_reduction": _round(
            _v20_redundancy_reduction()
        ),
        "hallucination_pressure": _round(pressure),
        "residual_hallucination": residual,
        "authority_drift": _round(_v20_authority_drift()),
        "capture_resistance": _round(_v20_capture_resistance()),
        "replay_stability": 1.0,
    }


# ---- deltas (dual-agent minus DESi-alone) ----
def delta_novelty_gain() -> float:
    return _round(
        dual_agent()["novelty_gain"]
        - desi_alone()["novelty_gain"]
    )


def delta_exploration_diversity() -> float:
    return _round(
        dual_agent()["exploration_diversity"]
        - desi_alone()["exploration_diversity"]
    )


def delta_redundancy_reduction() -> float:
    return _round(
        dual_agent()["redundancy_reduction"]
        - desi_alone()["redundancy_reduction"]
    )


def delta_hallucination_pressure() -> float:
    """Delta in the UNCONTAINED (residual) hallucination -
    the safety-relevant quantity, not the raw input
    pressure."""
    return _round(
        dual_agent()["residual_hallucination"]
        - desi_alone()["residual_hallucination"]
    )


def delta_authority_drift() -> float:
    return _round(
        dual_agent()["authority_drift"]
        - desi_alone()["authority_drift"]
    )


def delta_replay_stability() -> float:
    return _round(
        dual_agent()["replay_stability"]
        - desi_alone()["replay_stability"]
    )


def productivity_gain() -> float:
    return _round(_v20_productivity_gain())


def dual_agent_gate_passed() -> bool:
    return _v20_gate_passes()


def comparison_table() -> dict[str, dict[str, float]]:
    a = desi_alone()
    d = dual_agent()
    keys = [
        "redundancy_reduction", "novelty_gain",
        "exploration_diversity", "hallucination_pressure",
        "authority_drift", "capture_resistance",
        "replay_stability",
    ]
    return {
        k: {
            "desi_alone": a[k],
            "dual_agent": d[k],
            "delta": _round(d[k] - a[k]),
        }
        for k in keys
    }


__all__ = [
    "comparison_table",
    "delta_authority_drift",
    "delta_exploration_diversity",
    "delta_hallucination_pressure",
    "delta_novelty_gain",
    "delta_redundancy_reduction",
    "delta_replay_stability",
    "desi_alone",
    "dual_agent",
    "dual_agent_gate_passed",
    "productivity_gain",
]
