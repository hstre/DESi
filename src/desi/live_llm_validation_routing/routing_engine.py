"""v38.3 - routing engine over real captured costs and qualities.

Builds the routed task set from REAL captures: the six structured
tasks (Granite vs DeepSeek, graded by compliance) and the five hard
semantic tasks (Granite baseline vs DeepSeek, graded by rubric). Each
task carries both models' real cost and quality, the complexity class,
and the model DESi routes it to.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.live_llm_validation import load_captures
from desi.live_llm_validation_deepseek import (
    deepseek_results as semantic_deepseek,
    granite_results as semantic_granite,
)
from desi.live_llm_validation_granite import (
    results as structured_granite,
)
from desi.live_llm_validation_granite import is_compliant
from desi.live_llm_validation_granite.structured_tasks import (
    task_by_id as structured_task,
)

COMPLEXITY_LOW = "low"
COMPLEXITY_HIGH = "high"

ROUTE_GRANITE = "granite"
ROUTE_DEEPSEEK = "deepseek"


@dataclass(frozen=True)
class RoutedTask:
    task_id: str
    complexity: str
    routed_model: str
    granite_cost: float
    deepseek_cost: float
    granite_quality: float
    deepseek_quality: float

    @property
    def routed_cost(self) -> float:
        return (
            self.granite_cost if self.routed_model == ROUTE_GRANITE
            else self.deepseek_cost
        )

    @property
    def routed_quality(self) -> float:
        return (
            self.granite_quality if self.routed_model == ROUTE_GRANITE
            else self.deepseek_quality
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "complexity": self.complexity,
            "routed_model": self.routed_model,
            "granite_cost": self.granite_cost,
            "deepseek_cost": self.deepseek_cost,
            "granite_quality": self.granite_quality,
            "deepseek_quality": self.deepseek_quality,
            "routed_cost": self.routed_cost,
            "routed_quality": self.routed_quality,
        }


def _structured_deepseek() -> dict[str, dict]:
    return {r["task_id"]: r for r in load_captures(
        "routing_deepseek_structured")}


def _route(complexity: str) -> str:
    return ROUTE_DEEPSEEK if complexity == COMPLEXITY_HIGH else ROUTE_GRANITE


def routed_tasks() -> tuple[RoutedTask, ...]:
    out: list[RoutedTask] = []
    # structured tasks: low complexity -> Granite
    ds_struct = _structured_deepseek()
    for g in structured_granite():
        rec = ds_struct.get(g.task_id, {})
        ds_content = rec.get("raw_content", "")
        ds_quality = 1.0 if is_compliant(
            structured_task(g.task_id), ds_content) else 0.0
        out.append(RoutedTask(
            task_id=g.task_id,
            complexity=COMPLEXITY_LOW,
            routed_model=_route(COMPLEXITY_LOW),
            granite_cost=g.cost,
            deepseek_cost=float(rec.get("usage", {}).get("cost") or 0.0),
            granite_quality=1.0 if g.compliant else 0.0,
            deepseek_quality=ds_quality,
        ))
    # semantic tasks: high complexity -> DeepSeek
    gr_sem = {r.task_id: r for r in semantic_granite()}
    for d in semantic_deepseek():
        g = gr_sem.get(d.task_id)
        out.append(RoutedTask(
            task_id=d.task_id,
            complexity=COMPLEXITY_HIGH,
            routed_model=_route(COMPLEXITY_HIGH),
            granite_cost=g.cost if g else 0.0,
            deepseek_cost=d.cost,
            granite_quality=g.rubric_score if g else 0.0,
            deepseek_quality=d.rubric_score,
        ))
    return tuple(out)


__all__ = [
    "COMPLEXITY_HIGH",
    "COMPLEXITY_LOW",
    "ROUTE_DEEPSEEK",
    "ROUTE_GRANITE",
    "RoutedTask",
    "routed_tasks",
]
