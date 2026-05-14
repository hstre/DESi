"""Read-only memory access surface for operators.

Operators receive a :class:`ReadOnlyMemoryView`, never a :class:`MemoryStore`
or a :class:`MemoryRecorder`. The view exposes only read methods; there is
no path through this class to writes. The contract from v0.1 was social
("operators must not modify memory"); the contract in v0.2 is technical
("operators *cannot* modify memory because their reference has no write
methods").

Python is not type-airtight — a determined caller can reach the wrapped
store via attribute access — but the standard mypy / IDE surface and
the public API do not expose any write path. This is consistent with
how Python codebases enforce read-only contracts everywhere else.
"""
from __future__ import annotations

import re
from typing import Iterator

from .claim import Claim
from .events import OperatorEvent
from .relations import RelationType
from .store import MemoryStore


_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in _WORD_RE.finditer(text)}


class ReadOnlyMemoryView:
    """Read-only window onto the memory store.

    Operators are handed a ReadOnlyMemoryView. The view provides:

    * ``get_claim(claim_id)``         — fetch by id
    * ``find_related(claim_id)``      — claims linked by a relation
    * ``find_similar(content)``       — lexical-similarity stub (NO embeddings)
    * ``get_branch_history(...)``     — derivation chain for a claim
    * ``get_operator_history(...)``   — past events for an operator name

    There is intentionally no ``add_*`` / ``record_*`` / ``update_*``
    method. The wrapped store is private.
    """

    # The leading double underscore triggers Python's name-mangling.
    # Callers cannot reach the store via ``view._store`` without
    # going through ``view._ReadOnlyMemoryView__store`` — which makes
    # the intent visible in any code review.
    __slots__ = ("__store",)

    def __init__(self, store: MemoryStore) -> None:
        object.__setattr__(self, "_ReadOnlyMemoryView__store", store)

    # No __setattr__ override is needed; the slot is private and the
    # class has no public mutation methods at all.

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def get_claim(self, claim_id: str) -> Claim | None:
        return self.__store.get_claim(claim_id)

    def find_related(
        self,
        claim_id: str,
        *,
        rel_type: RelationType | None = None,
        direction: str = "out",
    ) -> list[Claim]:
        """Return the claims linked to ``claim_id`` by a relation.

        ``direction`` matches the underlying store semantics: ``out``
        returns targets of edges starting at ``claim_id``; ``in``
        returns sources of edges ending at ``claim_id``; ``both``
        returns both sets, deduplicated.
        """
        out: list[Claim] = []
        seen: set[str] = set()
        for rel in self.__store.relations_for(
            claim_id, rel_type=rel_type, direction=direction,
        ):
            other_id = (rel.target_claim_id
                        if rel.source_claim_id == claim_id
                        else rel.source_claim_id)
            if other_id in seen:
                continue
            seen.add(other_id)
            c = self.__store.get_claim(other_id)
            if c is not None:
                out.append(c)
        return out

    def find_similar(
        self,
        content: str,
        *,
        limit: int = 10,
        min_score: float = 0.1,
    ) -> list[Claim]:
        """Lexical-similarity stub.

        v0.2 deliberately ships a lexical Jaccard-on-token-sets score
        rather than an embedding or vector search (those are out of
        scope per the v0.2 directive). The score is
        ``|tokens_a ∩ tokens_b| / |tokens_a ∪ tokens_b|``. Returns the
        top ``limit`` claims with score ≥ ``min_score`` sorted by
        score descending.
        """
        query_tokens = _tokens(content)
        if not query_tokens:
            return []
        scored: list[tuple[float, Claim]] = []
        for claim in self.__store.all_claims():
            other = _tokens(claim.content)
            if not other:
                continue
            inter = len(query_tokens & other)
            union = len(query_tokens | other)
            if union == 0:
                continue
            score = inter / union
            if score >= min_score:
                scored.append((score, claim))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [c for _score, c in scored[:limit]]

    def get_branch_history(self, claim_id: str) -> list[Claim]:
        """Walk the derivation chain upstream from a claim.

        Follows ``DERIVES_FROM``, ``MERGED_INTO``, and ``SPLIT_FROM``
        relations backwards (out direction from the claim) and returns
        the chain of ancestor claims in walk order. Returns an empty
        list if the starting claim has no derivation edges. The walk
        is depth-first and cycle-safe.
        """
        history: list[Claim] = []
        visited: set[str] = {claim_id}
        stack: list[str] = [claim_id]
        derivation_kinds = {
            RelationType.DERIVES_FROM,
            RelationType.MERGED_INTO,
            RelationType.SPLIT_FROM,
        }
        while stack:
            current = stack.pop()
            for rel in self.__store.relations_for(current, direction="out"):
                if rel.rel_type not in derivation_kinds:
                    continue
                if rel.target_claim_id in visited:
                    continue
                visited.add(rel.target_claim_id)
                ancestor = self.__store.get_claim(rel.target_claim_id)
                if ancestor is not None:
                    history.append(ancestor)
                    stack.append(rel.target_claim_id)
        return history

    def get_operator_history(
        self,
        operator_name: str,
        *,
        run_id: str | None = None,
    ) -> list[OperatorEvent]:
        """Return past ``OperatorEvent`` records for ``operator_name``.

        If ``run_id`` is given, restrict to events from that run. If
        not, return events from every recorded run that match the
        operator name. Order is insertion order from the underlying
        store — the recorder writes in loop order, so this is
        chronological for a single run.
        """
        out: list[OperatorEvent] = []
        if run_id is not None:
            run_ids: Iterator[str] = iter([run_id])
        else:
            # The protocol does not expose ``all_runs``; in v0.2 the
            # caller passes run_id, or the recorder maintains the
            # list. For the run-agnostic call we read directly from
            # the store's internal state via a defensive iteration:
            # ``relations_for`` does not list runs, but we can ask
            # the store for events of each known run via a private
            # helper. To stay protocol-clean, we provide the
            # generator below that walks all stored events through a
            # public iteration helper added on the store.
            run_ids = _iter_run_ids(self.__store)
        for rid in run_ids:
            for ev in self.__store.events_for_run(rid):
                if ev.operator_code == operator_name:
                    out.append(ev)
        return out


def _iter_run_ids(store: MemoryStore) -> Iterator[str]:
    """Yield every known run id.

    Tries the concrete-store accessor first; falls back to the
    protocol's empty default so this function does not crash on a
    store that does not implement run-listing. The
    :class:`InMemoryStore` exposes ``_runs.keys()`` directly; the
    Neo4j store exposes nothing equivalent in v0.2 and so returns
    no run ids — callers must pass an explicit ``run_id`` for
    ``get_operator_history`` against Neo4j.
    """
    runs = getattr(store, "_runs", None)
    if isinstance(runs, dict):
        yield from list(runs.keys())
