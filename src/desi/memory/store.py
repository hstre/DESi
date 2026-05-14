"""Memory store implementations.

This module defines the :class:`MemoryStore` protocol and two concrete
implementations:

* :class:`InMemoryStore` — dictionary-backed, no external dependencies.
  Suitable for tests and for running DESi without a database.
* :class:`Neo4jStore`    — Neo4j-backed. Requires the optional ``neo4j``
  driver package. Importing this module does **not** require neo4j;
  instantiating ``Neo4jStore`` does.

The store is observation-only by contract: it has read and write methods
but no mutation hooks for operators. Guards may consult the store; they
must not pass references back to operators that could trigger feedback
loops. This contract is enforced socially, not technically — see
``docs/memory/observation_only_contract.md`` for the rationale.
"""
from __future__ import annotations

from typing import Any, Iterator, Protocol, runtime_checkable

from .claim import Claim
from .events import OperatorEvent, Run
from .relations import Relation, RelationType


class Neo4jDriverNotInstalled(RuntimeError):
    """Raised when :class:`Neo4jStore` is instantiated without the driver."""


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class MemoryStore(Protocol):
    """The minimum interface a memory store must support.

    The protocol is intentionally narrow. Bulk operations and advanced
    queries belong on subclasses; the protocol is what guards may rely
    on without depending on a concrete implementation.
    """

    # Claims
    def add_claim(self, claim: Claim) -> None: ...
    def get_claim(self, claim_id: str) -> Claim | None: ...
    def all_claims(self) -> Iterator[Claim]: ...

    # Relations
    def add_relation(self, rel: Relation) -> None: ...
    def relations_for(
        self,
        claim_id: str,
        *,
        rel_type: RelationType | None = None,
        direction: str = "out",
    ) -> Iterator[Relation]: ...

    # Runs and events
    def add_run(self, run: Run) -> None: ...
    def get_run(self, run_id: str) -> Run | None: ...
    def add_event(self, event: OperatorEvent) -> None: ...
    def events_for_run(self, run_id: str) -> Iterator[OperatorEvent]: ...

    # Lifecycle
    def close(self) -> None: ...


# ---------------------------------------------------------------------------
# In-memory implementation
# ---------------------------------------------------------------------------


class InMemoryStore:
    """Dictionary-backed memory store.

    Behaviour mirrors what the Neo4j store guarantees: insertion is
    idempotent on ``claim_id`` (re-adding the same claim overwrites);
    relations are stored as (source, target, rel_type) triples; queries
    return iterators in insertion order.
    """

    def __init__(self) -> None:
        self._claims: dict[str, Claim] = {}
        self._relations: list[Relation] = []
        self._runs: dict[str, Run] = {}
        self._events: dict[str, OperatorEvent] = {}

    # Claims --------------------------------------------------------------

    def add_claim(self, claim: Claim) -> None:
        self._claims[claim.claim_id] = claim

    def get_claim(self, claim_id: str) -> Claim | None:
        return self._claims.get(claim_id)

    def all_claims(self) -> Iterator[Claim]:
        return iter(list(self._claims.values()))

    # Relations -----------------------------------------------------------

    def add_relation(self, rel: Relation) -> None:
        self._relations.append(rel)

    def relations_for(
        self,
        claim_id: str,
        *,
        rel_type: RelationType | None = None,
        direction: str = "out",
    ) -> Iterator[Relation]:
        if direction not in {"out", "in", "both"}:
            raise ValueError(f"direction must be out/in/both, not {direction}")
        for r in self._relations:
            if rel_type is not None and r.rel_type is not rel_type:
                continue
            if direction == "out" and r.source_claim_id == claim_id:
                yield r
            elif direction == "in" and r.target_claim_id == claim_id:
                yield r
            elif direction == "both" and (
                r.source_claim_id == claim_id
                or r.target_claim_id == claim_id
            ):
                yield r

    # Runs and events -----------------------------------------------------

    def add_run(self, run: Run) -> None:
        self._runs[run.run_id] = run

    def get_run(self, run_id: str) -> Run | None:
        return self._runs.get(run_id)

    def add_event(self, event: OperatorEvent) -> None:
        self._events[event.event_id] = event

    def events_for_run(self, run_id: str) -> Iterator[OperatorEvent]:
        for ev in self._events.values():
            if ev.run_id == run_id:
                yield ev

    # Lifecycle -----------------------------------------------------------

    def close(self) -> None:
        # Nothing to release; the method exists so callers can write
        # ``store.close()`` against the protocol without branching.
        return None


# ---------------------------------------------------------------------------
# Neo4j implementation (optional)
# ---------------------------------------------------------------------------


# The neo4j import is gated. The module loads successfully without it;
# only ``Neo4jStore.__init__`` enforces the dependency.
try:  # pragma: no cover — guarded import
    from neo4j import GraphDatabase  # type: ignore[import-not-found]
    _NEO4J_AVAILABLE = True
except ImportError:  # pragma: no cover
    GraphDatabase = None  # type: ignore[assignment]
    _NEO4J_AVAILABLE = False


class Neo4jStore:
    """Neo4j-backed memory store.

    The driver is passed in (or constructed from a URI). Tests inject a
    mock driver to exercise the Cypher contract without a running
    database.
    """

    NODE_CLAIM = "Claim"
    NODE_RUN = "Run"
    NODE_EVENT = "OperatorEvent"

    def __init__(
        self,
        *,
        uri: str | None = None,
        auth: tuple[str, str] | None = None,
        driver: Any | None = None,
        database: str = "neo4j",
    ) -> None:
        """Construct a Neo4jStore.

        Either ``driver`` is provided directly (used by tests with a mock)
        or ``uri`` plus ``auth`` are provided and the driver is built.
        Constructing without a driver and without the neo4j package
        installed raises :class:`Neo4jDriverNotInstalled`.
        """
        if driver is None:
            if uri is None:
                raise ValueError("Either driver or uri must be provided.")
            if not _NEO4J_AVAILABLE:
                raise Neo4jDriverNotInstalled(
                    "The 'neo4j' driver package is not installed. Install "
                    "it with `pip install neo4j` or use InMemoryStore."
                )
            driver = GraphDatabase.driver(uri, auth=auth)
        self._driver = driver
        self._database = database

    # Claims --------------------------------------------------------------

    def add_claim(self, claim: Claim) -> None:
        rec = claim.to_record()
        cypher = (
            f"MERGE (c:{self.NODE_CLAIM} {{claim_id: $claim_id}}) "
            "SET c += $props"
        )
        with self._driver.session(database=self._database) as s:
            s.run(cypher, claim_id=claim.claim_id, props=rec)

    def get_claim(self, claim_id: str) -> Claim | None:
        cypher = (
            f"MATCH (c:{self.NODE_CLAIM} {{claim_id: $claim_id}}) "
            "RETURN c"
        )
        with self._driver.session(database=self._database) as s:
            result = s.run(cypher, claim_id=claim_id)
            row = result.single()
        if row is None:
            return None
        node = row["c"]
        # neo4j Node behaves like a Mapping over its properties; mock
        # tests pass a plain dict.
        rec = dict(node) if not isinstance(node, dict) else node
        return Claim.from_record(rec)

    def all_claims(self) -> Iterator[Claim]:
        cypher = f"MATCH (c:{self.NODE_CLAIM}) RETURN c"
        with self._driver.session(database=self._database) as s:
            result = s.run(cypher)
            rows = list(result)
        for row in rows:
            node = row["c"]
            rec = dict(node) if not isinstance(node, dict) else node
            yield Claim.from_record(rec)

    # Relations -----------------------------------------------------------

    def add_relation(self, rel: Relation) -> None:
        cypher = (
            f"MATCH (s:{self.NODE_CLAIM} {{claim_id: $source_id}}), "
            f"(t:{self.NODE_CLAIM} {{claim_id: $target_id}}) "
            f"MERGE (s)-[r:{rel.rel_type.value}]->(t) "
            "SET r.weight = $weight, r.created_at = $created_at"
        )
        rec = rel.to_record()
        with self._driver.session(database=self._database) as s:
            s.run(
                cypher,
                source_id=rel.source_claim_id,
                target_id=rel.target_claim_id,
                weight=rec["weight"],
                created_at=rec["created_at"],
            )

    def relations_for(
        self,
        claim_id: str,
        *,
        rel_type: RelationType | None = None,
        direction: str = "out",
    ) -> Iterator[Relation]:
        if direction not in {"out", "in", "both"}:
            raise ValueError(f"direction must be out/in/both, not {direction}")
        type_filter = f":{rel_type.value}" if rel_type else ""
        if direction == "out":
            pat = (
                f"MATCH (s:{self.NODE_CLAIM} {{claim_id: $cid}})"
                f"-[r{type_filter}]->(t:{self.NODE_CLAIM})"
            )
        elif direction == "in":
            pat = (
                f"MATCH (s:{self.NODE_CLAIM})"
                f"-[r{type_filter}]->(t:{self.NODE_CLAIM} {{claim_id: $cid}})"
            )
        else:
            pat = (
                f"MATCH (s:{self.NODE_CLAIM})"
                f"-[r{type_filter}]-(t:{self.NODE_CLAIM}) "
                "WHERE s.claim_id = $cid OR t.claim_id = $cid"
            )
        cypher = pat + " RETURN s.claim_id AS s, t.claim_id AS t, " \
                       "type(r) AS rt, r.weight AS w, r.created_at AS c"
        with self._driver.session(database=self._database) as s:
            result = s.run(cypher, cid=claim_id)
            rows = list(result)
        for row in rows:
            yield Relation.from_record({
                "source_claim_id": row["s"],
                "target_claim_id": row["t"],
                "rel_type": row["rt"],
                "weight": row["w"],
                "created_at": row["c"],
            })

    # Runs and events -----------------------------------------------------

    def add_run(self, run: Run) -> None:
        rec = run.to_record()
        cypher = (
            f"MERGE (r:{self.NODE_RUN} {{run_id: $run_id}}) SET r += $props"
        )
        with self._driver.session(database=self._database) as s:
            s.run(cypher, run_id=run.run_id, props=rec)

    def get_run(self, run_id: str) -> Run | None:
        cypher = f"MATCH (r:{self.NODE_RUN} {{run_id: $run_id}}) RETURN r"
        with self._driver.session(database=self._database) as s:
            row = s.run(cypher, run_id=run_id).single()
        if row is None:
            return None
        node = row["r"]
        rec = dict(node) if not isinstance(node, dict) else node
        return Run.from_record(rec)

    def add_event(self, event: OperatorEvent) -> None:
        rec = event.to_record()
        cypher = (
            f"MATCH (r:{self.NODE_RUN} {{run_id: $run_id}}) "
            f"MERGE (e:{self.NODE_EVENT} {{event_id: $event_id}}) "
            "SET e += $props "
            "MERGE (r)-[:PRODUCED]->(e)"
        )
        with self._driver.session(database=self._database) as s:
            s.run(
                cypher,
                run_id=event.run_id,
                event_id=event.event_id,
                props=rec,
            )

    def events_for_run(self, run_id: str) -> Iterator[OperatorEvent]:
        cypher = (
            f"MATCH (r:{self.NODE_RUN} {{run_id: $run_id}})"
            f"-[:PRODUCED]->(e:{self.NODE_EVENT}) RETURN e "
            "ORDER BY e.loop_index ASC"
        )
        with self._driver.session(database=self._database) as s:
            rows = list(s.run(cypher, run_id=run_id))
        for row in rows:
            node = row["e"]
            rec = dict(node) if not isinstance(node, dict) else node
            yield OperatorEvent.from_record(rec)

    # Lifecycle -----------------------------------------------------------

    def close(self) -> None:
        close_fn = getattr(self._driver, "close", None)
        if callable(close_fn):
            close_fn()
