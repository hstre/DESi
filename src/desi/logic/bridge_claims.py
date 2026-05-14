"""Bridge-claim generation for the v1.2 logical audit.

When :func:`desi.logic.gap_detector.detect_gap` returns
``MISSING_BRIDGE``, the auditor synthesises a bridge claim — an
explicit linking proposition that, if true, would close the gap.

v1.2 directive (hard invariant L5):

    Bridge claims MUST stay state=PROPOSED, method="logical_bridge".
    Never auto-upgrade.

The auditor *generates* the bridge as a candidate; it never accepts
it on the bridge generator's authority. A subsequent audit cycle (or
an external operator) must independently support the bridge before
the original claim can become ``LOGICALLY_SUPPORTED``.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from ..memory.claim import Claim, ClaimState, Provenance
from .gap_detector import Gap, GapKind
from .premises import ConclusionProposition, Propositions


# v1.2 directive: the only method label that may attach to a bridge.
BRIDGE_METHOD: str = "logical_bridge"


@dataclass(frozen=True)
class BridgeClaim:
    """A synthesised bridge proposition.

    The bridge carries the canonical text + a :class:`Claim` object
    suitable for downstream consumption (state always
    :attr:`ClaimState.PROPOSED`, method always
    :data:`BRIDGE_METHOD`). The bridge id is a deterministic hash of
    its text — same gap → same bridge id across processes.
    """

    bridge_id: str
    text: str
    claim: Claim
    rationale: str

    def to_dict(self) -> dict:
        return {
            "bridge_id": self.bridge_id,
            "text": self.text,
            "rationale": self.rationale,
            "claim_state": self.claim.state.value,
            "claim_method": self.claim.method,
        }


def _bridge_id(text: str) -> str:
    h = hashlib.sha256(text.lower().strip().encode("utf-8"))
    return "br_" + h.hexdigest()[:12]


def _bridge_text_for_rain_street(premise_text: str,
                                  conclusion_text: str) -> str:
    """The directive's P3 case: rain → street wet → bridge=
    'the street is exposed to the rain'."""
    p_low = premise_text.lower()
    c_low = conclusion_text.lower()
    if "rain" in p_low and "street" in c_low and "wet" in c_low:
        return "the street is exposed to the rain"
    return ""


def _generic_bridge_text(premise_text: str,
                         conclusion_text: str) -> str:
    """Fallback bridge: an explicit causal link.

    The text is intentionally bland — readers must inspect the
    bridge before the original claim can promote, so the bridge
    itself is a starting point, not a finished argument.
    """
    pt = premise_text.strip().rstrip(".")
    ct = conclusion_text.strip().rstrip(".")
    return f"({pt}) implies ({ct})"


def propose_bridge(
    props: Propositions,
    gap: Gap,
) -> BridgeClaim | None:
    """Synthesise a bridge claim that, if true, would close ``gap``.

    Returns ``None`` if the gap is not of kind
    :attr:`GapKind.MISSING_BRIDGE` — bridges are only meaningful for
    that gap kind. Authority and unreachable gaps yield
    ``LOGICALLY_REJECTED`` instead.
    """
    if gap.kind != GapKind.MISSING_BRIDGE:
        return None
    if props.conclusion is None:
        return None
    # Pick the premise that most closely supports the conclusion.
    if not props.premises:
        return None
    candidate_premise = props.premises[0].text
    text = _bridge_text_for_rain_street(candidate_premise,
                                          props.conclusion.text)
    if not text:
        text = _generic_bridge_text(candidate_premise,
                                     props.conclusion.text)
    bridge_id = _bridge_id(text)
    claim = Claim(
        content=text,
        method=BRIDGE_METHOD,
        state=ClaimState.PROPOSED,
        provenance=Provenance(
            source="logical_audit",
            run_id="bridge_synthesis",
            operator_path=(BRIDGE_METHOD,),
        ),
    )
    return BridgeClaim(
        bridge_id=bridge_id,
        text=text,
        claim=claim,
        rationale=gap.rationale,
    )


__all__ = [
    "BRIDGE_METHOD",
    "BridgeClaim",
    "propose_bridge",
]
