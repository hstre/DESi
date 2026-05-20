"""VetoToTestSynthesiser — convert valid Vetos into test obligations.

A valid veto blocks promotion. v0.6 promotes "blocked" into
"actionable": every valid veto becomes a :class:`VetoTestObligation`
with an explicit status flow. The synthesiser also produces a pytest
skeleton from the veto's structured fields so that the obligation can
be turned into a runnable test by a human ratifier.
"""
from __future__ import annotations

import pathlib
import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .jury import Veto


class ObligationStatus(str, Enum):
    """Closed lifecycle for a veto-driven test obligation."""

    OPEN = "open"
    IMPLEMENTED = "implemented"
    PASSED = "passed"
    FAILED = "failed"
    WAIVED = "waived"


_TERMINAL_STATES: frozenset[ObligationStatus] = frozenset({
    ObligationStatus.PASSED,
    ObligationStatus.WAIVED,
})


def is_resolved(status: ObligationStatus) -> bool:
    """``True`` if the status counts as resolved for promotion-gate.

    PASSED is the happy path. WAIVED is the documented escape hatch
    (a human ratifier marks the obligation as not-applicable with
    an explanatory note). FAILED keeps blocking. IMPLEMENTED keeps
    blocking until the test actually runs green.
    """
    return status in _TERMINAL_STATES


class VetoTestObligation(BaseModel):
    """One test obligation derived from a valid veto."""

    model_config = ConfigDict(extra="forbid")

    obligation_id: str = Field(
        default_factory=lambda: "obl_" + uuid.uuid4().hex[:12],
    )
    source_veto_id: str = Field(..., min_length=1)
    affected_claim: str = Field(..., min_length=1)
    risk: str = Field(..., min_length=1)
    failure_case: str = Field(..., min_length=1)
    proposed_test: str = Field(..., min_length=1)
    status: ObligationStatus = Field(default=ObligationStatus.OPEN)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    # Free-form note required when the status moves to WAIVED, so the
    # waiver is auditable.
    waiver_rationale: str = Field(default="")

    @property
    def is_resolved(self) -> bool:
        return is_resolved(self.status)

    def with_status(
        self,
        new_status: ObligationStatus,
        *,
        waiver_rationale: str = "",
    ) -> "VetoTestObligation":
        """Return a NEW obligation reflecting the status change.

        The original instance is untouched. This is the ledger-friendly
        update path: callers append a new ledger entry containing the
        new obligation rather than mutating the old one.
        """
        if new_status is ObligationStatus.WAIVED and not waiver_rationale:
            raise ValueError(
                "WAIVED requires a non-empty waiver_rationale; v0.6 "
                "audit refuses to record an unjustified waiver."
            )
        return self.model_copy(update={
            "status": new_status,
            "waiver_rationale": waiver_rationale,
        })


def _sanitise(s: str, *, max_len: int = 40) -> str:
    """Make a string safe for use as a python identifier suffix."""
    cleaned = re.sub(r"[^a-zA-Z0-9_]+", "_", s).strip("_").lower()
    return cleaned[:max_len] or "veto"


class VetoToTestSynthesiser:
    """Builds :class:`VetoTestObligation` records from valid Vetos.

    The synthesiser also produces a pytest skeleton string. Writing
    the skeleton to disk is opt-in via :meth:`write_skeleton`; the
    base call returns the text only.
    """

    DEFAULT_DIR: pathlib.Path = pathlib.Path("tests/evolution/veto_followups")

    def __init__(
        self,
        *,
        output_dir: pathlib.Path | str | None = None,
    ) -> None:
        self.output_dir = pathlib.Path(output_dir) if output_dir else \
            self.DEFAULT_DIR

    # ------------------------------------------------------------------
    # Synthesis
    # ------------------------------------------------------------------

    def synthesise(
        self,
        veto: Veto,
        *,
        source_veto_id: str | None = None,
    ) -> VetoTestObligation:
        if not veto.is_valid:
            raise ValueError(
                "VetoToTestSynthesiser refuses to build an obligation "
                "from an invalid veto; v0.6 directive: invalid vetos "
                "are discarded, not productive."
            )
        return VetoTestObligation(
            source_veto_id=source_veto_id or _veto_fingerprint(veto),
            affected_claim=veto.affected_claim,
            risk=veto.suspected_risk,
            failure_case=veto.failure_case,
            proposed_test=veto.proposed_test,
        )

    def pytest_skeleton(self, obligation: VetoTestObligation) -> str:
        """Return a runnable pytest skeleton as a string.

        The skeleton contains the risk, failure case, and proposed test
        as a structured docstring and a single failing assert so that
        the obligation surfaces in CI until a human implements it.
        """
        test_fn = f"test_veto_followup_{_sanitise(obligation.affected_claim)}_" \
                  f"{obligation.obligation_id[-8:]}"
        body = (
            f'"""Auto-generated from veto obligation '
            f'{obligation.obligation_id}.\n'
            f'\n'
            f'Affected claim : {obligation.affected_claim}\n'
            f'Risk           : {obligation.risk}\n'
            f'Failure case   : {obligation.failure_case}\n'
            f'\n'
            f'Proposed test  : {obligation.proposed_test}\n'
            f'\n'
            f"Source veto id : {obligation.source_veto_id}\n"
            f'Status         : {obligation.status.value}\n'
            f'"""\n'
        )
        skeleton = (
            f"# Auto-generated by VetoToTestSynthesiser.\n"
            f"# obligation_id: {obligation.obligation_id}\n"
            f"# DO NOT EDIT the metadata block; implement the test below.\n"
            f"import pytest\n"
            f"\n"
            f"def {test_fn}() -> None:\n"
            f"    {body}"
            f"    pytest.fail(\n"
            f"        f\"veto obligation {obligation.obligation_id} not \"\n"
            f"        f\"yet implemented; risk: {obligation.risk!r}\"\n"
            f"    )\n"
        )
        return skeleton

    def write_skeleton(
        self,
        obligation: VetoTestObligation,
        *,
        output_dir: pathlib.Path | str | None = None,
    ) -> pathlib.Path:
        """Write the pytest skeleton to a file. Opt-in only."""
        out_dir = pathlib.Path(output_dir) if output_dir else self.output_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"test_veto_followup_"
            f"{_sanitise(obligation.affected_claim)}_"
            f"{obligation.obligation_id[-8:]}.py"
        )
        path = out_dir / filename
        path.write_text(self.pytest_skeleton(obligation))
        return path


def _veto_fingerprint(veto: Veto) -> str:
    """Stable identifier for a veto object that the caller did not name."""
    raw = "\x00".join([
        veto.role.value,
        veto.affected_claim,
        veto.suspected_risk,
        veto.failure_case,
        veto.proposed_test,
    ]).encode("utf-8")
    import hashlib
    return "veto_" + hashlib.sha256(raw).hexdigest()[:12]


__all__ = [
    "ObligationStatus",
    "VetoTestObligation",
    "VetoToTestSynthesiser",
    "is_resolved",
]
