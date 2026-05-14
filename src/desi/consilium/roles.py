"""Consilium roles — the four adversarial reviewers (v1.3).

v1.3 introduces an authority-free *bridge consilium*: a closed set
of four roles that adversarially examine every bridge claim
produced by the v1.2 logical-gap audit. The roles are deterministic
rule-based reviewers. There is no LLM judge. There is no majority
vote. A single role that surfaces an unresolved gap blocks the
bridge.

The closed enum lives here so downstream code cannot silently
introduce a fifth role. Adding a role requires a code edit, which
is itself an audit event.
"""
from __future__ import annotations

from enum import Enum


class ConsiliumRole(str, Enum):
    """The four mandatory consilium reviewers.

    * ``LOGICIAN``         — validates inference structure; checks
      whether the bridge plus the original premises form a
      structurally sound argument under the v1.2 rule set.
    * ``SKEPTIC``           — searches for counterexamples and edge
      conditions that would falsify the bridge.
    * ``DOMAIN_EXAMINER``  — searches for missing environmental
      constraints and domain-specific exceptions (e.g. metaphor
      vs. literal use of "flooded").
    * ``INTEGRATOR``       — checks whether the bridge, once
      accepted, actually closes the original gap end-to-end.
    """

    LOGICIAN = "logician"
    SKEPTIC = "skeptic"
    DOMAIN_EXAMINER = "domain_examiner"
    INTEGRATOR = "integrator"


# The canonical evaluation order. The directive requires that the
# *verdict* be invariant under reordering of the role set; the
# orchestrator uses this constant only as a stable tie-breaker for
# ledger writes. The verdict-aggregation logic itself reads the role
# review set, not the sequence.
CANONICAL_ROLE_ORDER: tuple[ConsiliumRole, ...] = (
    ConsiliumRole.LOGICIAN,
    ConsiliumRole.SKEPTIC,
    ConsiliumRole.DOMAIN_EXAMINER,
    ConsiliumRole.INTEGRATOR,
)


__all__ = [
    "CANONICAL_ROLE_ORDER",
    "ConsiliumRole",
]
