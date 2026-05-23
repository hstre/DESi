"""v25.3 - workshop note port.

A short workshop note rendered from the same epistemic state as
the arXiv paper: fewer sections, identical claims and numbers.
"""
from __future__ import annotations

from desi.output_ports import PortType

from .renderer import render_port

PORT = PortType.WORKSHOP_NOTE.value


def render() -> str:
    return render_port(PORT)


__all__ = ["PORT", "render"]
