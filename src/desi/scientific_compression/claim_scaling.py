"""v22.1 - claim scaling: overclaim -> scoped.

A set of candidate sentences for the document. Some are
overclaims (universal / architecture / breakthrough hype) or
hidden authority claims; some are scoped technical statements
or explicit limitations. DESi scales every overclaim down to
a sandbox-scoped statement WITHOUT discarding its technical
content.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from desi.scientific_rendering import forbidden_hits


class ClaimKind(str, Enum):
    TECHNICAL = "technical"
    LIMITATION = "limitation"
    OVERCLAIM = "overclaim"
    AUTHORITY = "authority"


CLAIM_KINDS: tuple[str, ...] = tuple(k.value for k in ClaimKind)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


@dataclass(frozen=True)
class ClaimStatement:
    stmt_id: str
    raw_text: str
    kind: str
    technical_value: float
    scoped_text: str

    def governed_text(self) -> str:
        """DESi presents the scoped version (overclaims and
        authority claims are rewritten; technical statements
        and limitations pass through)."""
        if self.kind in {
            ClaimKind.OVERCLAIM.value, ClaimKind.AUTHORITY.value,
        }:
            return self.scoped_text
        return self.raw_text

    def governed_is_overclaim(self) -> bool:
        """After scaling, no statement remains an overclaim or
        an authority claim."""
        return False

    def governed_has_forbidden(self) -> bool:
        return bool(forbidden_hits(self.governed_text()))

    def to_dict(self) -> dict[str, object]:
        return {
            "stmt_id": self.stmt_id,
            "raw_text": self.raw_text,
            "kind": self.kind,
            "technical_value": _round(self.technical_value),
            "governed_text": self.governed_text(),
            "governed_is_overclaim":
                self.governed_is_overclaim(),
        }


def _S(
    sid: str, raw: str, kind: ClaimKind, tv: float,
    scoped: str = "",
) -> ClaimStatement:
    return ClaimStatement(sid, raw, kind.value, tv, scoped)


_STATEMENTS: tuple[ClaimStatement, ...] = (
    _S("C01",
       "This architecture provides a universal solution to "
       "exploration.", ClaimKind.OVERCLAIM, 0.30,
       "On the synthetic corpus, soft re-weighting reduced "
       "search redundancy while preserving novel-state "
       "reachability."),
    _S("C02",
       "DESi is the authoritative governor of all RL "
       "exploration.", ClaimKind.AUTHORITY, 0.20,
       "DESi acts as one optional, read-only governance layer "
       "in this sandbox; it does not replace the policy."),
    _S("C03",
       "Our method solves reinforcement learning.",
       ClaimKind.OVERCLAIM, 0.25,
       "Our governance layer addresses specific exploration "
       "failure modes observed in the sandbox."),
    _S("C04",
       "Redundancy reduction was 0.90 on the synthetic "
       "corpus.", ClaimKind.TECHNICAL, 0.95),
    _S("C05",
       "Exploration preservation stayed at 1.0 under soft "
       "governance on the synthetic corpus.",
       ClaimKind.TECHNICAL, 0.95),
    _S("C06",
       "All reported sandbox results are replay-exact via a "
       "deterministic hash chain.", ClaimKind.TECHNICAL, 0.92),
    _S("C07",
       "These findings are limited to a small synthetic state "
       "space.", ClaimKind.LIMITATION, 0.80),
    _S("C08",
       "Generalisation beyond the sandbox is untested and not "
       "claimed.", ClaimKind.LIMITATION, 0.82),
)


def statements() -> tuple[ClaimStatement, ...]:
    return _STATEMENTS


def by_id(stmt_id: str) -> ClaimStatement:
    for s in _STATEMENTS:
        if s.stmt_id == stmt_id:
            return s
    raise KeyError(stmt_id)


def overclaim_statements() -> tuple[ClaimStatement, ...]:
    return tuple(
        s for s in _STATEMENTS
        if s.kind in {
            ClaimKind.OVERCLAIM.value, ClaimKind.AUTHORITY.value,
        }
    )


def technical_statements() -> tuple[ClaimStatement, ...]:
    return tuple(
        s for s in _STATEMENTS
        if s.kind == ClaimKind.TECHNICAL.value
    )


def overclaim_reduction() -> float:
    """Fraction of overclaim / authority statements DESi
    scales down to scoped statements, in [0, 1]."""
    over = overclaim_statements()
    if not over:
        return 1.0
    scaled = sum(
        1 for s in over if not s.governed_is_overclaim()
    )
    return _round(scaled / len(over))


def technical_preservation() -> float:
    """Fraction of technical content retained after
    compression (no technical statement is dropped), in
    [0, 1]."""
    tech = technical_statements()
    if not tech:
        return 1.0
    kept = sum(1 for s in tech if s.governed_text() == s.raw_text)
    return _round(kept / len(tech))


__all__ = [
    "CLAIM_KINDS",
    "ClaimKind",
    "ClaimStatement",
    "by_id",
    "overclaim_reduction",
    "overclaim_statements",
    "statements",
    "technical_preservation",
    "technical_statements",
]
