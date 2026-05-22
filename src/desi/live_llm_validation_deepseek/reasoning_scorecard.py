"""v38.2 - per-task semantic reasoning scorecard.

Pairs each task's real DeepSeek result with the real Granite baseline,
exposing the rubric scores, gap preservation and the visible
ungrounded-token (potential-hallucination) signal. Nothing is hidden:
the grounding analysis is surfaced for every response.
"""
from __future__ import annotations

from dataclasses import dataclass

from .deepseek_runner import deepseek_results, granite_results
from .semantic_tasks import task_by_id


@dataclass(frozen=True)
class SemanticScorecard:
    task_id: str
    is_gap: bool
    deepseek_rubric: float
    granite_rubric: float
    deepseek_gap_preserved: bool
    deepseek_ungrounded_tokens: int
    deepseek_cost: float

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "is_gap": self.is_gap,
            "deepseek_rubric": self.deepseek_rubric,
            "granite_rubric": self.granite_rubric,
            "deepseek_gap_preserved": self.deepseek_gap_preserved,
            "deepseek_ungrounded_tokens":
                self.deepseek_ungrounded_tokens,
            "deepseek_cost": self.deepseek_cost,
        }


def scorecards() -> tuple[SemanticScorecard, ...]:
    gr = {r.task_id: r for r in granite_results()}
    out: list[SemanticScorecard] = []
    for d in deepseek_results():
        out.append(SemanticScorecard(
            task_id=d.task_id,
            is_gap=task_by_id(d.task_id).is_gap,
            deepseek_rubric=d.rubric_score,
            granite_rubric=gr[d.task_id].rubric_score
            if d.task_id in gr else 0.0,
            deepseek_gap_preserved=d.gap_preserved,
            deepseek_ungrounded_tokens=d.ungrounded_tokens,
            deepseek_cost=d.cost,
        ))
    return tuple(out)


__all__ = ["SemanticScorecard", "scorecards"]
