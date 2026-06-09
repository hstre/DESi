"""Pluggable tool registry — the deterministic alternatives to a model call.

A tool covers one or more task classes. If a tool covers the classified task,
the router prefers it: exact, replay-stable, ~$0, and fully local/private. New
tools (CAS, code-exec, retrieval, date/units) register the same way — no router
change.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from desi.arithmetic_tool import evaluate_expression


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


def default_registry() -> ToolRegistry:
    """The built-in tools shipped with v0.1."""
    return ToolRegistry(
        [
            Tool(
                name="calculator",
                task_classes=frozenset({"math_arithmetic"}),
                run=evaluate_expression,
            ),
        ]
    )
