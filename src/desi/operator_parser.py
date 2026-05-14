"""DES upstream operator-string parser.

DES upstream emits operator strings in three observed forms (from
`hstre/DES`'s real `operation_history`):

    1.  "T3 on C001"
    2.  "T6[hypothesis_builder] on C002 -> C004"
    3.  "T5[falsifier] on C003 -> C006"

Form 1 is what DESi's hand-authored fixtures use. Forms 2 and 3 carry
a sub-role annotation (`[hypothesis_builder]`, `[falsifier]`) and a
child-claim reference (`-> Cyyy`). The richer information is real DES
output. Pre-fix-2 DESi's regex matched only form 1; forms 2 and 3
were silently substituted as `UNKNOWN` operators, which cascaded into
spurious Phase V triggers (see
`experiments/external_reality_challenge/cycle_2/evaluation.md`,
"Failure 4").

This module exposes:

    parse_des_operation(s) -> ParsedOperation | OperatorParseFailure

`ParsedOperation` carries the canonical T-code plus the structured
sub-role / target metadata. `OperatorParseFailure` is an explicit
sentinel — when a caller encounters one, it MUST emit
`OPERATOR_PARSE_FAILURE` rather than silently substituting `UNKNOWN`.

DESi's `compute_all` is unaffected; this is a translator-side helper.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Form 1:  T3 on C001
# Form 2:  T6[hypothesis_builder] on C002 -> C004
_OP_PATTERN = re.compile(
    r"^\s*"
    r"(T\d)"                                # canonical T-code
    r"(?:\[([^\]]+)\])?"                    # optional sub-role
    r"\s+on\s+"
    r"(\S+?)"                               # source claim id
    r"(?:\s*->\s*(\S+))?"                   # optional target claim id
    r"\s*$",
    re.IGNORECASE,
)


# Sentinel emitted by callers that want "I know I could not parse this".
# Distinct from "UNKNOWN" which is the pre-fix-2 silent-substitution token.
OPERATOR_PARSE_FAILURE = "OPERATOR_PARSE_FAILURE"


@dataclass(frozen=True)
class ParsedOperation:
    """Structured form of a successfully-parsed DES operation string."""
    raw: str
    operator: str               # canonical T-code, upper-case
    sub_role: str | None        # "hypothesis_builder" / "falsifier" / None
    source_claim: str           # focus claim id (canonical "Cxxx")
    target_claim: str | None    # output-of-operation claim id, if present


@dataclass(frozen=True)
class OperatorParseFailure:
    """Explicit parse failure. Carries the raw string for audit."""
    raw: str

    @property
    def operator(self) -> str:
        return OPERATOR_PARSE_FAILURE

    @property
    def sub_role(self) -> None:
        return None

    @property
    def source_claim(self) -> str:
        return ""

    @property
    def target_claim(self) -> None:
        return None


def parse_des_operation(raw: str) -> ParsedOperation | OperatorParseFailure:
    """Parse an upstream DES operation_history string.

    Returns ParsedOperation if the regex matched (covers both
    "T3 on C001" and "T6[hypothesis_builder] on C002 -> C004").
    Returns OperatorParseFailure otherwise — the caller is responsible
    for emitting OPERATOR_PARSE_FAILURE explicitly and NOT silently
    falling back to UNKNOWN.
    """
    if not isinstance(raw, str):
        return OperatorParseFailure(raw=str(raw))
    m = _OP_PATTERN.match(raw)
    if not m:
        return OperatorParseFailure(raw=raw)
    op, sub, src, tgt = m.group(1), m.group(2), m.group(3), m.group(4)
    return ParsedOperation(
        raw=raw,
        operator=op.upper(),
        sub_role=sub or None,
        source_claim=src,
        target_claim=tgt,
    )


def parse_many(ops: list[str]) -> list[ParsedOperation | OperatorParseFailure]:
    return [parse_des_operation(o) for o in ops]
