"""Deterministic scope-match check — the wrong-scope plausible-wrong-slice signal.

A claim can be perfectly correct and still wrong *here*: it belongs to a different project, tenant,
user, region or time scope than the task asks about. The slice looks clean (the claim is valid) but
applies it out of scope. This is invisible to opposition and provenance checks — the graph holds no
contradiction and the source is fine; only the *scope tag* mismatches.

Deterministic, no LLM: compare the task's required scope against each selected claim's scope tag and
report the mismatches. Against a live Layer-9 the scope comes from the claim's ``scope``/``project_id``
and the task's project/user context. Degrades to caution, never blocks; an empty task scope means
"no scope constraint", so nothing is flagged.
"""
from __future__ import annotations

from collections.abc import Iterable


def scope_mismatches(task_scope: str | None,
                     claim_scopes: Iterable[str]) -> tuple[str, ...]:
    """Claim scope tags that do NOT match the task's required scope. Empty if no task scope is set
    (no constraint) or every claim matches. Order-stable, de-duped."""
    if not task_scope:
        return ()
    out: dict[str, None] = {}
    for s in claim_scopes:
        if s and s != task_scope:
            out[s] = None
    return tuple(out)
