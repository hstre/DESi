"""Closed registry of existing tunable parameters (Aufgabe 7).

The v2.1 diagnostic may only recommend knobs that physically exist
in stable-v1.9.0 + the v2.0 sandbox. "new operator", "more data",
"bigger LLM" are forbidden by directive — they would not appear in
this set.

The registry is the source of truth for two operations:

* ``is_known_knob(name)`` — used by :class:`DeficitRecord` to refuse
  unknown candidate knobs.
* ``live_knobs()`` / ``dead_knobs()`` — used by the final report.
  A knob is "dead" only when it has been **empirically** shown to
  produce no metric movement. Without evidence a knob is treated as
  ``unknown_liveness`` (i.e. not yet classified as dead).
"""
from __future__ import annotations

from dataclasses import dataclass


# The closed list of every parameter present in stable-v1.9.0 + v2.0
# that an external caller can adjust without modifying source code.
# Comments give the file:line of the definition for traceability.
EXISTING_KNOBS: frozenset[str] = frozenset({
    # v1.4 recursive resolver
    "RecursiveResolver.max_depth",
    # v1.9 tool gate
    "ToolGate.HARD_TIMEOUT_SECONDS",
    "ToolGate.MAX_INPUT_BYTES",
    # v0.7 era — empirically dead per v2.0
    "branch_open_evidence_min",
    # v2.0 sandbox
    "EvolutionSandbox.n_steps",
    "EvolutionSandbox.abort_on_kill",
    "EvolutionSandbox.initial_value",
})


# Liveness — only knobs with empirical evidence of being dead land
# here. "Empirical" means: a sandbox / benchmark run has shown that
# changing the value produces no metric movement over the six gate
# observables.
EMPIRICALLY_DEAD_KNOBS: frozenset[str] = frozenset({
    "branch_open_evidence_min",   # proven dead by v2.0 30-step sandbox
})


@dataclass(frozen=True)
class KnobInventory:
    """Lookup helper bundled with the closed sets above."""

    existing: frozenset[str]
    empirically_dead: frozenset[str]

    def is_known(self, name: str) -> bool:
        return name in self.existing

    def live_knobs(self) -> frozenset[str]:
        return self.existing - self.empirically_dead

    def dead_knobs(self) -> frozenset[str]:
        return frozenset(self.empirically_dead)


DEFAULT_INVENTORY: KnobInventory = KnobInventory(
    existing=EXISTING_KNOBS,
    empirically_dead=EMPIRICALLY_DEAD_KNOBS,
)


__all__ = [
    "DEFAULT_INVENTORY",
    "EMPIRICALLY_DEAD_KNOBS",
    "EXISTING_KNOBS",
    "KnobInventory",
]
