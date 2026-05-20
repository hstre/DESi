"""v25.1 - arXiv paper port.

Assembles the 13 mandated sections, in schema order, into a
single arXiv-compatible markdown paper. Rendering is a pure
function of the epistemic state; it is deterministic and adds
nothing the schema does not require.
"""
from __future__ import annotations

from desi.output_ports import (
    PortType, schema_for, section_title,
)

from .section_builder import build_section

PORT = PortType.ARXIV_PAPER.value


def required_sections() -> tuple[str, ...]:
    return schema_for(PORT).required_sections


def section_completeness() -> float:
    """Fraction of the port's required sections that render to
    non-empty content, in [0, 1]."""
    req = required_sections()
    if not req:
        return 0.0
    present = sum(
        1 for key in req if build_section(key).strip()
    )
    return round(present / len(req), 6)


def missing_sections() -> tuple[str, ...]:
    return tuple(
        key for key in required_sections()
        if not build_section(key).strip()
    )


def render() -> str:
    """Render the full arXiv paper in schema section order."""
    parts: list[str] = []
    for key in required_sections():
        body = build_section(key)
        if key == "title":
            parts.append(f"# {body}")
        else:
            parts.append(f"## {section_title(key)}\n\n{body}")
    return "\n\n".join(parts) + "\n"


__all__ = [
    "PORT",
    "missing_sections",
    "render",
    "required_sections",
    "section_completeness",
]
