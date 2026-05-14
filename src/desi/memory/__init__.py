"""Optional memory layer for DESi.

This package is intentionally **observation-only** in v0.1. Guards may read
from the memory store; operators must not modify their behaviour based on
memory state. The contract is reproducibility, not self-modification.

The public surface is the :class:`MemoryStore` protocol plus the two
shipped implementations:

* :class:`InMemoryStore` — dictionary-backed, zero dependencies, deterministic.
* :class:`Neo4jStore`    — optional, requires the ``neo4j`` driver package.

Neither implementation is imported from the rest of DESi. Importing
``desi.memory`` is safe on a host with no Neo4j driver installed and no
running database: the ``Neo4jStore`` symbol exists either way; calls that
need the driver raise :class:`Neo4jDriverNotInstalled` rather than crashing
at import time.
"""
from __future__ import annotations

from .claim import (
    Claim,
    ClaimState,
    Provenance,
)
from .events import OperatorEvent, Run
from .relations import RELATION_TYPES, Relation, RelationType
from .store import (
    InMemoryStore,
    MemoryStore,
    Neo4jDriverNotInstalled,
    Neo4jStore,
)

__all__ = [
    "Claim",
    "ClaimState",
    "InMemoryStore",
    "MemoryStore",
    "Neo4jDriverNotInstalled",
    "Neo4jStore",
    "OperatorEvent",
    "Provenance",
    "RELATION_TYPES",
    "Relation",
    "RelationType",
    "Run",
]
