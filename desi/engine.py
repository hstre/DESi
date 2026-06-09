"""DESi router engine — classify, decide, execute, audit.

Ties the pieces together for one query:
  1. classify the task (or accept an explicit override),
  2. decide tool / local-model / api-model (deterministic, replay-stable),
  3. execute — the tool runs locally and deterministically; a model is called
     only if its provider is reachable (no network/key -> decision returned
     without an answer, never a crash),
  4. record a deterministic audit entry.

The decision + audit are reproducible regardless of whether a model was reached;
only the model's text answer lives outside the deterministic boundary.
"""
from __future__ import annotations

from typing import Any

from desi.audit import AuditRecord
from desi.policy import Constraints, Decision, classify, decide
from desi.providers import OpenAICompatibleClient, Registry
from desi.tool_registry import ToolRegistry


def _provider_by_name(registry: Registry, name: str):
    for p in registry.providers:
        if p.name == name:
            return p
    return None


def run(
    query: str,
    *,
    registry: Registry,
    tools: ToolRegistry,
    constraints: Constraints | None = None,
    task_class: str | None = None,
    execute_model: bool = True,
) -> dict[str, Any]:
    constraints = constraints or Constraints()
    tc = task_class or classify(query)
    decision: Decision = decide(tc, constraints, registry, tools)

    answer: str | None = None
    answer_source = "none"
    error: str | None = None

    if decision.kind == "tool":
        tool = tools.find(tc)
        try:
            answer = str(tool.run(query))
            answer_source = "tool"
        except Exception as exc:  # inapplicable input is a language failure, surfaced honestly
            error = f"tool '{tool.name}' could not parse the query: {exc}"
    elif decision.kind == "model" and execute_model:
        provider = _provider_by_name(registry, decision.extras.get("provider", ""))
        if provider is not None:
            try:
                client = OpenAICompatibleClient(provider)
                answer = client.chat(
                    decision.extras["model_id"],
                    [{"role": "user", "content": query}],
                )
                answer_source = f"model:{decision.target}"
            except Exception as exc:  # offline / no key / unreachable -> decision still stands
                error = f"model not reached ({decision.target}): {exc}"

    audit = AuditRecord(
        query=query,
        task_class=tc,
        constraints={
            "privacy": constraints.privacy,
            "cost_budget_usd": constraints.cost_budget_usd,
            "accuracy_target": constraints.accuracy_target,
        },
        decision=decision.to_dict(),
        answer=answer,
        answer_source=answer_source,
    )
    return {
        "task_class": tc,
        "decision": decision.to_dict(),
        "answer": answer,
        "answer_source": answer_source,
        "error": error,
        "audit": audit.to_dict(),
    }
