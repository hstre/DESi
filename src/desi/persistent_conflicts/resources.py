"""v8.0 — closed resource taxonomy and claim
fixture under scarcity.

Each claim carries an intrinsic
``complexity_cost`` (CPU/attention required to
fully analyze) and ``epistemic_value`` (truth-
yield once analyzed). A CORRECT scheduler under
scarcity processes claims by epistemic_value
within the budget — NOT by 1/complexity_cost.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ResourceKind(str, Enum):
    COMPUTE          = "compute"
    MEMORY           = "memory"
    ATTENTION        = "attention"
    CONFLICT_BUDGET  = "conflict_budget"
    TIME_BUDGET      = "time_budget"


RESOURCE_KINDS: tuple[str, ...] = tuple(
    r.value for r in ResourceKind
)


@dataclass(frozen=True)
class ScarcityClaim:
    claim_id: str
    text: str
    complexity_cost: float
    epistemic_value: float

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "complexity_cost":
                self.complexity_cost,
            "epistemic_value":
                self.epistemic_value,
        }


# 16 claims, four quadrants in the
# (complexity_cost, epistemic_value) plane:
#   - HIGH value, HIGH cost: 4
#   - HIGH value, LOW cost:  4
#   - LOW value,  HIGH cost: 4
#   - LOW value,  LOW cost:  4
_FIXTURE: tuple[ScarcityClaim, ...] = (
    ScarcityClaim("sc-001",
        "Meta-analysis across 14 cohorts with "
        "hierarchical model and adjusted RR.",
        complexity_cost=0.95,
        epistemic_value=0.92),
    ScarcityClaim("sc-002",
        "Pre-registered RCT with 5000 subjects "
        "and adjudicated outcomes.",
        complexity_cost=0.85,
        epistemic_value=0.90),
    ScarcityClaim("sc-003",
        "Long-run prospective study with "
        "competing-risk adjustment.",
        complexity_cost=0.90,
        epistemic_value=0.88),
    ScarcityClaim("sc-004",
        "Bayesian causal inference with "
        "sensitivity analysis.",
        complexity_cost=0.88,
        epistemic_value=0.90),
    ScarcityClaim("sc-005",
        "Direct measurement with calibrated "
        "instrument.",
        complexity_cost=0.20,
        epistemic_value=0.85),
    ScarcityClaim("sc-006",
        "Single-line lab result, replicated.",
        complexity_cost=0.15,
        epistemic_value=0.80),
    ScarcityClaim("sc-007",
        "Published RCT primary outcome.",
        complexity_cost=0.25,
        epistemic_value=0.88),
    ScarcityClaim("sc-008",
        "Replicated benchmark accuracy.",
        complexity_cost=0.20,
        epistemic_value=0.82),
    ScarcityClaim("sc-009",
        "Press release with vague stats.",
        complexity_cost=0.80,
        epistemic_value=0.25),
    ScarcityClaim("sc-010",
        "Glossy report with cherry-picked "
        "subgroups.",
        complexity_cost=0.85,
        epistemic_value=0.20),
    ScarcityClaim("sc-011",
        "Long anecdotal review with rhetorical "
        "flourishes.",
        complexity_cost=0.90,
        epistemic_value=0.15),
    ScarcityClaim("sc-012",
        "Survey of opinions wrapped in jargon.",
        complexity_cost=0.85,
        epistemic_value=0.18),
    ScarcityClaim("sc-013",
        "One-line tweet without source.",
        complexity_cost=0.05,
        epistemic_value=0.10),
    ScarcityClaim("sc-014",
        "Forwarded chain message.",
        complexity_cost=0.08,
        epistemic_value=0.08),
    ScarcityClaim("sc-015",
        "Anonymous comment.",
        complexity_cost=0.05,
        epistemic_value=0.12),
    ScarcityClaim("sc-016",
        "Catchy slogan.",
        complexity_cost=0.10,
        epistemic_value=0.08),
)


def fixture() -> tuple[ScarcityClaim, ...]:
    return _FIXTURE


__all__ = [
    "RESOURCE_KINDS",
    "ResourceKind",
    "ScarcityClaim",
    "fixture",
]
