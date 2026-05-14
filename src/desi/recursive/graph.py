"""ResolutionGraph — the deterministic graph the resolver walks.

The resolver builds a directed graph of claim nodes during each
recursive walk. Nodes are identified by a stable hash of the
claim's *canonical text* (whitespace-normalised, lowercased) so
that the same proposition collides on every entry — the basis for
cycle detection and replay-hash determinism.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Iterator


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower()).rstrip(".")


def node_id(claim_text: str) -> str:
    """Stable 16-char identifier for a claim's canonical text."""
    h = hashlib.sha256(_normalise(claim_text).encode("utf-8"))
    return "rn_" + h.hexdigest()[:16]


@dataclass(frozen=True)
class GraphNode:
    """One node in the resolution graph."""

    node_id: str
    claim_text: str
    depth: int


@dataclass
class ResolutionGraph:
    """An append-only DAG of (parent, child) edges plus node metadata.

    The graph is deliberately mutable during the walk; once the
    walk completes, callers freeze it through
    :meth:`canonical_edges`. The resolver never deletes a node or
    an edge — every recorded relationship survives in the audit.
    """

    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)

    def add_node(self, claim_text: str, *, depth: int) -> GraphNode:
        nid = node_id(claim_text)
        if nid not in self.nodes:
            self.nodes[nid] = GraphNode(
                node_id=nid, claim_text=claim_text, depth=depth,
            )
        return self.nodes[nid]

    def add_edge(self, parent_text: str, child_text: str) -> None:
        edge = (node_id(parent_text), node_id(child_text))
        # Append-only — duplicate edges are tolerated (a parent may
        # reference the same child twice with two different bridges
        # pointing at it). Determinism is restored at canonicalisation.
        self.edges.append(edge)

    def canonical_edges(self) -> tuple[tuple[str, str], ...]:
        """Sorted, de-duplicated edge list — the basis for replay_hash."""
        return tuple(sorted(set(self.edges)))

    def canonical_nodes(self) -> tuple[str, ...]:
        """Sorted node-id list."""
        return tuple(sorted(self.nodes.keys()))

    def __iter__(self) -> Iterator[GraphNode]:
        return iter(self.nodes.values())

    def __len__(self) -> int:
        return len(self.nodes)

    def to_dict(self) -> dict:
        return {
            "nodes": [
                {"node_id": n.node_id, "claim_text": n.claim_text,
                 "depth": n.depth}
                for n in sorted(self.nodes.values(),
                                 key=lambda x: x.node_id)
            ],
            "edges": [list(e) for e in self.canonical_edges()],
        }


__all__ = [
    "GraphNode",
    "ResolutionGraph",
    "node_id",
]
