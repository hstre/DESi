"""DesiRouter — the one-object facade for embedding the router in your own code.

Everything the Reviewer Port wires by hand (config -> Registry, tool registry,
optional shared ledger, constraints -> engine) behind a single class, so a host
application needs exactly two lines:

    from desi_router import DesiRouter

    router = DesiRouter.from_config("config.json")
    result = router.route("What is 17 * 23?")           # -> routed, executed, audited

Design rules inherited from the rest of the package:

* stdlib only — embedding this must not pull a single dependency into the host;
* the *decision* is deterministic and always produced; only a live model call
  (if the decision picks one and ``execute_model`` is on) is outside that
  boundary — an unreachable model returns the decision with an ``error``,
  never a crash;
* the ledger is opt-in: without one the router is side-effect-free on disk.
  With one, every routed query is appended to the shared, hash-chained local
  Layer 9 and exact deterministic prior work is reused (SPL S7: never across
  the deterministic/stochastic boundary).

See EMBEDDING.md for the full guide.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable

from desi_router.engine import run as _run
from desi_router.ledger import Ledger
from desi_router.policy import Constraints, Decision, classify, decide
from desi_router.providers import Registry, load_config, registry_from_dict
from desi_router.tool_registry import Tool, ToolRegistry, default_registry


class DesiRouter:
    """Tool-first, privacy-aware routing as an embeddable building block.

    Parameters
    ----------
    config:
        Where the models live. A path to a ``config.json``, an equivalent
        ``dict`` (same shape as ``config.example.json``), an already-built
        :class:`Registry` — or ``None`` for a model-free router that still
        answers everything its deterministic tools cover (fully offline).
    corpus_dir:
        Optional folder of local documents; enables the deterministic
        ``keyword_retrieval`` tool. Ignored when ``tools`` is given.
    tools:
        Bring your own :class:`ToolRegistry` (the default registry ships
        calculator / date_math / unit_conversion). Use :meth:`add_tool` to
        extend either.
    ledger:
        ``None`` (default) for no persistence, a path for the shared local
        Layer 9 ledger (created if missing, appended if shared), or an
        existing :class:`Ledger` instance the host already holds.
    instance_id:
        How this embedding identifies itself in a shared ledger
        (default: ``hostname:pid``). Ignored when ``ledger`` is an instance.
    """

    def __init__(
        self,
        config: str | Path | dict | Registry | None = None,
        *,
        corpus_dir: str | Path | None = None,
        tools: ToolRegistry | None = None,
        ledger: str | Path | Ledger | None = None,
        instance_id: str | None = None,
    ) -> None:
        if config is None:
            self.registry = Registry(providers=[])
        elif isinstance(config, Registry):
            self.registry = config
        elif isinstance(config, dict):
            self.registry = registry_from_dict(config)
        else:
            self.registry = load_config(config)
        self.tools = tools if tools is not None else default_registry(corpus_dir)
        self._owns_ledger = not isinstance(ledger, Ledger)
        if ledger is None:
            self.ledger: Ledger | None = None
        elif isinstance(ledger, Ledger):
            self.ledger = ledger
        else:
            self.ledger = Ledger(ledger, instance_id=instance_id)

    @classmethod
    def from_config(cls, path: str | Path, **kwargs: Any) -> DesiRouter:
        """Build from a ``config.json`` file (see ``config.example.json``)."""
        return cls(path, **kwargs)

    # ---- routing ----------------------------------------------------------- #

    def route(
        self,
        query: str,
        *,
        privacy: str = "prefer_local",
        accuracy_target: float = 0.0,
        cost_budget_usd: float = float("inf"),
        task_class: str | None = None,
        execute_model: bool = True,
        reuse: bool = True,
    ) -> dict[str, Any]:
        """Classify, decide, execute, audit — one query end to end.

        Returns the engine's result dict: ``task_class``, ``decision``,
        ``answer`` (``None`` when nothing could or was allowed to run),
        ``answer_source``, ``error``, ``prior`` (ledger reuse report) and
        ``audit`` (replay-stable hash over query + constraints + decision).
        ``privacy`` is ``"local_only"`` / ``"prefer_local"`` / ``"any"``.
        """
        constraints = Constraints(
            privacy=privacy,
            cost_budget_usd=cost_budget_usd,
            accuracy_target=accuracy_target,
        )
        return _run(
            query,
            registry=self.registry,
            tools=self.tools,
            constraints=constraints,
            task_class=task_class,
            execute_model=execute_model,
            ledger=self.ledger,
            reuse=reuse,
        )

    def decide(
        self,
        query: str,
        *,
        privacy: str = "prefer_local",
        accuracy_target: float = 0.0,
        cost_budget_usd: float = float("inf"),
        task_class: str | None = None,
    ) -> Decision:
        """The routing decision alone — nothing is executed, nothing persisted.

        Pure and deterministic: a host that only wants to *dispatch* (run the
        model call through its own client, queue, retry logic) embeds this and
        keeps full control of execution.
        """
        constraints = Constraints(
            privacy=privacy,
            cost_budget_usd=cost_budget_usd,
            accuracy_target=accuracy_target,
        )
        return decide(task_class or classify(query), constraints, self.registry, self.tools)

    # ---- extension ---------------------------------------------------------- #

    def add_tool(
        self,
        name: str,
        task_classes: Iterable[str],
        fn: Callable[[str], object],
    ) -> None:
        """Register a deterministic tool of your own.

        ``fn`` takes the query text and returns the result (raise on input it
        cannot parse — the engine surfaces that honestly as an error). A tool
        that covers the classified task always wins over any model: exact,
        $0, local. Keep tools deterministic; a stochastic step belongs behind
        a model provider, not a tool, or the audit/reuse guarantees lie.
        """
        self.tools.register(Tool(name, frozenset(task_classes), fn))

    # ---- lifecycle ---------------------------------------------------------- #

    def close(self) -> None:
        """Close a ledger this router opened itself (a passed-in instance is
        the host's to manage). Safe to call twice."""
        if self.ledger is not None and self._owns_ledger:
            self.ledger.close()
            self.ledger = None

    def __enter__(self) -> DesiRouter:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
