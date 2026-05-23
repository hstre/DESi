"""10 mixed-frame paraphrases — Aufgabe 7.

Each carries `entropy` plus tokens that LOOK info-theoretic
(``bits``, ``Shannon``, ``coding``…) but the ground-truth frame
is **not** information-theoretic. A disambiguator candidate must
not absorb any of these — if it does, its
``negative_control_precision`` drops below 1.0 and the audit
disqualifies it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..frames import FrameKind


@dataclass(frozen=True)
class MixedCase:
    nc_id: str
    text: str
    expected_frame: FrameKind

    def to_dict(self) -> dict[str, Any]:
        return {
            "nc_id": self.nc_id,
            "text": self.text,
            "expected_frame": self.expected_frame.value,
        }


NEGATIVE_CONTROLS: tuple[MixedCase, ...] = (
    MixedCase(
        nc_id="MC01",
        text=(
            "Frame: thermodynamic. Entropy in heat reservoirs "
            "is unrelated to bits."
        ),
        expected_frame=FrameKind.THERMODYNAMIC,
    ),
    MixedCase(
        nc_id="MC02",
        text=(
            "Frame: thermodynamic. Entropy in a message-laden "
            "warm gas at high temperature."
        ),
        expected_frame=FrameKind.THERMODYNAMIC,
    ),
    MixedCase(
        nc_id="MC03",
        text=(
            "Frame: thermodynamic. Entropy in a closed system "
            "with Shannon-shaped pressure variations."
        ),
        expected_frame=FrameKind.THERMODYNAMIC,
    ),
    MixedCase(
        nc_id="MC04",
        text=(
            "Frame: metaphorical. The poet's entropy in bits of "
            "Shannon-style verse is fleeting."
        ),
        expected_frame=FrameKind.METAPHORICAL,
    ),
    MixedCase(
        nc_id="MC05",
        text=(
            "Frame: metaphorical. Loosely speaking the brain's "
            "entropy uses bits like a coding scheme."
        ),
        expected_frame=FrameKind.METAPHORICAL,
    ),
    MixedCase(
        nc_id="MC06",
        text=(
            "Frame: thermodynamic. Heat entropy in joule-per-kelvin "
            "with negligible bit-coding overhead."
        ),
        expected_frame=FrameKind.THERMODYNAMIC,
    ),
    MixedCase(
        nc_id="MC07",
        text=(
            "Frame: metaphorical. Like a Shannon library the brain "
            "carries entropy in bits of memory."
        ),
        expected_frame=FrameKind.METAPHORICAL,
    ),
    MixedCase(
        nc_id="MC08",
        text=(
            "Frame: thermodynamic. Adiabatic compression raises "
            "temperature and entropy without involving Shannon bits."
        ),
        expected_frame=FrameKind.THERMODYNAMIC,
    ),
    MixedCase(
        nc_id="MC09",
        text=(
            "Frame: metaphorical. In a sense the heat-entropy of the "
            "market codes bits of investor sentiment."
        ),
        expected_frame=FrameKind.METAPHORICAL,
    ),
    MixedCase(
        nc_id="MC10",
        text=(
            "Frame: thermodynamic. Closed-system entropy plus a "
            "kelvin gradient unrelated to information coding."
        ),
        expected_frame=FrameKind.THERMODYNAMIC,
    ),
)


__all__ = ["NEGATIVE_CONTROLS", "MixedCase"]
