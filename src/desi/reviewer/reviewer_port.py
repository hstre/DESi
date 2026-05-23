"""desi.reviewer.reviewer_port - the Reviewer Port (honest mapping).

The Reviewer Port is not a single hidden module; it is implemented
concretely by two real subsystems, which this facade maps cleanly
(nothing is invented or faked):

* desi.readme_self_review.reviewer_port - the claim / overreach audit
  used to review DESi's own documentation as an external claim
  artifact (extraction, forbidden-term scan, consistency checks).
* desi.scientific_reviewers - the role-based skeptical reviewer
  subsystem (reviewer attacks, hype resistance, response governance).

This module re-exports both so that

    from desi.reviewer import reviewer_port

resolves to a working, real implementation.
"""
from __future__ import annotations

# Documentation claim/overreach audit (the README self-review port).
from desi.readme_self_review.reviewer_port import (
    AUDIT_FRAMING, forbidden_term_hits, reviewed_hash,
)
from desi.readme_self_review import (
    build_claim_audit_artifact, claims, gate_conditions,
    gate_passes_all, recommendation,
)

# Role-based skeptical reviewer subsystem.
from desi import scientific_reviewers as role_reviewers

IMPLEMENTED_BY = (
    "desi.readme_self_review.reviewer_port",
    "desi.scientific_reviewers",
)


def claim_audit() -> dict:
    """Run the documentation claim/overreach audit (real)."""
    return build_claim_audit_artifact()


def role_review_report():
    """Run the role-based skeptical reviewer (real)."""
    return role_reviewers.build_report()


__all__ = [
    "AUDIT_FRAMING",
    "IMPLEMENTED_BY",
    "build_claim_audit_artifact",
    "claim_audit",
    "claims",
    "forbidden_term_hits",
    "gate_conditions",
    "gate_passes_all",
    "recommendation",
    "reviewed_hash",
    "role_review_report",
    "role_reviewers",
]
