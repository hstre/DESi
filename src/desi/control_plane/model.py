"""Authority and taint model for the DESi control plane.

The goal is not "no participating model drifts" — that is unrealistic. The
goal is: a drifting model can neither silently mutate the authoritative
Layer-9 state nor change goals, roles, method selection, or release rules.
Two mechanisms enforce that, both deterministic (rules, not a model):

1. **Strict data/control separation.** Everything from a source, user dialogue,
   or model response is *non-authoritative* until the controller promotes it.
   A model may *write* ``epistemic_status: verified`` into its output — DESi
   ignores the field. Status changes are made only by the gate (``gate.py``).

2. **Taint tracking across derivations.** A neutral summary of a contaminated
   text is not automatically clean. Every object carries its provenance and
   exposure; taint propagates through ``derived_from`` and is reduced only by
   defined check operations, never by rewriting.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace

# --- origins and authority --------------------------------------------------
ORIGINS = ("source", "user", "model", "system_policy")
# Ordered authority lattice: a higher level may steer more.
AUTHORITY_LEVELS = ("untrusted", "candidate", "verified", "control")
_AUTH_RANK = {a: i for i, a in enumerate(AUTHORITY_LEVELS)}

# Only system_policy origin and already-promoted control objects may steer.
STEERING_AUTHORITY = "control"

# Control-sensitive object kinds — they need higher clearance than a plain
# claim, because they change how the system itself behaves.
CONTROL_SENSITIVE_KINDS = frozenset({
    "goal", "role", "method_rule", "constraint", "router_rule", "status_promotion",
})

# Fields a model is never allowed to set on itself; stripped on ingestion.
_MODEL_FORBIDDEN_FIELDS = ("authority", "epistemic_status", "status", "verified",
                           "control", "taint", "exposure")

# --- taint and exposure -----------------------------------------------------
EXPOSURES = ("adversarial_source", "affective_dialogue")
TAINTS = ("framing", "role", "attribution")

# A taint flag is cleared ONLY by passing its named check operation. Rewriting
# the text (a model "cleaning" itself) does not clear taint.
TAINT_CLEARING_CHECK = {
    "framing": "framing_distance_check",
    "role": "role_frame_check",
    "attribution": "attribution_check",
}


@dataclass(frozen=True)
class StateObject:
    """A candidate or authoritative Layer-9 object, with provenance and taint."""
    obj_id: str
    kind: str
    payload: Mapping[str, object] = field(default_factory=dict)
    origins: tuple[str, ...] = ()
    authority: str = "untrusted"
    derived_from: tuple[str, ...] = ()
    exposure: frozenset[str] = field(default_factory=frozenset)
    taint: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self):
        bad = [o for o in self.origins if o not in ORIGINS]
        if bad:
            raise ValueError(f"unknown origin(s): {bad}; choose from {ORIGINS}")
        if self.authority not in AUTHORITY_LEVELS:
            raise ValueError(f"unknown authority {self.authority!r}")
        if not set(self.exposure) <= set(EXPOSURES):
            raise ValueError(f"unknown exposure in {self.exposure}")
        if not set(self.taint) <= set(TAINTS):
            raise ValueError(f"unknown taint in {self.taint}")

    @property
    def is_control_sensitive(self) -> bool:
        return self.kind in CONTROL_SENSITIVE_KINDS

    @property
    def eligible_for_control_state(self) -> bool:
        """A tainted or adversarially-exposed object can never steer."""
        return not self.taint and "adversarial_source" not in self.exposure

    def has_steering_effect(self) -> bool:
        """Only control-authority objects (set by the gate) actually steer."""
        return self.authority == STEERING_AUTHORITY


def authority_at_least(authority: str, minimum: str) -> bool:
    return _AUTH_RANK[authority] >= _AUTH_RANK[minimum]


def ingest_model_output(obj_id: str, kind: str, raw: Mapping[str, object],
                        *, derived_from: tuple[str, ...] = (),
                        exposure: frozenset[str] = frozenset()) -> StateObject:
    """Wrap a raw model output as a strictly NON-authoritative object.

    Any self-asserted authority/status/taint fields are stripped — a model
    cannot promote itself. Model-origin objects start at ``untrusted`` and
    inherit exposure (and, by default, the matching framing/role taint, since
    a model that saw adversarial/affective context is presumed exposed until a
    check clears it).
    """
    payload = {k: v for k, v in raw.items() if k not in _MODEL_FORBIDDEN_FIELDS}
    taint: set[str] = set()
    if "adversarial_source" in exposure:
        taint.update({"framing", "attribution"})
    if "affective_dialogue" in exposure:
        taint.add("role")
    return StateObject(
        obj_id=obj_id, kind=kind, payload=payload, origins=("model",),
        authority="untrusted", derived_from=tuple(derived_from),
        exposure=frozenset(exposure), taint=frozenset(taint),
    )


def propagate(obj: StateObject, parents: list[StateObject]) -> StateObject:
    """Taint and exposure flow through derivation: a derived object is at least
    as exposed/tainted as the union of its parents (laundering is impossible
    by simply summarizing)."""
    exp = set(obj.exposure)
    taint = set(obj.taint)
    parent_ids = list(obj.derived_from)
    for p in parents:
        exp |= set(p.exposure)
        taint |= set(p.taint)
        if p.obj_id not in parent_ids:
            parent_ids.append(p.obj_id)
    return replace(obj, exposure=frozenset(exp), taint=frozenset(taint),
                   derived_from=tuple(parent_ids))


def clear_taint(obj: StateObject, checks_passed: set[str]) -> StateObject:
    """Reduce taint only via the defined check operations.

    A taint flag is removed iff its required check name is in ``checks_passed``.
    Rewriting alone (no check) clears nothing — that is the whole point.
    """
    remaining = {t for t in obj.taint if TAINT_CLEARING_CHECK.get(t) not in checks_passed}
    return replace(obj, taint=frozenset(remaining))
