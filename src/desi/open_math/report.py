"""v12.0 — wild exploration sandbox report.

Five Pflichtmetriken:

* ``exploration_diversity``
* ``branch_growth``
* ``redundancy_rate``
* ``hallucination_pressure``
* ``replay_stability``

Killerfrage: "Kann kontrolliertes epistemisches
Chaos erzeugt werden, ohne sofort zu
kollabieren?"
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass

from .explorer import (
    HYPOTHESIS_SHAPES, fixture,
    shape_counts, status_counts,
)
from .governance import (
    classification_accuracy,
    governed_hypotheses,
    overreach_rejection_rate,
    replay_reuse_rate,
)
from .hypotheses import EPISTEMIC_STATUSES
from .mutation import (
    MUTATION_OPS, mutation_events, op_counts,
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def exploration_diversity() -> float:
    """Normalised Shannon entropy over the
    hypothesis-shape distribution. 1.0 = uniform
    coverage of all closed shapes."""
    counts = shape_counts()
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        p = c / total
        if p > 0:
            h -= p * math.log2(p)
    max_h = math.log2(
        max(len(HYPOTHESIS_SHAPES), 2),
    )
    if max_h <= 0:
        return 0.0
    return _round(h / max_h)


def branch_growth() -> int:
    """Number of mutation events emitted -
    the closed measure of how much the search
    space grew."""
    return len(mutation_events())


def redundancy_rate() -> float:
    """Fraction of hypotheses whose text
    OVERLAPS substantially with a prior
    hypothesis (operationalised: same first
    40 characters as any earlier one)."""
    rows = fixture()
    seen: dict[str, str] = {}
    dup = 0
    for h in rows:
        key = h.text[:40]
        if key in seen:
            dup += 1
        else:
            seen[key] = h.hypothesis_id
    if not rows:
        return 0.0
    return _round(dup / len(rows))


def hallucination_pressure() -> float:
    """Fraction of generated hypotheses that
    are ground-truth REJECTED overreach. High
    pressure means the wild brother is
    aggressively proposing dangerous claims;
    the v12.1 governance must still catch
    them."""
    rows = fixture()
    if not rows:
        return 0.0
    return _round(sum(
        1 for h in rows if h.is_overreach
    ) / len(rows))


@dataclass(frozen=True)
class V120Report:
    hypothesis_count: int
    exploration_diversity: float
    branch_growth: int
    redundancy_rate: float
    hallucination_pressure: float
    classification_accuracy: float
    overreach_rejection_rate: float
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "hypothesis_count":
                self.hypothesis_count,
            "exploration_diversity":
                self.exploration_diversity,
            "branch_growth":
                self.branch_growth,
            "redundancy_rate":
                self.redundancy_rate,
            "hallucination_pressure":
                self.hallucination_pressure,
            "classification_accuracy":
                self.classification_accuracy,
            "overreach_rejection_rate":
                self.overreach_rejection_rate,
            "replay_stability":
                self.replay_stability,
            "halt": self.halt,
            "recommendation":
                self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def _replay_stability() -> float:
    a = (
        exploration_diversity(),
        branch_growth(), redundancy_rate(),
        hallucination_pressure(),
        classification_accuracy(),
        overreach_rejection_rate(),
        replay_reuse_rate(),
    )
    b = (
        exploration_diversity(),
        branch_growth(), redundancy_rate(),
        hallucination_pressure(),
        classification_accuracy(),
        overreach_rejection_rate(),
        replay_reuse_rate(),
    )
    return 1.0 if a == b else 0.0


def _recommendation(
    *, replay: float, div: float,
    ca: float, orr: float, hp: float,
) -> str:
    if replay < 1.0:
        return "HALT_REPLAY_DRIFT"
    if orr < 1.0:
        return "WILD_OVERREACH_LEAK"
    if ca < 0.90:
        return "WILD_CLASSIFIER_WEAK"
    if div < 0.70:
        return "WILD_NARROW_EXPLORATION"
    if hp > 0.40:
        return "WILD_HALLUCINATION_HEAVY"
    return "WILD_DISCIPLINED"


def build_report() -> V120Report:
    div = exploration_diversity()
    bg = branch_growth()
    rr = redundancy_rate()
    hp = hallucination_pressure()
    ca = classification_accuracy()
    orr = overreach_rejection_rate()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, div=div, ca=ca,
        orr=orr, hp=hp,
    )
    rationale = (
        f"INFO: hypothesis_count "
        f"{len(fixture())}",
        f"INFO: shape_counts {shape_counts()}",
        f"INFO: status_counts {status_counts()}",
        f"INFO: op_counts {op_counts()}",
        f"INFO: classification_accuracy {ca}",
        f"{'PASS' if div >= 0.70 else 'FAIL'}: "
        f"exploration_diversity {div} >= 0.70",
        f"INFO: branch_growth {bg}",
        f"INFO: redundancy_rate {rr}",
        f"INFO: hallucination_pressure {hp}",
        f"{'PASS' if orr == 1.0 else 'FAIL'}: "
        f"overreach_rejection_rate {orr}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V120Report(
        hypothesis_count=len(fixture()),
        exploration_diversity=div,
        branch_growth=bg,
        redundancy_rate=rr,
        hallucination_pressure=hp,
        classification_accuracy=ca,
        overreach_rejection_rate=orr,
        replay_stability=replay,
        halt=halt, recommendation=verdict,
        rationale=rationale,
    )


def build_wild_sandbox_artifact(
) -> dict[str, object]:
    return {
        "schema_version":
            "v12_0_wild_exploration_sandbox",
        "hypothesis_shapes":
            list(HYPOTHESIS_SHAPES),
        "epistemic_statuses":
            list(EPISTEMIC_STATUSES),
        "mutation_ops": list(MUTATION_OPS),
        "hypothesis_count": len(fixture()),
        "shape_counts": shape_counts(),
        "status_counts": status_counts(),
        "op_counts": op_counts(),
        "hypotheses": [
            h.to_dict() for h in fixture()
        ],
        "mutation_events": [
            m.to_dict()
            for m in mutation_events()
        ],
        "governed_hypotheses": [
            g.to_dict()
            for g in governed_hypotheses()
        ],
        "exploration_diversity":
            exploration_diversity(),
        "branch_growth": branch_growth(),
        "redundancy_rate": redundancy_rate(),
        "hallucination_pressure":
            hallucination_pressure(),
        "classification_accuracy":
            classification_accuracy(),
        "overreach_rejection_rate":
            overreach_rejection_rate(),
    }


__all__ = [
    "V120Report",
    "branch_growth",
    "build_report",
    "build_wild_sandbox_artifact",
    "exploration_diversity",
    "hallucination_pressure",
    "redundancy_rate",
]
