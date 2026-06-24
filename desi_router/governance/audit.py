"""Audit record for one router-governance decision — deterministic and tamper-evident.

Mirrors ``desi_router.audit.AuditRecord``: it hashes the canonical (report-hash + decision +
post-check + update-allowed) so the governance decision is replay-stable, just like the routing
decision. Can be appended to the existing router ledger (``ledger.record``) by the caller.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from desi_router.governance.modes import RouterDecision
from desi_router.governance.report import DesiReport
from desi_router.governance.verifier import VerifierResult


@dataclass
class GovernanceAudit:
    report_hash: str
    decision: dict[str, Any]
    post_check: dict[str, Any] | None = None
    persistent_state_update_allowed: bool = False
    event_id: str = field(default="", init=False)

    def __post_init__(self) -> None:
        canonical = json.dumps(
            {"report_hash": self.report_hash, "decision": self.decision,
             "post_check": self.post_check,
             "persistent_state_update_allowed": self.persistent_state_update_allowed},
            sort_keys=True, ensure_ascii=False)
        self.event_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) | {"event_id": self.event_id}


def audit_event(report: DesiReport, decision: RouterDecision,
                verifier: VerifierResult | None = None,
                *, update_allowed: bool | None = None) -> GovernanceAudit:
    rec = GovernanceAudit(
        report_hash=report.audit_hash, decision=decision.to_dict(),
        post_check=(verifier.to_dict() if verifier is not None else None),
        persistent_state_update_allowed=bool(
            decision.persistent_state_update_allowed if update_allowed is None else update_allowed))
    decision.audit_event_id = rec.event_id
    return rec
