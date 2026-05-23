"""v13.3 — closed-enum integrity check across
the 5000-step trajectory."""
from __future__ import annotations

from .ecology import trajectory


def closed_enum_hash_constant() -> bool:
    hashes = {
        s.closed_enum_hash for s in trajectory()
    }
    return len(hashes) == 1


def gate_violation_count() -> int:
    return sum(
        1 for s in trajectory() if s.gate_bypass
    )


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


_POLLUTED_VERDICTS: frozenset[str] = frozenset({
    "ai_sludge", "adversarial_set",
    "sludge",
    "selective_reporting",
    "hidden_null_result",
    "confidence_inflation",
    "benchmark_cherry_pick",
    "causal_exaggeration",
    "methodological_laundering",
})


def epistemic_pollution() -> float:
    """Growth in polluted-verdict share between
    the early and late windows of the long-
    horizon trajectory. Clipped at 0.

    Raw fixture composition (45% adversarial in
    v13.2) is NOT what this metric is for; the
    point is whether pollution GROWS over the
    horizon. A stable fixture with constant
    pollution share returns 0.0 here."""
    rows = trajectory()
    if not rows:
        return 0.0
    window = 500
    early = rows[:window]
    late = rows[-window:]
    if not early or not late:
        return 0.0
    e = sum(
        1 for r in early
        if r.verdict in _POLLUTED_VERDICTS
    ) / len(early)
    l = sum(
        1 for r in late
        if r.verdict in _POLLUTED_VERDICTS
    ) / len(late)
    return _round(max(0.0, l - e))


def pollution_static_share() -> float:
    """Raw composition share - kept as a
    static info metric so the artifact records
    the fixture's adversarial-load level
    honestly."""
    rows = trajectory()
    if not rows:
        return 0.0
    polluted = sum(
        1 for r in rows
        if r.verdict in _POLLUTED_VERDICTS
    )
    return _round(polluted / len(rows))


__all__ = [
    "closed_enum_hash_constant",
    "epistemic_pollution",
    "gate_violation_count",
    "pollution_static_share",
]
