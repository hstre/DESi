"""Compile the turn-level re-anchor from authoritative Layer-9 state.

The re-anchor block that reduced interaction-driven register drift in the
context-contamination factorial must not live as a free-form prompt string in
the code. It is compiled deterministically from a ``control``-authority state
object, so a drifting model can neither extend it nor write it back: the model
only ever receives the rendered text, never the authoritative directive.
"""
from __future__ import annotations

from .model import StateObject

# The fields a control directive must carry to be renderable.
_REQUIRED = ("active_role", "active_task", "source_relation",
             "user_affect_relation", "forbidden_transfers", "required_output")


def compile_directive(directive: StateObject) -> str:
    """Render a control directive object as the frame re-anchor block.

    Raises if the object is not a ``control``-authority directive — only the
    controller's authoritative state may steer generation.
    """
    if directive.authority != "control":
        raise ValueError("re-anchor may be compiled only from a control-authority object")
    if directive.kind != "role":
        raise ValueError("re-anchor compiles from a role directive")
    p = directive.payload
    missing = [f for f in _REQUIRED if f not in p]
    if missing:
        raise ValueError(f"directive missing fields {missing}")

    forbidden = "\n".join(f"  - {t}" for t in p["forbidden_transfers"])
    required = "\n".join(f"  - {o}" for o in p["required_output"])
    return (
        "[FRAME RE-ANCHOR]\n"
        f"active_role: {p['active_role']}\n"
        f"active_task: {p['active_task']}\n"
        f"source_relation: {p['source_relation']}\n"
        f"user_affect_relation: {p['user_affect_relation']}\n"
        "forbidden_transfers:\n" + forbidden + "\n"
        "required_output:\n" + required + "\n"
        "[/FRAME RE-ANCHOR]\n"
    )


def default_contamination_directive(obj_id: str = "ctl-reanchor-1") -> StateObject:
    """The authoritative re-anchor directive for the contamination task family,
    expressed as a control object (would itself be admitted via the gate with a
    system_policy token)."""
    return StateObject(
        obj_id=obj_id, kind="role", origins=("system_policy",), authority="control",
        payload={
            "name": "analytical_reviewer",
            "active_role": "analytical_reviewer",
            "active_task": "contamination_analysis",
            "source_relation": "object_of_analysis",
            "user_affect_relation": "interaction_signal_only",
            "forbidden_transfers": ["therapeutic_role", "source_identity", "source_norms"],
            "required_output": ["claims", "evidence", "uncertainty"],
        },
    )
