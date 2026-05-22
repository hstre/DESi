"""v38.1 - deterministic compliance + hallucination checks.

Evaluates the real captured Granite output against each task's
deterministic expectation. Compliance = the response satisfies the
format/schema and contains the grounded expected answer.
Hallucination = the response asserts a value/label outside the
grounded vocabulary - i.e. it invented something. All checks read the
captured raw content; the model is never re-called.
"""
from __future__ import annotations

import json
import re

from .structured_tasks import (
    KIND_AUDIT_STRUCTURING, KIND_CLASSIFICATION, KIND_EVIDENCE_MAPPING,
    KIND_EXTRACTION, KIND_JSON_SCHEMA, KIND_ONE_WORD, StructuredTask,
)


def _norm(text: str) -> str:
    return text.strip().lower()


def _tokens(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", _norm(text)) if t]


def _try_json(text: str) -> dict | None:
    s = text.strip()
    start, end = s.find("{"), s.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        obj = json.loads(s[start:end + 1])
        return obj if isinstance(obj, dict) else None
    except (ValueError, TypeError):
        return None


def is_compliant(task: StructuredTask, content: str) -> bool:
    norm = _norm(content)
    if task.kind == KIND_JSON_SCHEMA:
        obj = _try_json(content)
        return obj is not None and "risk" in {
            str(k).lower() for k in obj
        }
    if task.kind == KIND_ONE_WORD:
        return len(_tokens(content)) == 1 and any(
            e in norm for e in task.expected
        )
    if task.kind in (KIND_CLASSIFICATION, KIND_EXTRACTION,
                     KIND_EVIDENCE_MAPPING):
        return all(_norm(e) in norm for e in task.expected)
    if task.kind == KIND_AUDIT_STRUCTURING:
        return all(_norm(e) in norm for e in task.expected)
    return False


def is_hallucinated(task: StructuredTask, content: str) -> bool:
    """A response hallucinates if it introduces a value/label outside
    the grounded vocabulary for a closed-vocabulary task."""
    norm = _norm(content)
    if task.kind == KIND_CLASSIFICATION:
        labels = {"positive", "negative", "neutral"}
        present = {lab for lab in labels if lab in norm}
        # exactly the expected label, no other label asserted
        return present != set(task.expected)
    if task.kind == KIND_EVIDENCE_MAPPING:
        ids = {x for x in ("e1", "e2", "e3") if x in _tokens(content)}
        return ids != set(task.expected)
    if task.kind == KIND_EXTRACTION:
        nums = set(re.findall(r"\d+", content))
        return bool(nums) and nums != set(task.expected)
    # open-ended tasks: hallucination only if compliance fails
    # AND content is non-empty with off-vocab claims
    if not is_compliant(task, content):
        toks = set(_tokens(content))
        return bool(toks) and not (toks & {
            _norm(v) for v in task.grounded_vocab
        })
    return False


__all__ = [
    "is_compliant",
    "is_hallucinated",
]
