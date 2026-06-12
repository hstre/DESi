"""The deterministic Layer-9 state-update gate.

No model output reaches the authoritative state directly. Every candidate
passes a fixed pipeline; on any failure the object stays ``candidate`` or is
rejected — it never silently becomes authoritative:

    module output
      -> schema validation
      -> provenance check
      -> frame / role check
      -> conflict check
      -> independent verification
      -> allowed status change
      -> ledger

The gate is pure rules (no LLM) and returns the full reason trail, so every
admit/reject decision is auditable.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .model import (
    CONTROL_SENSITIVE_KINDS,
    StateObject,
    authority_at_least,
)

# Required payload fields per object kind (schema validation).
_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "claim": ("content",),
    "goal": ("statement",),
    "role": ("name",),
    "method_rule": ("rule",),
    "constraint": ("rule",),
    "router_rule": ("rule",),
    "status_promotion": ("target_id", "to_authority"),
}


@dataclass
class GateDecision:
    """Outcome of one update attempt — auditable, with the full reason trail."""
    obj_id: str
    requested: str
    admitted_authority: str          # what the object actually became
    accepted: bool                   # admitted at the requested level?
    rejected: bool                   # blocked entirely (stays out of state)?
    reasons: list[str] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "obj_id": self.obj_id, "requested": self.requested,
            "admitted_authority": self.admitted_authority,
            "accepted": self.accepted, "rejected": self.rejected,
            "reasons": list(self.reasons), "checks": dict(self.checks),
        }


class LedgerSink:
    """In-memory append-only sink (the seam to desi_router.ledger.Ledger).

    Production wiring passes an object whose ``record(kind, payload)`` appends
    to the hash-chained Layer-9 ledger; tests use this fake.
    """

    def __init__(self):
        self.events: list[tuple[str, dict]] = []

    def record(self, kind: str, payload: dict) -> dict:
        self.events.append((kind, dict(payload)))
        return {"seq": len(self.events)}


class StateUpdateGate:
    """Admits candidates into Layer 9 only through the fixed check pipeline."""

    def __init__(self, state: Mapping[str, StateObject] | None = None,
                 *, system_policy_tokens: frozenset[str] = frozenset(),
                 ledger: LedgerSink | None = None):
        # current authoritative state, keyed by obj_id (verified / control)
        self.state: dict[str, StateObject] = dict(state or {})
        # opaque tokens that only the controller / system_policy possesses;
        # required to promote control-sensitive kinds or reach control authority
        self._tokens = frozenset(system_policy_tokens)
        self.ledger = ledger or LedgerSink()

    # --- the pipeline steps (each returns (ok, reason)) ---------------------

    def _schema_ok(self, obj: StateObject) -> tuple[bool, str]:
        required = _REQUIRED_FIELDS.get(obj.kind)
        if required is None:
            return False, f"unknown kind {obj.kind!r}"
        missing = [f for f in required if f not in obj.payload]
        return (not missing), (f"missing fields {missing}" if missing else "schema ok")

    def _provenance_ok(self, obj: StateObject) -> tuple[bool, str]:
        # A model-origin object may never carry pre-set authority above
        # untrusted; that would mean it promoted itself.
        if "model" in obj.origins and authority_at_least(obj.authority, "verified"):
            return False, "model-origin object self-asserted authority"
        # Every derived_from reference must resolve to known state or be a
        # declared external producer id (source:/model:/user:).
        for ref in obj.derived_from:
            if ref in self.state or ref.split(":", 1)[0] in ("source", "model", "user"):
                continue
            return False, f"dangling provenance reference {ref!r}"
        return True, "provenance ok"

    def _frame_role_ok(self, obj: StateObject) -> tuple[bool, str]:
        # Role-affecting kinds may not carry an uncleared role/framing taint.
        if obj.kind in ("role", "goal", "method_rule") and obj.taint:
            return False, f"frame/role taint not cleared: {sorted(obj.taint)}"
        return True, "frame/role ok"

    def _conflict_ok(self, obj: StateObject) -> tuple[bool, str]:
        # A candidate may not contradict an existing control object (e.g.
        # re-defining a forbidden_transfer or disabling a protection rule).
        for existing in self.state.values():
            if existing.authority != "control":
                continue
            if obj.payload.get("overrides") == existing.obj_id:
                return False, f"attempts to override control object {existing.obj_id}"
            if (obj.kind == existing.kind
                    and obj.payload.get("name") == existing.payload.get("name")
                    and obj.payload.get("disable") is True):
                return False, f"attempts to disable control object {existing.obj_id}"
        return True, "no conflict"

    def _independent_verification_ok(self, obj: StateObject,
                                     target: str) -> tuple[bool, str]:
        # Promotion to verified/control needs verification independent of the
        # producer: not all provenance may come from a single model, and a
        # majority vote of models cannot by itself overturn control state.
        if not authority_at_least(target, "verified"):
            return True, "no verification required below verified"
        model_refs = [r for r in obj.derived_from if r.startswith("model")]
        non_model = [r for r in obj.derived_from
                     if not r.startswith("model") and r not in ("",)]
        if model_refs and not non_model:
            return False, "no verification independent of the producing model(s)"
        if not obj.eligible_for_control_state:
            return False, "tainted/adversarially-exposed object cannot be promoted"
        return True, "independently verifiable"

    def _status_change_ok(self, obj: StateObject, target: str,
                          token: str | None) -> tuple[bool, str]:
        # Model output never reaches verified directly.
        if "model" in obj.origins and target == "verified" and len(obj.origins) == 1:
            # allowed only with an explicit controller token (the controller
            # took responsibility for verifying it)
            if token not in self._tokens:
                return False, "model output cannot reach verified without controller token"
        # Control authority and control-sensitive kinds require a system_policy
        # token — a higher clearance than a normal claim.
        needs_token = (target == "control") or (obj.kind in CONTROL_SENSITIVE_KINDS)
        if needs_token and token not in self._tokens:
            return False, ("control-sensitive change requires a system_policy token "
                           f"(kind={obj.kind}, target={target})")
        return True, "status change permitted"

    # --- the gate ------------------------------------------------------------

    def submit(self, obj: StateObject, target_authority: str = "candidate",
               *, token: str | None = None) -> GateDecision:
        """Run the pipeline; admit at the highest safe authority, or reject."""
        d = GateDecision(obj_id=obj.obj_id, requested=target_authority,
                         admitted_authority="rejected", accepted=False, rejected=True)

        steps = [
            ("schema", self._schema_ok(obj)),
            ("provenance", self._provenance_ok(obj)),
            ("frame_role", self._frame_role_ok(obj)),
            ("conflict", self._conflict_ok(obj)),
            ("independent_verification", self._independent_verification_ok(obj, target_authority)),
            ("status_change", self._status_change_ok(obj, target_authority, token)),
        ]
        for name, (ok, reason) in steps:
            d.checks[name] = ok
            d.reasons.append(f"{name}: {reason}")
            # schema / provenance / frame-role / conflict failures reject outright
            if not ok and name in ("schema", "provenance", "frame_role", "conflict"):
                d.admitted_authority, d.accepted, d.rejected = "rejected", False, True
                self.ledger.record("control_plane_reject",
                                   {"obj_id": obj.obj_id, "stage": name, "reason": reason})
                return d

        # verification / status-change failures DOWNGRADE to candidate rather
        # than reject — the object is retained but cannot steer.
        if d.checks["independent_verification"] and d.checks["status_change"]:
            admitted = target_authority
        else:
            admitted = "candidate"

        d.admitted_authority = admitted
        d.accepted = (admitted == target_authority)
        d.rejected = False
        promoted = StateObject(
            obj_id=obj.obj_id, kind=obj.kind, payload=obj.payload,
            origins=obj.origins, authority=admitted,
            derived_from=obj.derived_from, exposure=obj.exposure, taint=obj.taint,
        )
        # only verified/control objects enter the authoritative state
        if authority_at_least(admitted, "verified"):
            self.state[obj.obj_id] = promoted
        self.ledger.record("control_plane_update", {
            "obj_id": obj.obj_id, "kind": obj.kind,
            "admitted_authority": admitted, "accepted": d.accepted,
        })
        return d
