"""Routing policy — deterministic decision: tool, local model, or API model.

The decision is a pure function of (task class, constraints, configured
providers, tool registry). It never calls anything; execution happens later in
the engine. That keeps the *decision* replay-stable and unit-testable, with the
model's (non-deterministic) output isolated downstream.

Order of preference:
  1. A deterministic tool that covers the task  -> always wins (exact, $0, local).
  2. Otherwise a model, filtered by privacy (local_only / prefer_local), then by
     accuracy target (task_scores), then cheapest. Falls back to the
     best-scoring candidate if none clears the bar (flagged as below_target).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from desi_router.providers import ModelSpec, Provider, Registry
from desi_router.routing_table import measured_score
from desi_router.tool_registry import ToolRegistry

# privacy modes
LOCAL_ONLY = "local_only"
PREFER_LOCAL = "prefer_local"
ANY = "any"


@dataclass
class Constraints:
    privacy: str = PREFER_LOCAL
    cost_budget_usd: float = float("inf")
    accuracy_target: float = 0.0


@dataclass
class Decision:
    kind: str                           # "tool" | "model" | "none"
    target: str                         # tool name or "provider/model_id"
    rationale: str
    locality: str = ""                  # "local" | "api" | "tool"
    expected_cost_usd: float = 0.0
    expected_score: float | None = None
    below_target: bool = False
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "target": self.target,
            "rationale": self.rationale,
            "locality": self.locality,
            "expected_cost_usd": self.expected_cost_usd,
            "expected_score": self.expected_score,
            "below_target": self.below_target,
            "extras": self.extras,
        }


_DATE_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")
_DATE_KW = re.compile(r"\b(days?|between|after|before)\b", re.I)
_UNIT_WORDS = (
    r"(?:km|cm|mm|mi|miles?|ft|foot|feet|inch(?:es)?|yd|yards?|kg|mg|lbs?|"
    r"pounds?|oz|ounces?|tonnes?|grams?|meters?|metres?|celsius|fahrenheit|kelvin)"
)
_UNIT = re.compile(
    rf"-?\d+(?:\.\d+)?\s*{_UNIT_WORDS}\s*(?:into|to|in)\s*{_UNIT_WORDS}", re.I
)
_MATH = re.compile(r"\d")
# A bare hyphen between digits is NOT an operator by itself: "2020-2021" and
# "rooms 5-10" are ranges, not subtraction. A hyphen counts as minus only when
# whitespace-separated, or when the query carries an explicit compute cue.
_MATH_OPS = re.compile(r"[+*/]|\s-\s|times|plus|minus|divided|product|sum\b")
_MATH_CUE = re.compile(r"\b(what is|calculate|compute|how much is|equals?)\b", re.I)
_HYPHEN_NUM = re.compile(r"\d\s*-\s*\d")
_CODE = re.compile(r"\b(bug|function|code|stack ?trace|exception|compile|refactor)\b", re.I)
_SCI = re.compile(r"\b(study|claim|evidence|hypothesis|paper|citation|abstract)\b", re.I)
_MEM = re.compile(r"\b(earlier|before|you said|i told you|remember|last time|previously)\b", re.I)


def classify(query: str) -> str:
    """Deterministic, rule-based task classification (v0.1).

    A heuristic, not a model. Returns one of: date_math, unit_conversion,
    math_arithmetic, code_audit, scientific_claim, memory_recall, general.
    Date and units are checked first (ISO dates contain '-', which would
    otherwise read as arithmetic). Callers may override.
    """
    if _DATE_ISO.search(query) and _DATE_KW.search(query):
        return "date_math"
    if _UNIT.search(query):
        return "unit_conversion"
    if _MATH.search(query) and (
        _MATH_OPS.search(query)
        or (_MATH_CUE.search(query) and _HYPHEN_NUM.search(query))
    ):
        return "math_arithmetic"
    if _CODE.search(query):
        return "code_audit"
    if _SCI.search(query):
        return "scientific_claim"
    if _MEM.search(query):
        return "memory_recall"
    return "general"


def _candidates(reg: Registry, task_class: str, privacy: str) -> list[tuple[Provider, ModelSpec]]:
    cands = reg.all_models()
    if privacy == LOCAL_ONLY:
        cands = [(p, m) for p, m in cands if m.is_local]
    return cands


def _score(m: ModelSpec, task_class: str) -> tuple[float | None, str]:
    """Effective capability score and its provenance.

    Measured (from routing_table.json, by exact model-id match) overrides a
    config hint, which overrides nothing. Source is surfaced for transparency.
    """
    measured = measured_score(task_class, m.id)
    if measured is not None:
        return measured, "measured"
    hint = m.task_scores.get(task_class)
    if hint is not None:
        return hint, "config_hint"
    return None, "unmeasured"


def decide(
    task_class: str,
    constraints: Constraints,
    registry: Registry,
    tools: ToolRegistry,
) -> Decision:
    # 1. deterministic tool wins outright
    tool = tools.find(task_class)
    if tool is not None:
        return Decision(
            kind="tool",
            target=tool.name,
            locality="tool",
            expected_cost_usd=0.0,
            expected_score=1.0,
            rationale=(
                f"'{task_class}' is covered by the deterministic tool '{tool.name}': "
                "exact, replay-stable, $0 and fully local — no model needed."
            ),
        )

    # 2. otherwise pick a model
    cands = _candidates(registry, task_class, constraints.privacy)
    if not cands:
        return Decision(
            kind="none", target="", rationale="No provider satisfies the privacy constraint.",
        )

    within_cost = [(p, m) for p, m in cands if m.cost_per_item_usd <= constraints.cost_budget_usd]
    pool = within_cost or cands  # if nothing in budget, still decide (flagged below)

    def sort_key(pm: tuple[Provider, ModelSpec]):
        p, m = pm
        s, _ = _score(m, task_class)
        meets = (s is not None) and (s >= constraints.accuracy_target)
        local_pref = 0 if (constraints.privacy == PREFER_LOCAL and m.is_local) else 1
        # prefer: clears bar, then local (if preferred), then cheaper, then higher score
        return (0 if meets else 1, local_pref, m.cost_per_item_usd, -(s or 0.0))

    p, m = sorted(pool, key=sort_key)[0]
    s, src = _score(m, task_class)
    below = (s is None) or (s < constraints.accuracy_target) or (m.cost_per_item_usd > constraints.cost_budget_usd)
    why = []
    if constraints.privacy == LOCAL_ONLY:
        why.append("privacy=local_only")
    elif constraints.privacy == PREFER_LOCAL and m.is_local:
        why.append("kept local (prefer_local)")
    why.append(f"score={s if s is not None else 'unmeasured'} ({src}) vs target {constraints.accuracy_target}")
    why.append(f"${m.cost_per_item_usd:.5f}/item")
    return Decision(
        kind="model",
        target=f"{p.name}/{m.id}",
        locality="local" if m.is_local else "api",
        expected_cost_usd=m.cost_per_item_usd,
        expected_score=s,
        below_target=below,
        rationale="Model route: " + "; ".join(why) + ".",
        extras={"provider": p.name, "model_id": m.id, "score_source": src},
    )
