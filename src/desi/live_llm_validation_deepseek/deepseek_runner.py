"""v38.2 - DeepSeek runner with a real Granite baseline (capture+replay).

`capture_all` makes the real DeepSeek V4 Pro calls AND a real Granite
baseline call for every semantic task (run once; committed as the
replay source), so the semantic-quality lift is a real measured
comparison. `deepseek_results` / `granite_results` read the committed
captures for deterministic evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass

from desi.live_llm_validation import (
    ROLE_DEEPSEEK, ROLE_GRANITE, capture_response, load_captures,
    model_for_role, write_captures,
)

from .audit_semantic_checks import (
    gap_preserved, rubric_score, ungrounded_token_count,
)
from .semantic_tasks import SemanticTask, semantic_tasks, task_by_id

_DEEPSEEK_CAPTURE = "deepseek_tasks"
_GRANITE_BASELINE = "deepseek_granite_baseline"


def capture_all() -> tuple[str, str]:
    ds_model = model_for_role(ROLE_DEEPSEEK)
    gr_model = model_for_role(ROLE_GRANITE)
    ds_records, gr_records = [], []
    for t in semantic_tasks():
        msg = [{"role": "user", "content": t.prompt}]
        ds_records.append(capture_response(
            t.task_id, ROLE_DEEPSEEK, ds_model, msg,
            max_tokens=t.max_tokens))
        gr_records.append(capture_response(
            t.task_id, ROLE_GRANITE, gr_model, msg,
            max_tokens=t.max_tokens))
    p1 = write_captures(_DEEPSEEK_CAPTURE, ds_records)
    p2 = write_captures(_GRANITE_BASELINE, gr_records)
    return str(p1), str(p2)


@dataclass(frozen=True)
class SemanticResult:
    task_id: str
    model_version: str
    content: str
    rubric_score: float
    gap_preserved: bool
    ungrounded_tokens: int
    cost: float

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "model_version": self.model_version,
            "content": self.content,
            "rubric_score": self.rubric_score,
            "gap_preserved": self.gap_preserved,
            "ungrounded_tokens": self.ungrounded_tokens,
            "cost": self.cost,
        }


def _results(capture_name: str) -> tuple[SemanticResult, ...]:
    out: list[SemanticResult] = []
    for rec in load_captures(capture_name):
        task: SemanticTask = task_by_id(rec["task_id"])
        content = rec.get("raw_content", "")
        out.append(SemanticResult(
            task_id=task.task_id,
            model_version=rec.get("model_version", ""),
            content=content,
            rubric_score=rubric_score(task, content),
            gap_preserved=gap_preserved(task, content),
            ungrounded_tokens=ungrounded_token_count(task, content),
            cost=float(rec.get("usage", {}).get("cost") or 0.0),
        ))
    return tuple(out)


def deepseek_results() -> tuple[SemanticResult, ...]:
    return _results(_DEEPSEEK_CAPTURE)


def granite_results() -> tuple[SemanticResult, ...]:
    return _results(_GRANITE_BASELINE)


__all__ = [
    "SemanticResult",
    "capture_all",
    "deepseek_results",
    "granite_results",
]
