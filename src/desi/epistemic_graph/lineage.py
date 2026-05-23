"""v24.0 - deterministic epistemic graph construction.

Builds a read-only graph over the existing DESi structures.
Claim nodes and their sprint provenance are read live from the
v23 anchoring layer; the surrounding structural nodes (methods,
fixtures, limitations, governance rules, replay hashes, the
dissent path and the ecology run) are curated deterministic
fixtures. No heavy computation and no recomputed metric values
are pulled in - values stay canonical in the JSON artifacts.
"""
from __future__ import annotations

import hashlib
import re
from functools import lru_cache

from desi.icrl_followup_revision import claims
from desi.icrl_followup_conditions import definitions, sandbox_limits

from .edges import Edge
from .nodes import Node, NodeType

_SPRINT_RE = re.compile(r"v\d+\.\d+")

# --- curated structural vocabularies ------------
_METHODS: dict[str, str] = {
    "soft_reweighting": "Soft re-weighting of redundant search",
    "containment": "Containment of high-certainty incoherent "
                   "paths",
    "generator_governor_split": "Generator/governor split",
    "negotiation": "Region-preserving negotiation",
    "bounded_saturating_drift": "Bounded saturating authority "
                                "drift",
}

_FIXTURES: dict[str, str] = {
    "synthetic_trajectories": "Synthetic fixed trajectory set",
    "hallucinated_paths": "Adversarial hallucinated-path "
                          "fixture",
    "region_partition": "Distinct-region partition fixture",
    "ecology_5600": "5600-step deterministic ecology fixture",
}

_RULES: dict[str, str] = {
    "forbidden_terms": "No forbidden / hype terminology",
    "read_only_layer": "Governance layer is read-only",
    "no_hidden_authority": "No hidden optimisation authority",
}

# claim_id -> derivations / scoping / governance.
_CLAIM_METHODS: dict[str, tuple[str, ...]] = {
    "DC1": ("soft_reweighting",),
    "DC2": ("containment",),
    "DC3": ("generator_governor_split", "negotiation"),
    "DC4": ("soft_reweighting",),
    "DC5": ("bounded_saturating_drift", "negotiation"),
}
_CLAIM_FIXTURES: dict[str, tuple[str, ...]] = {
    "DC1": ("synthetic_trajectories",),
    "DC2": ("hallucinated_paths",),
    "DC3": ("synthetic_trajectories",),
    "DC4": ("synthetic_trajectories",),
    "DC5": ("ecology_5600",),
}
_CLAIM_LIMITS: dict[str, tuple[str, ...]] = {
    "DC1": ("L1",),
    "DC2": ("L1",),
    "DC3": ("L1", "L5"),
    "DC4": ("L1",),
    "DC5": ("L1", "L2"),
}
_CLAIM_RULES: tuple[str, ...] = (
    "forbidden_terms", "read_only_layer",
)
# Claims born from resolving the wild-explorer / governor
# tension carry an explicit dissent edge.
_CLAIM_CONFLICTS: dict[str, tuple[str, ...]] = {
    "DC2": ("wild_vs_governor",),
    "DC3": ("wild_vs_governor",),
}

# metric_name -> producing sprint and supported claim.
_METRIC_SPRINT: dict[str, str] = {
    "redundancy_reduction": "v19.1",
    "novelty_gain": "v21.0",
    "exploration_diversity": "v20.2",
    "residual_hallucination": "v20.1",
    "authority_drift": "v20.3",
    "capture_resistance": "v20.3",
    "productivity_gain": "v21.0",
    "replay_stability": "v22.4",
}
_METRIC_SUPPORTS: dict[str, str] = {
    "redundancy_reduction": "DC1",
    "novelty_gain": "DC3",
    "exploration_diversity": "DC5",
    "residual_hallucination": "DC2",
    "authority_drift": "DC5",
    "capture_resistance": "DC5",
    "productivity_gain": "DC3",
    "replay_stability": "DC1",
}

_ARTIFACT_SPRINT: dict[str, str] = {
    "v23_0_anchoring": "v23.0",
    "v23_1_conditions": "v23.1",
    "v23_2_density": "v23.2",
    "v23_3_relevance": "v23.3",
    "v23_4_followup_verdict": "v23.4",
    "v24_0_schema": "v24.0",
}

_DISSENT: dict[str, str] = {
    "wild_vs_governor": "Wild Explorer aggression vs governor "
                        "conservatism",
}

_ECOLOGY: dict[str, str] = {
    "v20_3_5600": "v20.3 long-horizon dual-agent ecology "
                  "(5600 steps)",
}


def _replay_value(sprint: str) -> str:
    return hashlib.sha256(
        f"replay::{sprint}".encode("utf-8"),
    ).hexdigest()[:16]


def _claim_sprints(sprint_source: str) -> tuple[str, ...]:
    return tuple(sorted(set(_SPRINT_RE.findall(sprint_source))))


def _construct() -> tuple[tuple[Node, ...], tuple[Edge, ...]]:
    nodes: dict[str, Node] = {}
    edges: set[Edge] = set()

    def add_node(node_id: str, ntype: NodeType, label: str) -> str:
        if node_id not in nodes:
            nodes[node_id] = Node(node_id, ntype.value, label)
        return node_id

    def add_edge(src: str, dst: str, etype) -> None:
        edges.add(Edge(src, dst, etype.value))

    from .edges import EdgeType as E

    # methods / fixtures / rules / limitations
    for slug, label in _METHODS.items():
        add_node(f"method:{slug}", NodeType.METHOD, label)
    for slug, label in _FIXTURES.items():
        add_node(f"fixture:{slug}", NodeType.FIXTURE, label)
    for slug, label in _RULES.items():
        add_node(f"rule:{slug}", NodeType.GOVERNANCE_RULE, label)
    for limit in sandbox_limits():
        add_node(
            f"limitation:{limit.limit_id}",
            NodeType.LIMITATION, limit.statement,
        )

    # every method is itself governed (read-only / no hidden
    # authority); fixtures are scoped by the sandbox limits
    for slug in _METHODS:
        add_edge(f"method:{slug}", "rule:read_only_layer",
                 E.GOVERNED_BY)
        add_edge(f"method:{slug}", "rule:no_hidden_authority",
                 E.GOVERNED_BY)
    add_edge("fixture:synthetic_trajectories", "limitation:L1",
             E.LIMITED_BY)
    add_edge("fixture:ecology_5600", "limitation:L2",
             E.LIMITED_BY)

    sprints_needed: set[str] = set()

    # claims (live) + their provenance
    for c in claims():
        cid = f"claim:{c.claim_id}"
        add_node(cid, NodeType.CLAIM, c.text)
        for sp in _claim_sprints(c.sprint_source):
            sprints_needed.add(sp)
            add_edge(cid, f"sprint:{sp}", E.GENERATED_IN)
        for m in _CLAIM_METHODS.get(c.claim_id, ()):  # methods
            add_edge(cid, f"method:{m}", E.DERIVED_FROM)
        for fx in _CLAIM_FIXTURES.get(c.claim_id, ()):
            add_edge(cid, f"fixture:{fx}", E.DERIVED_FROM)
        for lm in _CLAIM_LIMITS.get(c.claim_id, ()):
            add_edge(cid, f"limitation:{lm}", E.LIMITED_BY)
        for ru in _CLAIM_RULES:
            add_edge(cid, f"rule:{ru}", E.GOVERNED_BY)
        first = _claim_sprints(c.sprint_source)[0]
        add_edge(cid, f"replayhash:{first}", E.VALIDATED_BY)
        for d in _CLAIM_CONFLICTS.get(c.claim_id, ()):
            add_edge(cid, f"dissent:{d}", E.CONFLICTS_WITH)

    # metrics (definitions only - no recomputed values)
    defined = {d.name for d in definitions()}
    for name in sorted(defined):
        mid = f"metric:{name}"
        add_node(mid, NodeType.METRIC, name)
        sp = _METRIC_SPRINT.get(name)
        if sp:
            sprints_needed.add(sp)
            add_edge(mid, f"sprint:{sp}", E.GENERATED_IN)
            add_edge(mid, f"replayhash:{sp}", E.REPLAYED_AS)
        sup = _METRIC_SUPPORTS.get(name)
        if sup:
            add_edge(mid, f"claim:{sup}", E.SUPPORTS)

    # artifacts
    for art, sp in _ARTIFACT_SPRINT.items():
        sprints_needed.add(sp)
        aid = f"artifact:{art}"
        add_node(aid, NodeType.ARTIFACT, art)
        add_edge(aid, f"sprint:{sp}", E.GENERATED_IN)
        add_edge(aid, f"replayhash:{sp}", E.VALIDATED_BY)

    # dissent path + ecology run
    for slug, label in _DISSENT.items():
        did = f"dissent:{slug}"
        add_node(did, NodeType.DISSENT_PATH, label)
        add_edge(did, "rule:forbidden_terms", E.GOVERNED_BY)
    for slug, label in _ECOLOGY.items():
        eid = f"ecology:{slug}"
        add_node(eid, NodeType.ECOLOGY_RUN, label)
        sprints_needed.add("v20.3")
        add_edge(eid, "sprint:v20.3", E.GENERATED_IN)
        add_edge(eid, "replayhash:v20.3", E.VALIDATED_BY)

    # sprints + replay hashes (one hash per sprint)
    for sp in sprints_needed:
        add_node(f"sprint:{sp}", NodeType.SPRINT, sp)
        rid = f"replayhash:{sp}"
        add_node(rid, NodeType.REPLAY_HASH, _replay_value(sp))
        add_edge(f"sprint:{sp}", rid, E.REPLAYED_AS)
        add_edge(rid, "fixture:synthetic_trajectories",
                 E.INVALIDATED_BY)

    node_tuple = tuple(
        sorted(nodes.values(), key=lambda n: n.sort_key())
    )
    edge_tuple = tuple(
        sorted(edges, key=lambda e: e.sort_key())
    )
    return node_tuple, edge_tuple


@lru_cache(maxsize=1)
def _build() -> tuple[tuple[Node, ...], tuple[Edge, ...]]:
    return _construct()


def _signature_of(
    pair: tuple[tuple[Node, ...], tuple[Edge, ...]],
) -> str:
    n, e = pair
    parts = [f"N|{x.node_type}|{x.node_id}" for x in n]
    parts += [
        f"E|{x.edge_type}|{x.source}|{x.target}" for x in e
    ]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def determinism_signatures() -> tuple[str, str]:
    """Two independent from-scratch builds, for the determinism
    check (bypasses the cache)."""
    return (
        _signature_of(_construct()),
        _signature_of(_construct()),
    )


def nodes() -> tuple[Node, ...]:
    return _build()[0]


def edges() -> tuple[Edge, ...]:
    return _build()[1]


def _node_types() -> dict[str, str]:
    return {n.node_id: n.node_type for n in nodes()}


def nodes_of_type(node_type: str) -> tuple[Node, ...]:
    return tuple(n for n in nodes() if n.node_type == node_type)


def edges_of_type(edge_type: str) -> tuple[Edge, ...]:
    return tuple(e for e in edges() if e.edge_type == edge_type)


def out_edges(node_id: str) -> tuple[Edge, ...]:
    return tuple(e for e in edges() if e.source == node_id)


def lineage_of(node_id: str) -> tuple[Edge, ...]:
    """Direct provenance edges out of a node, sorted."""
    return out_edges(node_id)


def claim_lineage_visible(claim_id: str) -> bool:
    """A claim has visible lineage iff it is generated in a
    sprint, derived from a method/fixture, validated by a
    replay hash, scoped by a limitation and governed by a
    rule."""
    cid = f"claim:{claim_id}"
    kinds = {e.edge_type for e in out_edges(cid)}
    return {
        "GENERATED_IN", "DERIVED_FROM", "VALIDATED_BY",
        "LIMITED_BY", "GOVERNED_BY",
    }.issubset(kinds)


def graph_signature() -> str:
    return _signature_of(_build())


__all__ = [
    "claim_lineage_visible",
    "determinism_signatures",
    "edges",
    "edges_of_type",
    "graph_signature",
    "lineage_of",
    "nodes",
    "nodes_of_type",
    "out_edges",
]
