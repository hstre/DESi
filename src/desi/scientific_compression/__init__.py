"""DESi v22.1 - Governance Compression (read-only).

DESi scales overclaims and hidden-authority claims down to
sandbox-scoped statements while keeping the technical content
and making the limits explicit - compression without
hollowing.
"""
from __future__ import annotations

from .authority_filter import (
    authority_resistance, authority_statements,
    no_authority_survives,
)
from .claim_scaling import (
    CLAIM_KINDS, ClaimKind, ClaimStatement, by_id,
    overclaim_reduction, overclaim_statements, statements,
    technical_preservation, technical_statements,
)
from .compression import (
    compression_is_clean, governed_forbidden_count,
    governed_overclaim_count,
)
from .report import (
    REPORT_VERDICTS, VERDICT_COMPRESSED, VERDICT_HALT,
    VERDICT_HOLLOW, V221Report, build_compression_artifact,
    build_report,
)
from .scientific_limits import (
    limitation_statements, limitations_visibility,
    sandbox_honesty,
)


__all__ = [
    "CLAIM_KINDS",
    "REPORT_VERDICTS",
    "VERDICT_COMPRESSED",
    "VERDICT_HALT",
    "VERDICT_HOLLOW",
    "ClaimKind",
    "ClaimStatement",
    "V221Report",
    "authority_resistance",
    "authority_statements",
    "build_compression_artifact",
    "build_report",
    "by_id",
    "compression_is_clean",
    "governed_forbidden_count",
    "governed_overclaim_count",
    "limitation_statements",
    "limitations_visibility",
    "no_authority_survives",
    "overclaim_reduction",
    "overclaim_statements",
    "sandbox_honesty",
    "statements",
    "technical_preservation",
    "technical_statements",
]
