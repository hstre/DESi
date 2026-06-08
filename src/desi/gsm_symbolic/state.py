"""GSM-Symbolic DESi arm - deterministic Level-A/B state extractor.

The DESi arm of the probe structures a task *before* it is solved,
separating surface form, (suspected) irrelevant clauses and the relevant
quantities. This module is the deterministic, rule-based skeleton of
that structuring - "rules for logic": it extracts a Level-A/B state and
performs **no arithmetic and no answer derivation** (the design's Level C
is deliberately excluded, so the structuring pass can never pre-solve the
task).

Levels (see docs/gsm_symbolic_experiment_design.md section 4.1):

* Level A - representation: clauses, which clause is the question core,
  the numeric quantities, and a per-clause *suspected-irrelevant* flag.
* Level B - operation constraints: the answer_type and the set of
  relevant quantities available to a downstream solver. No operators,
  no ordered steps, no execution.

NoOp heuristic (intentionally simple and honest): a non-core clause is
*suspected irrelevant* iff it contains no numeric token. On the P2
fixtures this cleanly separates noop clauses ("painted blue") from
load-bearing and adversarial-similar clauses (which carry numbers). Its
blind spots are real and documented/tested: a noop clause with a decoy
number is wrongly kept, and an adversarial clause that hides its operand
in words ("gives half back") is wrongly dropped. A numeric cue is a
proxy for relevance, not relevance itself.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .normalizer import NormalizedGsmTask, all_normalized_tasks

_NUMBER = re.compile(r"\d")
_SENTENCE_SPLIT = re.compile(r"(?<=[.?])\s+")

# Expected per-role outcome of the suspected-irrelevant flag on the
# clause a P2 variant adds over its base.
_ROLE_SHOULD_BE_IRRELEVANT = {
    "noop": True,
    "load_bearing": False,
    "adversarial_similar": False,
}


def has_number(text: str) -> bool:
    return bool(_NUMBER.search(text))


def clause_is_suspected_irrelevant(text: str, *, is_core: bool) -> bool:
    """The NoOp heuristic: a non-core clause with no numeric token."""
    return (not is_core) and not has_number(text)


def split_clauses(question: str) -> tuple[str, ...]:
    parts = [p.strip() for p in _SENTENCE_SPLIT.split(question.strip())]
    return tuple(p for p in parts if p)


@dataclass(frozen=True)
class Clause:
    text: str
    is_core: bool
    has_number: bool
    suspected_irrelevant: bool


@dataclass(frozen=True)
class DesiState:
    task_id: str
    answer_type: str
    clauses: tuple[Clause, ...]

    def relevant_clauses(self) -> tuple[Clause, ...]:
        return tuple(c for c in self.clauses if not c.suspected_irrelevant)

    def irrelevant_clauses(self) -> tuple[Clause, ...]:
        return tuple(c for c in self.clauses if c.suspected_irrelevant)

    def quantities(self) -> tuple[str, ...]:
        """Level-A relevant quantities: numeric tokens from the clauses
        not flagged irrelevant. No arithmetic is performed on them."""
        out: list[str] = []
        for c in self.relevant_clauses():
            out.extend(re.findall(r"\d+(?:\.\d+)?", c.text))
        return tuple(out)

    def to_dict(self) -> dict[str, object]:
        return {
            "task_id": self.task_id,
            "answer_type": self.answer_type,
            "quantities": list(self.quantities()),
            "relevant_clauses": [c.text for c in self.relevant_clauses()],
            "irrelevant_clauses": [
                c.text for c in self.irrelevant_clauses()
            ],
        }


def extract_state(task: NormalizedGsmTask) -> DesiState:
    clauses: list[Clause] = []
    for raw in split_clauses(task.question):
        is_core = raw.endswith("?")
        clauses.append(Clause(
            text=raw,
            is_core=is_core,
            has_number=has_number(raw),
            suspected_irrelevant=clause_is_suspected_irrelevant(
                raw, is_core=is_core,
            ),
        ))
    return DesiState(
        task_id=task.task_id,
        answer_type=task.answer_type,
        clauses=tuple(clauses),
    )


def extract_all() -> tuple[DesiState, ...]:
    return tuple(extract_state(t) for t in all_normalized_tasks())


def _added_clause(base_question: str, variant_question: str) -> str | None:
    """The single clause a P2 variant adds over its base."""
    base = set(split_clauses(base_question))
    added = [s for s in split_clauses(variant_question) if s not in base]
    return added[0] if len(added) == 1 else None


def noop_detection_metrics() -> dict[str, object]:
    """Evaluate the NoOp heuristic against the P2 negative controls.

    For each P2 template, isolate the clause every non-base variant adds
    and check whether the heuristic's suspected-irrelevant flag matches
    the role's expectation (noop -> irrelevant, load_bearing /
    adversarial_similar -> relevant).
    """
    by_template: dict[str, dict[str, str]] = {}
    for t in all_normalized_tasks():
        if t.variant != "p2":
            continue
        by_template.setdefault(t.template_id, {})[t.clause_role] = (
            t.question
        )

    per_role: dict[str, list[int]] = {
        r: [0, 0] for r in _ROLE_SHOULD_BE_IRRELEVANT
    }
    for roles in by_template.values():
        base_q = roles.get("base")
        if base_q is None:
            continue
        for role, expected in _ROLE_SHOULD_BE_IRRELEVANT.items():
            variant_q = roles.get(role)
            if variant_q is None:
                continue
            added = _added_clause(base_q, variant_q)
            if added is None:
                continue
            flagged = clause_is_suspected_irrelevant(
                added, is_core=added.endswith("?"),
            )
            per_role[role][1] += 1
            if flagged is expected:
                per_role[role][0] += 1

    correct = sum(v[0] for v in per_role.values())
    total = sum(v[1] for v in per_role.values())
    return {
        "per_role": {
            r: {"correct": v[0], "total": v[1]}
            for r, v in per_role.items()
        },
        "accuracy": round(correct / total, 6) if total else 0.0,
    }


__all__ = [
    "Clause",
    "DesiState",
    "clause_is_suspected_irrelevant",
    "extract_all",
    "extract_state",
    "has_number",
    "noop_detection_metrics",
    "split_clauses",
]
