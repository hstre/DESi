"""v25.3 - technical report port.

A technical report rendered from the same epistemic state:
emphasises experimental conditions, metrics and reproducibility,
with identical claims and numbers to the other ports.
"""
from __future__ import annotations

from desi.output_ports import PortType

from .renderer import render_port

PORT = PortType.TECHNICAL_REPORT.value


def render() -> str:
    return render_port(PORT)


__all__ = ["PORT", "render"]
