"""Prior-work lookup: has this content or method already been done?

Before an instance works on something, it asks the shared ledger two questions:

  * **content** — has this exact task been processed before? Keyed by a light
    normalization of the query (lowercase, collapsed whitespace, trailing
    punctuation removed). Operators are preserved on purpose: "2+2" and "2*2"
    must NOT collide. This is exact-match-after-normalization, not semantic
    similarity (that would need embeddings and would not be deterministic).

  * **method** — has this routing approach been used before? Keyed by
    ``task_class | decision.kind | decision.target`` (e.g. a tool, or a specific
    provider/model), independent of the particular query.

A deterministic tool answer for matching content can be reused exactly; a model
answer is reported as a prior match but not auto-reused (it could be stale).
"""
from __future__ import annotations

import hashlib
import re

_WS = re.compile(r"\s+")


def normalize_query(query: str) -> str:
    q = _WS.sub(" ", query.strip().lower())
    return q.rstrip(" ?!.")


def content_hash(query: str) -> str:
    return hashlib.sha256(normalize_query(query).encode("utf-8")).hexdigest()


def method_signature(task_class: str, decision: dict) -> str:
    return f"{task_class}|{decision.get('kind', '')}|{decision.get('target', '')}"


def method_hash(task_class: str, decision: dict) -> str:
    return hashlib.sha256(method_signature(task_class, decision).encode("utf-8")).hexdigest()


# --- SPL S7: content/method separation as a closed, governed set ---------------
# SPL (spl_adapter/mapping.py) draws identity from (content + method), with method
# restricted to a closed set, and the S7 invariant: same content + different method
# => distinct, never merged. We adopt the *principle* here at the router level:
# a deterministic tool result and a stochastic model result are NEVER merged or
# reused across the boundary; only deterministic results are reused.
LEGAL_METHOD_CLASSES = frozenset({"deterministic", "stochastic"})


def method_class(decision: dict) -> str:
    """Governed method class: a tool is ``deterministic``; a model is ``stochastic``.

    Reuse/merge is permitted only within ``deterministic`` and never across this
    boundary (SPL's S7 invariant). A ``none`` decision is treated as stochastic
    (nothing deterministic was produced).
    """
    return "deterministic" if decision.get("kind") == "tool" else "stochastic"
