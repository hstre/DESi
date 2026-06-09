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
from desi.dedup import content_hash as _content_hash
from desi.dedup import method_hash as _method_hash
from desi.policy import Constraints, Decision, classify, decide
from desi.providers import OpenAICompatibleClient, Registry
from desi.tool_registry import ToolRegistry


def _provider_by_name(registry: Registry, name: str):
    for p in registry.providers:
        if p.name == name:
            return p
    return None


def _reusable_tool_answer(prior_content: list[dict]) -> dict | None:
    """Most recent prior event with the same content and a deterministic
    (tool) answer — safe to reuse exactly. Model answers are not auto-reused."""
    for e in reversed(prior_content):
        p = e["payload"]
        if p.get("answer") is not None and str(p.get("answer_source", "")).startswith("tool"):
            return e
    return None


def run(
    query: str,
    *,
    registry: Registry,
    tools: ToolRegistry,
    constraints: Constraints | None = None,
    task_class: str | None = None,
    execute_model: bool = True,
    ledger=None,
    reuse: bool = True,
) -> dict[str, Any]:
    constraints = constraints or Constraints()
    tc = task_class or classify(query)
    decision: Decision = decide(tc, constraints, registry, tools)

    ch = _content_hash(query)
    mh = _method_hash(tc, decision.to_dict())

    # ask the shared ledger: is this content / method already present?
    prior_content = ledger.by_content_hash(ch) if ledger is not None else []
    prior_method = ledger.by_method_hash(mh) if ledger is not None else []

    answer: str | None = None
    answer_source = "none"
    error: str | None = None
    reused = False

    reusable = _reusable_tool_answer(prior_content) if reuse else None
    if reusable is not None:
        # exact reuse of a deterministic prior result — no recomputation
        answer = reusable["payload"]["answer"]
        answer_source = f"reused:tool#{reusable['seq']}"
        reused = True
    elif decision.kind == "tool":
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

    prior = {
        "content_seen": bool(prior_content),
        "content_count": len(prior_content),
        "content_prior_seq": prior_content[-1]["seq"] if prior_content else None,
        "content_prior_instance": prior_content[-1]["instance_id"] if prior_content else None,
        "method_seen": bool(prior_method),
        "method_count": len(prior_method),
        "reused": reused,
        "reuse_source": answer_source if reused else None,
    }

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
    result = {
        "task_class": tc,
        "decision": decision.to_dict(),
        "answer": answer,
        "answer_source": answer_source,
        "error": error,
        "prior": prior,
        "audit": audit.to_dict(),
    }

    # persist to the local Layer 9 (append-only, shared across instances)
    if ledger is not None:
        entry = ledger.record(
            "route",
            {
                "task_class": tc,
                "query": query,
                "decision": decision.to_dict(),
                "answer": answer,
                "answer_source": answer_source,
                "reused": reused,
                "prior_seq": prior["content_prior_seq"],
            },
            decision_hash=audit.decision_hash,
            content_hash=ch,
            method_hash=mh,
        )
        result["ledger"] = entry

    return result
