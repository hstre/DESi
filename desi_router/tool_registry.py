"""Pluggable tool registry — the deterministic alternatives to a model call.

A tool covers one or more task classes. If a tool covers the classified task,
the router prefers it: exact, replay-stable, ~$0, and fully local/private. New
tools (CAS, code-exec, retrieval, date/units) register the same way — no router
change.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from desi_router.arithmetic_tool import evaluate_expression
from desi_router.tools import convert_units, make_keyword_search, solve_date


@dataclass(frozen=True)
class Tool:
    name: str
    task_classes: frozenset[str]
    run: Callable[[str], object]        # query text -> result (raises on inapplicable input)


class ToolRegistry:
    def __init__(self, tools: list[Tool] | None = None):
        self._tools = list(tools) if tools else []

    def register(self, tool: Tool) -> None:
        self._tools.append(tool)

    def find(self, task_class: str) -> Tool | None:
        for t in self._tools:
            if task_class in t.task_classes:
                return t
        return None


def default_registry(corpus_dir: str | Path | None = None) -> ToolRegistry:
    """The built-in deterministic tools shipped with v0.1.

    ``corpus_dir`` optionally enables the keyword-retrieval tool over a local
    document folder; without it, retrieval is not registered (the router never
    claims a tool it has no data for).

    Deliberately NOT shipped: arbitrary code execution. A real code-exec tool
    needs a sandbox; shipping an unsandboxed evaluator would be a security
    footgun. The registry slot is open for a sandboxed executor later.
    """
    tools = [
        Tool("calculator", frozenset({"math_arithmetic"}), evaluate_expression),
        Tool("date_math", frozenset({"date_math"}), solve_date),
        Tool("unit_conversion", frozenset({"unit_conversion"}), convert_units),
    ]
    if corpus_dir is not None:
        tools.append(
            Tool("keyword_retrieval", frozenset({"retrieval"}), make_keyword_search(corpus_dir))
        )
    return ToolRegistry(tools)
