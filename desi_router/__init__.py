"""desi_router — DESi's tool-first, privacy-aware LLM router as a building block.

Self-contained and stdlib-only: no third-party dependency, no import from the
rest of the DESi repository. Embed it by copying this folder into your project,
installing it (see EMBEDDING.md), or running from a repo checkout — the import
surface is identical either way.

The front door for embedding:

    from desi_router import DesiRouter

    router = DesiRouter.from_config("config.json")      # or DesiRouter(dict) / DesiRouter()
    result = router.route("What is 17 * 23?", privacy="prefer_local")

Deeper seams (all documented in EMBEDDING.md):

* :class:`ToolRegistry` / :func:`default_registry` — the deterministic tools;
* :class:`Registry` / :func:`load_config` / :func:`registry_from_dict` — providers;
* :class:`Constraints` and :func:`run` — the raw engine under the facade;
* :class:`Ledger` — the shared, append-only, hash-chained local Layer 9;
* ``desi_router.router.EpistemicRouter`` and ``desi_router.pipeline.DESiPipeline``
  (lazy exports below) — the benchmark-grounded Pareto router with
  confidence-based escalation, for the measured task classes.
"""
from __future__ import annotations

from desi_router.embed import DesiRouter
from desi_router.engine import run
from desi_router.ledger import Ledger
from desi_router.policy import ANY, LOCAL_ONLY, PREFER_LOCAL, Constraints, Decision, classify
from desi_router.providers import (
    ModelSpec,
    Provider,
    Registry,
    load_config,
    registry_from_dict,
)
from desi_router.tool_registry import Tool, ToolRegistry, default_registry

__version__ = "0.1.0"

__all__ = [
    "ANY",
    "LOCAL_ONLY",
    "PREFER_LOCAL",
    "Constraints",
    "Decision",
    "DesiRouter",
    "DESiPipeline",
    "EpistemicRouter",
    "Ledger",
    "ModelSpec",
    "Provider",
    "Registry",
    "RouteRequest",
    "Tool",
    "ToolRegistry",
    "classify",
    "default_registry",
    "load_config",
    "registry_from_dict",
    "run",
]


def __getattr__(name: str):
    # The Pareto/escalation stack is exported lazily so that importing the
    # lightweight routing core never pays for (or fails on) modules the host
    # does not use.
    if name in ("EpistemicRouter", "RouteRequest"):
        from desi_router import router as _router
        return getattr(_router, name)
    if name == "DESiPipeline":
        from desi_router.pipeline import DESiPipeline
        return DESiPipeline
    raise AttributeError(f"module 'desi_router' has no attribute {name!r}")
