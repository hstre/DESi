"""Tests for the Neo4j schema migrations."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any

import pytest

from desi.memory import (
    InMemoryStore,
    Migration,
    Neo4jStore,
    list_migrations,
    run_migrations,
)


class _FakeResult:
    def single(self): return None
    def __iter__(self): return iter([])


class _FakeSession:
    def __init__(self, log: list[str]) -> None:
        self._log = log

    def __enter__(self) -> "_FakeSession": return self
    def __exit__(self, *exc) -> None: return None

    def run(self, cypher: str, **_params: Any) -> _FakeResult:
        self._log.append(" ".join(cypher.split()))
        return _FakeResult()


class _FakeDriver:
    def __init__(self) -> None:
        self.cypher_log: list[str] = []

    @contextmanager
    def session(self, database: str = "neo4j"):
        yield _FakeSession(self.cypher_log)

    def close(self) -> None: ...


# ---------------------------------------------------------------------------
# Coverage of the required migration surface
# ---------------------------------------------------------------------------


def test_list_migrations_contains_three_required_constraints() -> None:
    migs = list_migrations()
    required_names = {m.name for m in migs}
    for required in ("claim_id_unique", "run_id_unique", "event_id_unique"):
        assert required in required_names


def test_list_migrations_contains_optional_indices_by_default() -> None:
    migs = list_migrations()
    optional_names = {m.name for m in migs}
    for opt in ("claim_state_idx", "claim_method_idx", "claim_timestamp_idx"):
        assert opt in optional_names


def test_list_migrations_excludes_indices_when_requested() -> None:
    migs = list_migrations(include_optional_indices=False)
    names = {m.name for m in migs}
    assert "claim_id_unique" in names
    assert "claim_state_idx" not in names


# ---------------------------------------------------------------------------
# Application against a fake Neo4j driver
# ---------------------------------------------------------------------------


def test_run_migrations_issues_all_statements_first_time() -> None:
    driver = _FakeDriver()
    store = Neo4jStore(driver=driver)
    issued = run_migrations(store)
    assert "claim_id_unique" in issued
    assert "run_id_unique" in issued
    assert "event_id_unique" in issued
    # Every Cypher statement contains the idempotent "IF NOT EXISTS"
    # marker, which is what makes repeated runs safe.
    for cypher in driver.cypher_log:
        assert "IF NOT EXISTS" in cypher


def test_run_migrations_is_idempotent() -> None:
    driver = _FakeDriver()
    store = Neo4jStore(driver=driver)
    first = run_migrations(store)
    second = run_migrations(store)
    # The names returned are stable; the Cypher is issued every call
    # (Neo4j short-circuits server-side via "IF NOT EXISTS").
    assert first == second
    assert len(driver.cypher_log) == 2 * len(first)


# ---------------------------------------------------------------------------
# InMemoryStore path
# ---------------------------------------------------------------------------


def test_run_migrations_against_inmemory_store_is_noop() -> None:
    store = InMemoryStore()
    assert run_migrations(store) == []


# ---------------------------------------------------------------------------
# Extension
# ---------------------------------------------------------------------------


def test_extra_migrations_are_appended() -> None:
    driver = _FakeDriver()
    store = Neo4jStore(driver=driver)
    extra = (Migration(
        name="custom_idx",
        cypher="CREATE INDEX custom_idx IF NOT EXISTS "
               "FOR (c:Claim) ON (c.custom_property)",
    ),)
    issued = run_migrations(store, extra=extra)
    assert issued[-1] == "custom_idx"
