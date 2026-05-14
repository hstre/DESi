"""Bridge state transitions enforced by the v1.3 consilium.

A bridge that enters the consilium is in :class:`BridgeState.UNDER_CONSILIUM`.
After the verdict it transitions to exactly one of
``CONSILIUM_ACCEPTED``, ``CONSILIUM_REJECTED``, or
``CONSILIUM_BLOCKED``.

An *accepted* bridge may be promoted from
:attr:`desi.memory.claim.ClaimState.PROPOSED` to
:attr:`desi.memory.claim.ClaimState.LOGICALLY_SUPPORTED`. The
``method`` field is preserved verbatim — v1.2's
``"logical_bridge"`` stays. Anything else is a structural rewrite
and the consilium refuses to perform it.

The original claim (the one whose v1.2 audit returned
``BRIDGE_REQUIRED``) may transition from
:attr:`ClaimState.BRIDGE_REQUIRED` to
:attr:`ClaimState.LOGICALLY_SUPPORTED` *only* after an accepted
bridge replay has succeeded — :func:`upgrade_original_claim`
enforces this precondition.
"""
from __future__ import annotations

from ..memory.claim import Claim, ClaimState, Provenance
from ..logic.bridge_claims import BRIDGE_METHOD, BridgeClaim
from .verdict import BridgeState, ConsiliumVerdict, Verdict


def promote_accepted_bridge(
    bridge: BridgeClaim,
    verdict: ConsiliumVerdict,
) -> Claim:
    """Return a new :class:`Claim` for the accepted bridge.

    The returned claim:

    * keeps ``method == "logical_bridge"`` verbatim;
    * keeps the bridge's text and content unchanged;
    * has ``state == LOGICALLY_SUPPORTED``;
    * carries fresh provenance whose ``operator_path`` records the
      consilium step.

    Raises ``ValueError`` if the verdict is not
    :attr:`Verdict.ACCEPT_AS_BRIDGE`.
    """
    if verdict.verdict is not Verdict.ACCEPT_AS_BRIDGE:
        raise ValueError(
            "promote_accepted_bridge requires verdict=ACCEPT_AS_BRIDGE "
            f"(got {verdict.verdict.value})"
        )
    if bridge.claim.method != BRIDGE_METHOD:
        raise ValueError(
            f"bridge claim method must remain '{BRIDGE_METHOD}'; "
            f"got '{bridge.claim.method}'"
        )
    prov = Provenance(
        source="bridge_consilium",
        run_id=f"consilium_accept_{verdict.bridge_id}",
        operator_path=(BRIDGE_METHOD, "consilium_accept"),
    )
    return Claim(
        content=bridge.claim.content,
        method=BRIDGE_METHOD,
        state=ClaimState.LOGICALLY_SUPPORTED,
        confidence=bridge.claim.confidence,
        provenance=prov,
    )


class ClaimUpgradeError(Exception):
    """Raised when an original claim upgrade precondition is not met."""


def upgrade_original_claim(
    original: Claim,
    *,
    accepted_bridge_state: BridgeState,
    verdict: Verdict,
) -> Claim:
    """Return a new :class:`Claim` for the original claim, upgraded to
    :attr:`ClaimState.LOGICALLY_SUPPORTED`.

    Preconditions (enforced):

    * the original claim must be in :attr:`ClaimState.BRIDGE_REQUIRED`;
    * the bridge must already be in
      :attr:`BridgeState.CONSILIUM_ACCEPTED`;
    * the verdict must be :attr:`Verdict.ACCEPT_AS_BRIDGE`.

    The original's ``method`` and ``content`` are preserved. The
    new provenance records ``consilium_upgrade`` in its operator
    path so the audit trail names the upgrade event.
    """
    if original.state is not ClaimState.BRIDGE_REQUIRED:
        raise ClaimUpgradeError(
            "original claim must be BRIDGE_REQUIRED to upgrade; "
            f"got {original.state.value}"
        )
    if accepted_bridge_state is not BridgeState.CONSILIUM_ACCEPTED:
        raise ClaimUpgradeError(
            "bridge must be in CONSILIUM_ACCEPTED to upgrade the "
            f"original; got {accepted_bridge_state.value}"
        )
    if verdict is not Verdict.ACCEPT_AS_BRIDGE:
        raise ClaimUpgradeError(
            "consilium verdict must be ACCEPT_AS_BRIDGE to upgrade "
            f"the original; got {verdict.value}"
        )
    prov = Provenance(
        source="bridge_consilium",
        run_id=f"consilium_upgrade_{original.claim_id}",
        operator_path=original.provenance.operator_path + (
            "consilium_upgrade",
        ),
    )
    return Claim(
        content=original.content,
        method=original.method,
        state=ClaimState.LOGICALLY_SUPPORTED,
        confidence=original.confidence,
        provenance=prov,
    )


__all__ = [
    "ClaimUpgradeError",
    "promote_accepted_bridge",
    "upgrade_original_claim",
]
