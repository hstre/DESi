"""v6.2 — ecology summary primitives.

Wraps cross_paper + conflict_graph into the
audit-level view: per-topic clusters, uncertainty
zones (topics where direction signs disagree),
and per-school distributions.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .conflict_graph import components, nodes
from .cross_paper import (
    EcologyConflictKind, corpus,
    detected_conflicts,
)


@dataclass(frozen=True)
class TopicCluster:
    topic: str
    papers: tuple[str, ...]
    schools: tuple[str, ...]
    directions: tuple[str, ...]
    is_uncertainty_zone: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "topic": self.topic,
            "papers": list(self.papers),
            "schools": list(self.schools),
            "directions":
                list(self.directions),
            "is_uncertainty_zone":
                self.is_uncertainty_zone,
        }


def topic_clusters() -> tuple[TopicCluster, ...]:
    by_topic: dict[
        str, list,
    ] = {}
    for p in corpus():
        by_topic.setdefault(
            p.topic, [],
        ).append(p)
    out: list[TopicCluster] = []
    for topic in sorted(by_topic.keys()):
        papers = tuple(
            sorted(
                p.paper_id
                for p in by_topic[topic]
            ),
        )
        schools = tuple(
            sorted({
                p.school
                for p in by_topic[topic]
            }),
        )
        directions = tuple(
            sorted({
                p.direction
                for p in by_topic[topic]
            }),
        )
        signs = {
            d for d in directions
            if d in {"+", "-"}
        }
        is_uncertain = (
            len(signs) > 1
            or (
                "0" in directions
                and len(directions) > 1
            )
        )
        out.append(TopicCluster(
            topic=topic, papers=papers,
            schools=schools,
            directions=directions,
            is_uncertainty_zone=is_uncertain,
        ))
    return tuple(out)


def uncertainty_zone_count() -> int:
    return sum(
        1 for c in topic_clusters()
        if c.is_uncertainty_zone
    )


def conflict_kind_counts() -> dict[str, int]:
    cnt = Counter(
        c.kind for c in detected_conflicts()
    )
    return {k: cnt[k] for k in sorted(cnt)}


def school_distribution() -> dict[str, int]:
    cnt = Counter(p.school for p in corpus())
    return {k: cnt[k] for k in sorted(cnt)}


def component_sizes() -> tuple[int, ...]:
    return tuple(len(c) for c in components())


__all__ = [
    "TopicCluster",
    "component_sizes",
    "conflict_kind_counts",
    "school_distribution",
    "topic_clusters",
    "uncertainty_zone_count",
]
