"""v38.2 - hard semantic task definitions for DeepSeek V4 Pro.

Semantic audit tensions, multi-hop reasoning, narrative conflicts,
evidence gaps and complex semantic conflicts. Each task carries a
deterministic rubric (required element groups) so a real captured
response can be scored without re-calling the model. Tasks flagged
is_gap require an evidence gap to be preserved (surfaced), not papered
over.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticTask:
    task_id: str
    prompt: str
    required_elements: tuple[tuple[str, ...], ...]
    is_gap: bool
    max_tokens: int


def semantic_tasks() -> tuple[SemanticTask, ...]:
    return (
        SemanticTask(
            "ds_audit_tension",
            "A company reports strong cash generation, but its "
            "operating cashflow EXCLUDES one-off receipts and its "
            "revenue INCLUDES early-recognised deferred amounts. In "
            "two short sentences, name the cashflow tension and the "
            "revenue-recognition tension an auditor should flag.",
            (("cash",),
             ("revenue", "recognition", "recognised", "recognized",
              "deferred")),
            True, 1200),
        SemanticTask(
            "ds_multihop",
            "Question: in what country is the capital of the country "
            "where the author of book B was born? Facts: the author "
            "of B was born in city X; city X is the capital of "
            "country K. List the reasoning hops explicitly.",
            (("born", "author"), ("capital",), ("country", "k")),
            False, 1200),
        SemanticTask(
            "ds_narrative_conflict",
            "A footnote states receivables overdue more than 90 days "
            "INCREASED materially. The narrative states collections "
            "ACCELERATED versus prior year. State the conflict "
            "between the footnote and the narrative.",
            (("90", "overdue", "ageing", "aging", "increase",
              "increased"),
             ("collection", "collections", "accelerat")),
            False, 1200),
        SemanticTask(
            "ds_evidence_gap",
            "A paper claims 'the method generalizes across "
            "datasets' but reports evidence on only ONE dataset. "
            "What evidence is missing, and should the claim be "
            "accepted as stated?",
            (("dataset", "datasets", "additional", "more", "other",
              "second", "multiple"),
             ("missing", "insufficient", "not", "cannot",
              "generaliz")),
            True, 1200),
        SemanticTask(
            "ds_complex_conflict",
            "The financial statements are formally correct (the "
            "numbers add up), but management describes a clearly "
            "one-off gain as 'sustainable core growth'. Identify the "
            "semantic red flag.",
            (("one-off", "one off", "nonrecurring", "non-recurring",
              "one-time", "nonrecurring"),
             ("sustainable", "core", "recurring", "misleading",
              "mischaracter")),
            False, 1200),
    )


def task_by_id(task_id: str) -> SemanticTask:
    for t in semantic_tasks():
        if t.task_id == task_id:
            return t
    raise KeyError(task_id)


__all__ = ["SemanticTask", "semantic_tasks", "task_by_id"]
