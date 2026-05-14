"""MemoryRecorder — the only authorised writer of the memory store.

v0.2 makes the recorder the single seam through which writes enter the
store. Operators do not write; guards do not write; only the recorder
writes. This rule has three consequences:

1. Every write carries a recorder-assigned timestamp and a run scope.
2. Every claim is born inside a run; there are no orphan claims.
3. Merge and split are atomic helpers on the recorder, not free
   functions, so the all-or-nothing contract is enforced where the
   writes are issued.

The recorder exposes :meth:`read_only_view` so that callers receive a
:class:`ReadOnlyMemoryView` — not the store, not the recorder — when
they only need to read.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from .claim import Claim, ClaimState, Provenance
from .events import OperatorEvent, Run
from .relations import Relation, RelationType
from .store import MemoryStore
from .view import ReadOnlyMemoryView


class RecorderError(RuntimeError):
    """Raised when the recorder is asked to do something inconsistent."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _config_hash(config: dict[str, Any] | None) -> str:
    """Deterministic hash of a config dict for run-identity purposes."""
    if not config:
        return ""
    items = sorted((str(k), str(v)) for k, v in config.items())
    raw = "\x00".join(f"{k}={v}" for k, v in items).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


class MemoryRecorder:
    """Central recorder for DESi runs.

    Lifecycle:

    >>> recorder = MemoryRecorder(InMemoryStore())
    >>> run = recorder.start_run(model="claude-opus-4-7", config={"seed": 7})
    >>> claim = recorder.record_claim(content="...", method="T6")
    >>> recorder.record_relation(source=a, target=b,
    ...                          rel_type=RelationType.SUPPORTS)
    >>> recorder.end_run()

    The recorder refuses writes outside of an open run (except for
    ``end_run`` / ``read_only_view``). This keeps the invariant
    ``every claim has a run_id`` enforceable in storage.
    """

    def __init__(self, store: MemoryStore) -> None:
        self._store = store
        self._active_run: Run | None = None
        self._loop_index: int = 0

    # ------------------------------------------------------------------
    # Read-only handle
    # ------------------------------------------------------------------

    def read_only_view(self) -> ReadOnlyMemoryView:
        """Return a read-only window onto this recorder's store.

        Pass this object to operators. Operators must not receive the
        recorder or the store directly.
        """
        return ReadOnlyMemoryView(self._store)

    # ------------------------------------------------------------------
    # Run lifecycle
    # ------------------------------------------------------------------

    def start_run(
        self,
        *,
        run_id: str | None = None,
        model: str,
        config: dict[str, Any] | None = None,
        prompt_hash: str | None = None,
        label: str = "",
    ) -> Run:
        """Open a run and make it active."""
        if self._active_run is not None:
            raise RecorderError(
                f"a run is already active (run_id={self._active_run.run_id!r}); "
                "call end_run() before starting another"
            )
        rid = run_id or _new_id("run")
        meta = {"model": model, "config_hash": _config_hash(config)}
        if prompt_hash is not None:
            meta["prompt_hash"] = prompt_hash
        run = Run(
            run_id=rid,
            label=label,
            started_at=_utcnow(),
            metadata=meta,
        )
        self._store.add_run(run)
        self._active_run = run
        self._loop_index = 0
        return run

    def end_run(self) -> Run:
        """Mark the active run finished and persist the close timestamp."""
        if self._active_run is None:
            raise RecorderError("no run is active; end_run() is a no-op")
        finished = self._active_run.model_copy(update={
            "finished_at": _utcnow(),
        })
        self._store.add_run(finished)
        run = finished
        self._active_run = None
        self._loop_index = 0
        return run

    @property
    def active_run(self) -> Run | None:
        return self._active_run

    # ------------------------------------------------------------------
    # Operator events
    # ------------------------------------------------------------------

    def record_operator_event(
        self,
        *,
        operator_name: str,
        input_claims: tuple[str, ...] = (),
        output_claims: tuple[str, ...] = (),
        guard_result: str = "",
        sub_role: str = "",
        loop_index: int | None = None,
        event_id: str | None = None,
    ) -> OperatorEvent:
        run = self._require_active_run("record_operator_event")
        idx = loop_index if loop_index is not None else self._loop_index
        self._loop_index = max(self._loop_index, idx + 1)
        ev = OperatorEvent(
            event_id=event_id or _new_id("ev"),
            run_id=run.run_id,
            operator_code=operator_name,
            loop_index=idx,
            sub_role=sub_role,
            input_claim_ids=tuple(input_claims),
            output_claim_ids=tuple(output_claims),
            timestamp=_utcnow(),
            payload={"guard_result": guard_result} if guard_result else {},
        )
        self._store.add_event(ev)
        return ev

    # ------------------------------------------------------------------
    # Claim creation / revision
    # ------------------------------------------------------------------

    def record_claim(
        self,
        *,
        content: str,
        method: str,
        state: ClaimState = ClaimState.PROPOSED,
        confidence: float = 0.5,
        operator_path: tuple[str, ...] = (),
        claim_id: str | None = None,
    ) -> Claim:
        run = self._require_active_run("record_claim")
        provenance = Provenance(
            source="desi",
            run_id=run.run_id,
            operator_path=operator_path,
            timestamp=_utcnow(),
        )
        claim_kwargs: dict[str, Any] = {
            "content": content,
            "method": method,
            "state": state,
            "confidence": confidence,
            "version": 1,
            "provenance": provenance,
        }
        if claim_id is not None:
            claim_kwargs["claim_id"] = claim_id
        claim = Claim(**claim_kwargs)
        self._store.add_claim(claim)
        return claim

    def record_revision(
        self,
        claim: Claim,
        *,
        new_content: str | None = None,
        new_state: ClaimState | None = None,
        new_confidence: float | None = None,
        new_method: str | None = None,
    ) -> Claim:
        """Persist a revision of an existing claim.

        The recorder bumps ``version`` and keeps the original claim_id
        (this is what distinguishes a revision from a new derived
        claim — for that, the caller records a new claim plus a
        DERIVES_FROM edge).
        """
        run = self._require_active_run("record_revision")
        updates: dict[str, Any] = {
            "version": claim.version + 1,
            "state": new_state or ClaimState.REVISED,
        }
        if new_content is not None:
            updates["content"] = new_content
        if new_method is not None:
            updates["method"] = new_method
        if new_confidence is not None:
            updates["confidence"] = new_confidence
        # Update provenance to point at the current run so revision
        # ownership is traceable.
        updates["provenance"] = claim.provenance.model_copy(update={
            "run_id": run.run_id,
            "timestamp": _utcnow(),
        })
        revised = claim.model_copy(update=updates)
        self._store.add_claim(revised)
        return revised

    # ------------------------------------------------------------------
    # Relations
    # ------------------------------------------------------------------

    def record_relation(
        self,
        *,
        source: Claim | str,
        target: Claim | str,
        rel_type: RelationType,
        weight: float = 1.0,
    ) -> Relation:
        self._require_active_run("record_relation")
        source_id = source.claim_id if isinstance(source, Claim) else source
        target_id = target.claim_id if isinstance(target, Claim) else target
        rel = Relation(
            source_claim_id=source_id,
            target_claim_id=target_id,
            rel_type=rel_type,
            weight=weight,
            created_at=_utcnow(),
        )
        self._store.add_relation(rel)
        return rel

    # ------------------------------------------------------------------
    # Atomic helpers
    # ------------------------------------------------------------------

    def merge_claims(
        self,
        source_claims: list[Claim],
        target_claim: Claim,
    ) -> Claim:
        """Merge ``source_claims`` into ``target_claim`` atomically.

        Single transaction:

        1. ``target_claim`` is added (or updated, idempotent).
        2. each source claim is rewritten with state=MERGED and
           version+1.
        3. a ``MERGED_INTO`` relation is created from each source
           to the target.

        If any step raises, the transaction rolls back and the store
        is unchanged.
        """
        self._require_active_run("merge_claims")
        if not source_claims:
            raise RecorderError("merge_claims requires at least one source")
        if any(s.claim_id == target_claim.claim_id for s in source_claims):
            raise RecorderError(
                "merge target must differ from every source claim_id"
            )
        with self._store.transaction():
            self._store.add_claim(target_claim)
            for src in source_claims:
                merged_src = src.model_copy(update={
                    "state": ClaimState.MERGED,
                    "version": src.version + 1,
                })
                self._store.add_claim(merged_src)
                self._store.add_relation(Relation(
                    source_claim_id=src.claim_id,
                    target_claim_id=target_claim.claim_id,
                    rel_type=RelationType.MERGED_INTO,
                    created_at=_utcnow(),
                ))
        return target_claim

    def split_claim(
        self,
        source_claim: Claim,
        child_claims: list[Claim],
    ) -> list[Claim]:
        """Split ``source_claim`` into ``child_claims`` atomically.

        Single transaction:

        1. each child claim is added.
        2. the source claim is rewritten with state=SPLIT and
           version+1.
        3. a ``SPLIT_FROM`` relation is created from each child to
           the source.

        Returns the list of stored child claims in input order.
        """
        self._require_active_run("split_claim")
        if not child_claims:
            raise RecorderError("split_claim requires at least one child")
        if any(c.claim_id == source_claim.claim_id for c in child_claims):
            raise RecorderError(
                "split children must differ from source claim_id"
            )
        with self._store.transaction():
            for child in child_claims:
                self._store.add_claim(child)
                self._store.add_relation(Relation(
                    source_claim_id=child.claim_id,
                    target_claim_id=source_claim.claim_id,
                    rel_type=RelationType.SPLIT_FROM,
                    created_at=_utcnow(),
                ))
            split_source = source_claim.model_copy(update={
                "state": ClaimState.SPLIT,
                "version": source_claim.version + 1,
            })
            self._store.add_claim(split_source)
        return list(child_claims)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _require_active_run(self, op: str) -> Run:
        if self._active_run is None:
            raise RecorderError(
                f"{op}() requires an active run; call start_run() first"
            )
        return self._active_run
