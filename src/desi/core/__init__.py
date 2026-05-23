"""desi.core - stable public facade over the protected core.

Provides the recommended import paths

    from desi.core import replay_kernel
    from desi.core import determinism_scanner
    from desi.core import governance_core

without relocating any implementation. Modules were NOT physically
moved (that would churn the import graph and risk replay drift); this
facade re-exports the real, in-place implementations.
"""
from __future__ import annotations

from . import determinism_scanner, governance_core, replay_kernel

__all__ = ["determinism_scanner", "governance_core", "replay_kernel"]
