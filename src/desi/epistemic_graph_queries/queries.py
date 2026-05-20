"""v24.3 - read-only graph queries.

Structural read primitives over the v24.0 epistemic graph. These
queries return provenance; they make no decision, rank nothing
and never write. They are the substrate for automatic scientific
traceability, citation and paper lineage.
"""
from __future__ import annotations

from desi.epistemic_graph import (
    edges_of_type, nodes_of_type, out_edges,
)
from desi.epistemic_graph.nodes import NodeType


def _strip(node_id: str) -> str:
    return node_id.split(":", 1)[1]


def claim_ids() -> tuple[str, ...]:
    return tuple(
        _strip(n.node_id)
        for n in nodes_of_type(NodeType.CLAIM.value)
    )


def claim_text(claim_id: str) -> str:
    for n in nodes_of_type(NodeType.CLAIM.value):
        if n.node_id == f"claim:{claim_id}":
            return n.label
    raise KeyError(claim_id)


def _out_targets(
    node_id: str, edge_type: str, prefix: str | None = None,
) -> tuple[str, ...]:
    targets = (
        e.target for e in out_edges(node_id)
        if e.edge_type == edge_type
    )
    if prefix is not None:
        targets = (t for t in targets if t.startswith(prefix))
    return tuple(sorted(targets))


def generating_sprints(claim_id: str) -> tuple[str, ...]:
    return tuple(
        _strip(t) for t in _out_targets(
            f"claim:{claim_id}", "GENERATED_IN", "sprint:")
    )


def methods_of(claim_id: str) -> tuple[str, ...]:
    return tuple(
        _strip(t) for t in _out_targets(
            f"claim:{claim_id}", "DERIVED_FROM", "method:")
    )


def fixtures_of(claim_id: str) -> tuple[str, ...]:
    return tuple(
        _strip(t) for t in _out_targets(
            f"claim:{claim_id}", "DERIVED_FROM", "fixture:")
    )


def replay_hashes_of(claim_id: str) -> tuple[str, ...]:
    return tuple(
        _strip(t) for t in _out_targets(
            f"claim:{claim_id}", "VALIDATED_BY", "replayhash:")
    )


def limitations_of(claim_id: str) -> tuple[str, ...]:
    return tuple(
        _strip(t) for t in _out_targets(
            f"claim:{claim_id}", "LIMITED_BY", "limitation:")
    )


def governance_of(claim_id: str) -> tuple[str, ...]:
    return tuple(
        _strip(t) for t in _out_targets(
            f"claim:{claim_id}", "GOVERNED_BY", "rule:")
    )


def supporting_metrics(claim_id: str) -> tuple[str, ...]:
    return tuple(sorted(
        _strip(e.source) for e in edges_of_type("SUPPORTS")
        if e.target == f"claim:{claim_id}"
    ))


def provenance_of(claim_id: str) -> dict[str, object]:
    return {
        "claim_id": claim_id,
        "sprints": list(generating_sprints(claim_id)),
        "methods": list(methods_of(claim_id)),
        "fixtures": list(fixtures_of(claim_id)),
        "replay_hashes": list(replay_hashes_of(claim_id)),
        "limitations": list(limitations_of(claim_id)),
        "governance": list(governance_of(claim_id)),
        "metrics": list(supporting_metrics(claim_id)),
    }


# --- metric-side queries ------------------------
def metric_names() -> tuple[str, ...]:
    return tuple(
        _strip(n.node_id)
        for n in nodes_of_type(NodeType.METRIC.value)
    )


def metric_sprints(metric: str) -> tuple[str, ...]:
    return tuple(
        _strip(t) for t in _out_targets(
            f"metric:{metric}", "GENERATED_IN", "sprint:")
    )


def metric_replay_hashes(metric: str) -> tuple[str, ...]:
    return tuple(
        _strip(t) for t in _out_targets(
            f"metric:{metric}", "REPLAYED_AS", "replayhash:")
    )


def metric_supported_claims(metric: str) -> tuple[str, ...]:
    return tuple(
        _strip(t) for t in _out_targets(
            f"metric:{metric}", "SUPPORTS", "claim:")
    )


__all__ = [
    "claim_ids",
    "claim_text",
    "fixtures_of",
    "generating_sprints",
    "governance_of",
    "limitations_of",
    "methods_of",
    "metric_names",
    "metric_replay_hashes",
    "metric_sprints",
    "metric_supported_claims",
    "provenance_of",
    "replay_hashes_of",
    "supporting_metrics",
]
