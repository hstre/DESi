"""desi.reviewer - stable facade for the Reviewer Port.

    from desi.reviewer import reviewer_port

The Reviewer Port maps to two real subsystems
(desi.readme_self_review.reviewer_port and desi.scientific_reviewers);
this facade does not invent capability.
"""
from __future__ import annotations

from . import reviewer_port

__all__ = ["reviewer_port"]
