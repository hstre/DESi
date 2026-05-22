"""v38.2 - deterministic semantic rubric + grounding analysis.

Scores a real captured response against a task's required element
groups (a rubric element is satisfied if any of its synonyms appears).
Also exposes a grounding analysis: the count of content tokens not
present in the prompt, surfaced so any potential hallucination is
visible rather than hidden.
"""
from __future__ import annotations

import re

from .semantic_tasks import SemanticTask

_STOP = frozenset({
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "are",
    "was", "were", "be", "as", "for", "on", "by", "it", "its", "this",
    "that", "with", "from", "at", "but", "not", "no", "should", "than",
    "which", "what", "where", "two", "one", "sentence", "sentences",
})


def _norm(text: str) -> str:
    return text.lower()


def _tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", _norm(text)) if t]


def rubric_score(task: SemanticTask, content: str) -> float:
    norm = _norm(content)
    if not task.required_elements:
        return 0.0
    hit = 0
    for group in task.required_elements:
        if any(syn in norm for syn in group):
            hit += 1
    return round(hit / len(task.required_elements), 6)


def gap_preserved(task: SemanticTask, content: str) -> bool:
    """For a gap task, the gap is preserved iff the response surfaces
    the gap-related element group (the second group)."""
    if not task.is_gap:
        return True
    norm = _norm(content)
    group = task.required_elements[-1]
    return any(syn in norm for syn in group)


def ungrounded_token_count(task: SemanticTask, content: str) -> int:
    """Content tokens (non-stopword, length>=4) not present in the
    prompt - surfaced as a visible hallucination signal."""
    prompt_tokens = set(_tokens(task.prompt))
    out = 0
    for t in _tokens(content):
        if len(t) >= 4 and t not in _STOP and t not in prompt_tokens:
            out += 1
    return out


__all__ = [
    "gap_preserved",
    "rubric_score",
    "ungrounded_token_count",
]
