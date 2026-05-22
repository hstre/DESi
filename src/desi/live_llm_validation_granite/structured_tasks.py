"""v38.1 - structured task definitions for IBM Granite.

Small, cheap, structured tasks: classification, claim extraction,
schema-following, format constraints, simple evidence mapping and
light audit structuring. Each task carries a deterministic
expectation so the real captured response can be evaluated without
re-calling the model. The grounded vocabulary lets us distinguish a
correct answer from a hallucinated one.
"""
from __future__ import annotations

from dataclasses import dataclass

KIND_CLASSIFICATION = "classification"
KIND_EXTRACTION = "extraction"
KIND_JSON_SCHEMA = "json_schema"
KIND_ONE_WORD = "one_word"
KIND_EVIDENCE_MAPPING = "evidence_mapping"
KIND_AUDIT_STRUCTURING = "audit_structuring"


@dataclass(frozen=True)
class StructuredTask:
    task_id: str
    kind: str
    prompt: str
    expected: tuple[str, ...]
    grounded_vocab: tuple[str, ...]
    max_tokens: int


def structured_tasks() -> tuple[StructuredTask, ...]:
    return (
        StructuredTask(
            "gr_classify", KIND_CLASSIFICATION,
            "Classify the sentiment of the statement 'profits "
            "doubled this year' as exactly one of: positive, "
            "negative, neutral. Reply with one word only.",
            ("positive",), ("positive", "negative", "neutral"), 6),
        StructuredTask(
            "gr_extract", KIND_EXTRACTION,
            "Extract the numeric value from 'Total revenue was 1000.'"
            " Reply with only the number.",
            ("1000",), ("1000",), 8),
        StructuredTask(
            "gr_json", KIND_JSON_SCHEMA,
            "Return only a JSON object with a key \"risk\" whose "
            "value is \"high\" for an overdue receivable. No prose.",
            ("risk", "high"), ("risk", "high", "low", "medium"), 24),
        StructuredTask(
            "gr_oneword", KIND_ONE_WORD,
            "Reply with exactly one word: the antonym of 'increase'.",
            ("decrease",), ("decrease", "reduce", "drop", "decline"),
            6),
        StructuredTask(
            "gr_evidence", KIND_EVIDENCE_MAPPING,
            "Claim c1 is supported only by evidence e2. Which "
            "evidence id supports claim c1? Reply with the id only.",
            ("e2",), ("e1", "e2", "e3"), 6),
        StructuredTask(
            "gr_audit", KIND_AUDIT_STRUCTURING,
            "A footnote states that revenue was recognised early. "
            "Name the audit risk this raises in 2 to 4 words.",
            ("revenue", "recognition"),
            ("revenue", "recognition", "recognised", "recognized",
             "early", "cut-off", "cutoff"),
            16),
    )


def task_by_id(task_id: str) -> StructuredTask:
    for t in structured_tasks():
        if t.task_id == task_id:
            return t
    raise KeyError(task_id)


__all__ = [
    "KIND_AUDIT_STRUCTURING",
    "KIND_CLASSIFICATION",
    "KIND_EVIDENCE_MAPPING",
    "KIND_EXTRACTION",
    "KIND_JSON_SCHEMA",
    "KIND_ONE_WORD",
    "StructuredTask",
    "structured_tasks",
    "task_by_id",
]
