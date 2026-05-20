"""v25.2 - reference registry view.

Single source of truth for references is the v25.1 reference
manager; this module re-exposes it for the citation governance
layer so there is exactly one registry, never a divergent copy.
"""
from __future__ import annotations

from desi.output_ports_arxiv import (
    Reference, is_registered, reference_keys, references,
    resolve,
)


def registered_keys() -> frozenset[str]:
    return reference_keys()


__all__ = [
    "Reference",
    "is_registered",
    "reference_keys",
    "references",
    "registered_keys",
    "resolve",
]
