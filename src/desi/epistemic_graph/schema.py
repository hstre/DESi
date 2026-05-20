"""v24.0 - epistemic graph schema.

Declares which (source_type, edge_type, target_type) triples
are well-formed. The schema is closed: an edge whose endpoints
do not match an allowed triple is a schema violation. This is
purely structural validation - it never decides or ranks.
"""
from __future__ import annotations

from .edges import EDGE_TYPES, EdgeType
from .nodes import NODE_TYPES, NodeType

_N = NodeType
_E = EdgeType

# Closed set of allowed (source_type, edge_type, target_type).
_ALLOWED_TRIPLES: tuple[tuple[str, str, str], ...] = (
    (_N.CLAIM.value, _E.DERIVED_FROM.value, _N.METHOD.value),
    (_N.CLAIM.value, _E.DERIVED_FROM.value, _N.FIXTURE.value),
    (_N.CLAIM.value, _E.GENERATED_IN.value, _N.SPRINT.value),
    (_N.CLAIM.value, _E.VALIDATED_BY.value, _N.REPLAY_HASH.value),
    (_N.CLAIM.value, _E.LIMITED_BY.value, _N.LIMITATION.value),
    (_N.CLAIM.value, _E.GOVERNED_BY.value,
     _N.GOVERNANCE_RULE.value),
    (_N.CLAIM.value, _E.CONFLICTS_WITH.value, _N.CLAIM.value),
    (_N.CLAIM.value, _E.CONFLICTS_WITH.value,
     _N.DISSENT_PATH.value),
    (_N.METRIC.value, _E.SUPPORTS.value, _N.CLAIM.value),
    (_N.METRIC.value, _E.GENERATED_IN.value, _N.SPRINT.value),
    (_N.METRIC.value, _E.REPLAYED_AS.value,
     _N.REPLAY_HASH.value),
    (_N.ARTIFACT.value, _E.GENERATED_IN.value, _N.SPRINT.value),
    (_N.ARTIFACT.value, _E.VALIDATED_BY.value,
     _N.REPLAY_HASH.value),
    (_N.SPRINT.value, _E.REPLAYED_AS.value,
     _N.REPLAY_HASH.value),
    (_N.REPLAY_HASH.value, _E.INVALIDATED_BY.value,
     _N.FIXTURE.value),
    (_N.ECOLOGY_RUN.value, _E.GENERATED_IN.value,
     _N.SPRINT.value),
    (_N.ECOLOGY_RUN.value, _E.VALIDATED_BY.value,
     _N.REPLAY_HASH.value),
    (_N.DISSENT_PATH.value, _E.GOVERNED_BY.value,
     _N.GOVERNANCE_RULE.value),
    (_N.METHOD.value, _E.GOVERNED_BY.value,
     _N.GOVERNANCE_RULE.value),
    (_N.FIXTURE.value, _E.LIMITED_BY.value, _N.LIMITATION.value),
)


def allowed_triples() -> tuple[tuple[str, str, str], ...]:
    return _ALLOWED_TRIPLES


def is_valid_triple(
    source_type: str, edge_type: str, target_type: str,
) -> bool:
    return (
        source_type, edge_type, target_type,
    ) in _ALLOWED_TRIPLES


def required_node_types() -> tuple[str, ...]:
    return NODE_TYPES


def required_edge_types() -> tuple[str, ...]:
    return EDGE_TYPES


def schema_signature() -> str:
    import hashlib
    parts = ["|".join(t) for t in _ALLOWED_TRIPLES]
    return hashlib.sha256(
        "\n".join(sorted(parts)).encode("utf-8"),
    ).hexdigest()


__all__ = [
    "allowed_triples",
    "is_valid_triple",
    "required_edge_types",
    "required_node_types",
    "schema_signature",
]
