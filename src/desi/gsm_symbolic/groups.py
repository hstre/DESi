"""GSM-Symbolic G0 - template grouping.

Reconstructs the paraphrase/template groups that the frame-invariance
metrics (G1) will operate on: a *group* is the set of all normalised
tasks that share a ``template_id``. This is the GSM-Symbolic analogue of
the ``frame_invariance`` ParaphraseGroup - variants that are expected to
behave identically because they encode the same underlying structure.

G0 only builds and validates the grouping; it computes no model-derived
metric. The invariance rate itself (which needs a correctness signal,
i.e. a model run) is deferred to G1/G2.
"""
from __future__ import annotations

from dataclasses import dataclass

from .normalizer import NormalizedGsmTask, all_normalized_tasks


@dataclass(frozen=True)
class TemplateGroup:
    template_id: str
    family: str
    variant: str
    tasks: tuple[NormalizedGsmTask, ...]

    def size(self) -> int:
        return len(self.tasks)

    def instance_ids(self) -> tuple[str, ...]:
        return tuple(t.instance_id for t in self.tasks)

    def clause_roles(self) -> tuple[str, ...]:
        return tuple(t.clause_role for t in self.tasks)

    def group_key(self) -> str:
        return f"{self.family}:{self.variant}:{self.template_id}"


def build_groups(
    tasks: tuple[NormalizedGsmTask, ...] | None = None,
) -> tuple[TemplateGroup, ...]:
    items = all_normalized_tasks() if tasks is None else tasks
    buckets: dict[str, list[NormalizedGsmTask]] = {}
    order: list[str] = []
    for t in items:
        key = f"{t.family}:{t.variant}:{t.template_id}"
        if key not in buckets:
            buckets[key] = []
            order.append(key)
        buckets[key].append(t)
    groups = [
        TemplateGroup(
            template_id=buckets[k][0].template_id,
            family=buckets[k][0].family,
            variant=buckets[k][0].variant,
            tasks=tuple(buckets[k]),
        )
        for k in order
    ]
    # Deterministic ordering, independent of input order.
    return tuple(sorted(groups, key=lambda g: g.group_key()))


def grouping_integrity(
    groups: tuple[TemplateGroup, ...] | None = None,
) -> float:
    """Fraction of groups that contain more than one variant.

    A template with a single instance cannot exhibit (or fail) invariance,
    so for the probe to be meaningful every group must hold >= 2 variants.
    """
    gs = build_groups() if groups is None else groups
    if not gs:
        return 0.0
    multi = sum(1 for g in gs if g.size() >= 2)
    return round(multi / len(gs), 6)


__all__ = [
    "TemplateGroup",
    "build_groups",
    "grouping_integrity",
]
