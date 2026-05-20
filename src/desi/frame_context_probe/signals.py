"""Closed taxonomy of context signals — Aufgabe 3."""
from __future__ import annotations

from enum import Enum


class ContextSignal(str, Enum):
    SECTION_HEADER = "section_header"
    EXPLICIT_FRAME = "explicit_frame"
    DOMAIN_REPETITION = "domain_repetition"
    TOOL_ROUTE = "tool_route"
    AUTHORITY_CONTEXT = "authority_context"
    METAPHOR_CONTEXT = "metaphor_context"
    NONE = "none"


__all__ = ["ContextSignal"]
