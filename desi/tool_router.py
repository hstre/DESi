"""Tool-router — DESi routing taken one step past model selection.

The model-router (``router.EpistemicRouter``) answers "which *model* for this
task class". The natural endpoint of "LLM for language, rules for logic" is one
question earlier: should this run a model at all, or a deterministic *tool*?

For a task whose core is a known computation (arithmetic, unit conversion,
date math, a lookup), a tool is exact, replay-stable, ~$0 and frame-invariant —
strictly better than any stochastic model on the part it covers. This router
sends such task classes to a tool and delegates everything else to the
empirical model-router.

Scope: v0.1, a deliberately small, honest seam. The only tool wired here is the
arithmetic evaluator; the catalogue is meant to grow (sympy/CAS, code exec,
retrieval) the same way the routing table did — by measurement, not assertion.
"""
from __future__ import annotations

from dataclasses import dataclass

# task classes whose core reduces to a deterministic tool
TOOL_TASKS = {"math_arithmetic"}


@dataclass
class ToolRoute:
    kind: str               # "tool"
    tool: str               # tool identifier
    rationale: str
    deterministic: bool = True
    expected_cost_usd: float = 0.0


class ToolRouter:
    """Route to a deterministic tool when one covers the task; else to a model."""

    def __init__(self, model_router=None):
        # lazy/optional: importing the model router pulls routing_table.json
        self._model_router = model_router

    def _models(self):
        if self._model_router is None:
            from desi.router import EpistemicRouter

            self._model_router = EpistemicRouter()
        return self._model_router

    def route(self, task_class: str, **model_kwargs):
        """Return a ToolRoute for tool-covered task classes, else a model Decision.

        ``model_kwargs`` (cost/accuracy/latency budgets) are forwarded to the
        model-router for non-tool tasks.
        """
        if task_class in TOOL_TASKS:
            return ToolRoute(
                kind="tool",
                tool="arithmetic_evaluator",
                rationale=(
                    "Core is a known arithmetic structure: a deterministic "
                    "evaluator is exact, replay-stable, frame-invariant and ~$0 — "
                    "running a stochastic model here can only add error and cost."
                ),
            )
        from desi.router import RouteRequest

        return self._models().route(RouteRequest(task_class=task_class, **model_kwargs))
