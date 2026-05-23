"""v24.1 - optional Neo4j client.

IMPORTANT: this module must import cleanly whether or not the
`neo4j` driver is installed. The `neo4j` package is imported
lazily, only inside `connect`. DESi never reads anything back
from Neo4j to steer itself - the only direction is DESi -> graph
(write provenance). Tests use the offline DryRunClient and never
require a live database.
"""
from __future__ import annotations

from dataclasses import dataclass, field


class Neo4jUnavailableError(RuntimeError):
    """Raised when a real Neo4j driver is requested but the
    `neo4j` package is not installed."""


def neo4j_available() -> bool:
    try:
        import neo4j  # noqa: F401
    except Exception:
        return False
    return True


@dataclass
class DryRunClient:
    """Offline client that records the statements it would run
    without touching any database. Deterministic and dependency
    free, so the export path works (and is testable) with no
    Neo4j present."""

    statements: list[tuple[str, dict]] = field(
        default_factory=list,
    )
    # DESi only ever writes provenance; it never queries the
    # graph back into a decision. Kept explicit as a guard.
    read_only_from_desi: bool = True

    def run(
        self, statement: str, params: dict | None = None,
    ) -> None:
        self.statements.append((statement, dict(params or {})))

    def executed(self) -> tuple[tuple[str, dict], ...]:
        return tuple(self.statements)

    def reset(self) -> None:
        self.statements.clear()


def connect(uri: str, user: str, password: str):
    """Return a real Neo4j driver. Only callable when the
    `neo4j` package is installed (e.g. the GitHub Actions
    service container). Never used by the test suite."""
    if not neo4j_available():
        raise Neo4jUnavailableError(
            "the neo4j package is not installed; use "
            "DryRunClient for offline, replay-safe export",
        )
    import neo4j

    return neo4j.GraphDatabase.driver(uri, auth=(user, password))


__all__ = [
    "DryRunClient",
    "Neo4jUnavailableError",
    "connect",
    "neo4j_available",
]
