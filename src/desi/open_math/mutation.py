"""v12.0 — deterministic mutation of hypotheses.

The wild brother proposes; this module replays
the proposals through a deterministic mutation
function so the lineage stays auditable. Each
mutation is hashed by ``(parent_id, mutation_
op, step)`` so the full lineage is reproducible.

Mutation operations are CLOSED - the wild
brother cannot synthesise an op outside this
enum.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

from .explorer import Hypothesis, fixture


class MutationOp(str, Enum):
    GENERALISE        = "generalise"
    SPECIALISE        = "specialise"
    ANALOGISE         = "analogise"
    RANDOMISE         = "randomise"
    COMBINE           = "combine"


MUTATION_OPS: tuple[str, ...] = tuple(
    m.value for m in MutationOp
)


@dataclass(frozen=True)
class MutationEvent:
    parent_id: str
    child_id: str
    op: str
    step: int
    lineage_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "parent_id": self.parent_id,
            "child_id": self.child_id,
            "op": self.op,
            "step": self.step,
            "lineage_hash":
                self.lineage_hash,
        }


def _lineage_hash(
    parent_id: str, child_id: str,
    op: str, step: int,
) -> str:
    raw = (
        f"{parent_id}|{child_id}|{op}|{step}"
        .encode("utf-8")
    )
    return hashlib.sha256(raw).hexdigest()[:16]


@lru_cache(maxsize=1)
def mutation_events() -> tuple[
    MutationEvent, ...,
]:
    """Synthesise a deterministic mutation
    lineage over the closed fixture. Each
    hypothesis after the first is a mutation
    of the previous one under a closed op."""
    hyps = fixture()
    if len(hyps) < 2:
        return ()
    out: list[MutationEvent] = []
    ops = MUTATION_OPS
    for i in range(1, len(hyps)):
        parent = hyps[i - 1]
        child = hyps[i]
        op = ops[i % len(ops)]
        out.append(MutationEvent(
            parent_id=parent.hypothesis_id,
            child_id=child.hypothesis_id,
            op=op,
            step=i,
            lineage_hash=_lineage_hash(
                parent.hypothesis_id,
                child.hypothesis_id,
                op, i,
            ),
        ))
    return tuple(out)


def op_counts() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(
        e.op for e in mutation_events()
    ))


__all__ = [
    "MUTATION_OPS",
    "MutationEvent",
    "MutationOp",
    "mutation_events",
    "op_counts",
]
