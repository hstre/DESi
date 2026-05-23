"""Idempotent Neo4j schema migrations for the DESi memory layer.

Migrations run once per cold start. The current set creates UNIQUE
constraints on the three node-identity properties and optional indices
on the most-queried claim properties. ``CREATE CONSTRAINT IF NOT
EXISTS`` and ``CREATE INDEX IF NOT EXISTS`` are Neo4j 4.4+ syntax;
both forms are idempotent — running migrations a second time is a
no-op.

Migrations do not touch :class:`InMemoryStore` because that store has
no schema. Calling :func:`run_migrations` with an InMemoryStore is a
no-op rather than an error so that test code that runs against both
backends does not have to branch.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .store import InMemoryStore, MemoryStore, Neo4jStore


@dataclass(frozen=True)
class Migration:
    """A single Cypher statement plus a stable identifier."""

    name: str
    cypher: str


# Required constraints. The triple-set is the load-bearing v0.2
# invariant: each node-kind's identity property is unique.
REQUIRED_CONSTRAINTS: tuple[Migration, ...] = (
    Migration(
        name="claim_id_unique",
        cypher=(
            "CREATE CONSTRAINT claim_id_unique IF NOT EXISTS "
            "FOR (c:Claim) REQUIRE c.claim_id IS UNIQUE"
        ),
    ),
    Migration(
        name="run_id_unique",
        cypher=(
            "CREATE CONSTRAINT run_id_unique IF NOT EXISTS "
            "FOR (r:Run) REQUIRE r.run_id IS UNIQUE"
        ),
    ),
    Migration(
        name="event_id_unique",
        cypher=(
            "CREATE CONSTRAINT event_id_unique IF NOT EXISTS "
            "FOR (e:OperatorEvent) REQUIRE e.event_id IS UNIQUE"
        ),
    ),
)

# Optional indices for read-heavy queries. The v0.2 directive lists
# state, method, and timestamp as the three candidate indices.
OPTIONAL_INDICES: tuple[Migration, ...] = (
    Migration(
        name="claim_state_idx",
        cypher=(
            "CREATE INDEX claim_state_idx IF NOT EXISTS "
            "FOR (c:Claim) ON (c.state)"
        ),
    ),
    Migration(
        name="claim_method_idx",
        cypher=(
            "CREATE INDEX claim_method_idx IF NOT EXISTS "
            "FOR (c:Claim) ON (c.method)"
        ),
    ),
    Migration(
        name="claim_timestamp_idx",
        cypher=(
            "CREATE INDEX claim_timestamp_idx IF NOT EXISTS "
            "FOR (c:Claim) ON (c.prov_timestamp)"
        ),
    ),
)


def run_migrations(
    store: MemoryStore,
    *,
    include_optional_indices: bool = True,
    extra: Sequence[Migration] = (),
) -> list[str]:
    """Apply all required migrations + optional indices to a Neo4j store.

    Returns the list of migration names that were issued (every name
    appears exactly once per invocation; CREATE ... IF NOT EXISTS
    makes the underlying Cypher idempotent so repeat calls do not
    error).

    Calling this against an :class:`InMemoryStore` is a no-op and
    returns an empty list. This keeps test rigs portable between
    backends.
    """
    if isinstance(store, InMemoryStore):
        return []
    if not isinstance(store, Neo4jStore):
        # Defensive — protocol-conforming stores that are not the two
        # shipped impls cannot get useful constraints applied.
        return []
    issued: list[str] = []
    for migration in _all_migrations(include_optional_indices, extra):
        with store._runner() as session:  # type: ignore[attr-defined]
            session.run(migration.cypher)
        issued.append(migration.name)
    return issued


def list_migrations(
    *,
    include_optional_indices: bool = True,
    extra: Sequence[Migration] = (),
) -> list[Migration]:
    """Return the ordered list of migrations ``run_migrations`` would issue."""
    return list(_all_migrations(include_optional_indices, extra))


def _all_migrations(
    include_optional_indices: bool,
    extra: Sequence[Migration],
) -> Iterable[Migration]:
    yield from REQUIRED_CONSTRAINTS
    if include_optional_indices:
        yield from OPTIONAL_INDICES
    yield from extra
