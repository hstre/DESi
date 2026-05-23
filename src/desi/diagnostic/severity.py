"""Severity + confidence scoring (Aufgabe 4).

Both scores live in ``[0.0, 1.0]`` and are derived **only from
data** — never from metadata (author, journal, citation count,
prestige). A "metadata storm" — attaching irrelevant fields to a
deficit's source records — must not move either score.

* ``severity`` = how broadly the deficit shows up
* ``confidence`` = how robust the *detection* is
"""
from __future__ import annotations


def severity_from_coverage(
    affected_cases: int,
    total_cases: int,
) -> float:
    """Pure ratio. Returns 0.0 when ``total_cases == 0``."""
    if total_cases <= 0:
        return 0.0
    return round(min(1.0, max(0.0, affected_cases / total_cases)), 6)


def confidence_score(
    *,
    frequency: int,
    reproducibility: float,
    cross_source_consistency: float,
    self_reference: bool = False,
) -> float:
    """Combine three orthogonal evidence axes into one score.

    Parameters
    ----------
    frequency:
        Raw count of how many independent observations support the
        deficit. Mapped through a saturating curve so a single
        observation already yields 0.5 confidence; 5+ yields ~1.0.
    reproducibility:
        ``[0.0, 1.0]``. 1.0 when two runs of the underlying detector
        produced identical results (e.g. replay_hash equality).
    cross_source_consistency:
        ``[0.0, 1.0]``. 1.0 when the deficit was observed from at
        least two independent sources (e.g. benchmark + sandbox).
    self_reference:
        When True, the deficit was detected and evaluated by the
        same mechanism. Confidence is halved as a self-deception
        guard (Aufgabe 8).
    """
    if frequency <= 0:
        freq_axis = 0.0
    else:
        freq_axis = round(min(1.0, 0.5 + 0.125 * (frequency - 1)), 6)
    repro_axis = max(0.0, min(1.0, float(reproducibility)))
    cross_axis = max(0.0, min(1.0, float(cross_source_consistency)))
    raw = (freq_axis + repro_axis + cross_axis) / 3.0
    if self_reference:
        raw *= 0.5
    return round(max(0.0, min(1.0, raw)), 6)


__all__ = ["confidence_score", "severity_from_coverage"]
