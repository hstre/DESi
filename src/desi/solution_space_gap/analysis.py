"""DESi's epistemic-gap analysis: turn an EpistemicGapSnapshot into justified, NON-authoritative
BlindSpotProposals. DESi structures the state, analyses coverage/dependencies, and locates
under-worked-but-RELEVANT gaps. It does NOT generate creative content - that is Kevin's job; DESi
only points at where the room is and WHY, with provenance.

What makes this substantive (not a frequency sort over affinity counts):
  * it is driven by the actual OPEN conflicts and their severity, not by how often a move was used;
  * an affinity already TRIED on a conflict (with negative trials) is NOT a blind spot - it is
    "known not to help yet", so it is demoted, and a different untried-relevant move rises (the
    intervention sensitivity the contract demands);
  * a resolved conflict is simply absent from the snapshot, so it disappears from the proposals;
  * every proposal carries the concrete signals that produced it, so each ranking change is
    traceable to a specific input.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .snapshot import EpistemicGapSnapshot

# Which content-free thinking-moves help resolve which KIND of incompatibility, and HOW relevant
# each is (the weight ranks within a kind, so the most fitting untried move wins - not just any rare
# one). A small, explicit, override-able taxonomy. NOT the substance: the substance is the
# trial/attempt awareness below; relevance only guards against the "rare ⇒ seeded" Goodhart trap.
_RELEVANT_BY_KIND: dict[str, tuple[tuple[str, float], ...]] = {
    "causal_dispute": (("causal", 1.0), ("boundary", 0.7), ("decomposition", 0.6),
                       ("invariant", 0.5)),
    "contradiction": (("causal", 0.9), ("adversarial", 0.8), ("provenance", 0.7), ("boundary", 0.6)),
    "value_mismatch": (("boundary", 1.0), ("invariant", 0.8), ("provenance", 0.6)),
    "numeric": (("boundary", 1.0), ("invariant", 0.9)),
    "stale_hypothesis": (("adversarial", 1.0), ("risk", 0.8), ("inversion", 0.7)),
    "unqualified": (("causal", 0.8), ("adversarial", 0.7), ("provenance", 0.6), ("boundary", 0.5)),
}
_BASE_RELEVANT: tuple[tuple[str, float], ...] = (("causal", 0.8), ("adversarial", 0.7),
                                                 ("provenance", 0.6), ("boundary", 0.5))
_SEVERITY_W = {"hard": 1.0, "soft": 0.6}


@dataclass(frozen=True)
class BlindSpotProposal:
    """A justified, NON-authoritative pointer at where creativity is owed. Kevin turns it into
    hypotheses/methods; it is never a decision and never written back to Layer 9."""

    target: str                       # e.g. "conflict:X17"
    missing_affinity: str             # the under-addressed, relevant thinking-move
    reason: tuple[str, ...]           # the concrete signals that produced this (traceable)
    expected_information_gain: str    # "low" | "medium" | "high"
    priority: float
    provenance: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "target": self.target, "missing_affinity": self.missing_affinity,
            "reason": list(self.reason), "expected_information_gain": self.expected_information_gain,
            "priority": self.priority, "provenance": dict(self.provenance),
        }


def _relevant_affinities(kind: str) -> tuple[tuple[str, float], ...]:
    return _RELEVANT_BY_KIND.get(kind, _BASE_RELEVANT)


def _under_addressed(snapshot: EpistemicGapSnapshot, conflict_id: str, affinity: str,
                     attempted: tuple[str, ...]) -> tuple[float, str]:
    """How much of a blind spot ``affinity`` still is FOR THIS conflict (scope-bound). The demotion
    is bound to (conflict, scope, method_variant, result) - a local failure never demotes the move
    globally, and ``technical_failure`` (no methodological signal) does NOT demote at all.

    Returns ``(under, why)``; ``under == 0`` means "not a gap here" (already worked)."""
    here = [t for t in snapshot.method_trials
            if t.affinity == affinity and t.target_conflict == conflict_id]
    if any(t.result == "success" for t in here):
        return 0.0, "already worked on this conflict"
    real_neg = sum(t.count for t in here if t.result in ("no_benefit", "harmful"))
    tech = sum(t.count for t in here if t.result == "technical_failure")
    inc = sum(t.count for t in here if t.result in ("inconclusive", "unknown"))
    # success in ANOTHER scope is a promising-transfer signal: it raises the gap, not lowers it.
    elsewhere = any(t.affinity == affinity and t.target_conflict != conflict_id
                    and t.result == "success" for t in snapshot.method_trials)
    if real_neg:
        return 0.15, f"{affinity} tried {real_neg}x with no benefit/harm here (ineffective in scope)"
    if tech and not inc:
        # tried, but ONLY technical failures - that is not evidence the move is wrong; keep it open.
        return (0.9, f"{affinity} attempted here but only {tech} technical failure(s) "
                "(not methodological - worth a clean retry)")
    if inc:
        return 0.5, f"{affinity} only inconclusively tried here ({inc}x)"
    if elsewhere:
        return 1.0, f"{affinity} never tried on this conflict but SUCCEEDED in another scope"
    if affinity in attempted:
        return 0.5, f"{affinity} marked attempted on this conflict but no outcome recorded (unknown)"
    return 1.0, f"{affinity} never tried on this conflict"


def _info_gain(priority: float) -> str:
    return "high" if priority >= 0.66 else ("medium" if priority >= 0.33 else "low")


def analyze_gaps(snapshot: EpistemicGapSnapshot) -> list[BlindSpotProposal]:
    """Locate under-addressed-but-relevant thinking-moves on the OPEN conflicts. Deterministic and
    fully traceable. Resolved conflicts are absent from the snapshot, so they yield nothing."""
    prov = {"snapshot_hash": snapshot.provenance.snapshot_hash,
            "layer9_sequence": snapshot.provenance.layer9_sequence}
    proposals: list[BlindSpotProposal] = []
    for c in snapshot.conflicts:
        sev = _SEVERITY_W.get(c.severity, 0.6)
        for aff, relevance in _relevant_affinities(c.kind):
            under, why = _under_addressed(snapshot, c.id, aff, c.attempted_affinities)
            if under <= 0:
                continue                                  # the move already worked here - not a gap
            priority = round(sev * relevance * under, 6)
            if priority <= 0:
                continue
            reason = (
                f"{c.severity}-severity unresolved conflict {c.id} (open since {c.unresolved_since})",
                why,
                f"relevant move for a '{c.kind}' incompatibility",
            )
            proposals.append(BlindSpotProposal(
                target=f"conflict:{c.id}", missing_affinity=aff, reason=reason,
                expected_information_gain=_info_gain(priority), priority=priority, provenance=prov))
    proposals.sort(key=lambda p: (-p.priority, p.target, p.missing_affinity))
    return proposals


def frequency_baseline(snapshot: EpistemicGapSnapshot, *, top_k: int = 4) -> list[str]:
    """Baseline 1 - a pure affinity-FREQUENCY heuristic: the least-used moves across the repertoire,
    ignoring conflicts, severity, trial OUTCOMES and relevance."""
    from collections import Counter
    counts: Counter = Counter()
    for m in snapshot.method_history:
        for a in m.affinities:
            counts[a] += 1
    universe = sorted({a for m in snapshot.method_history for a in m.affinities}
                      | {a for a, _ in _BASE_RELEVANT})
    return sorted(universe, key=lambda a: (counts.get(a, 0), a))[:top_k]


def static_kind_baseline(snapshot: EpistemicGapSnapshot) -> list[str]:
    """Baseline 2 - a STATIC conflict-kind -> affinity lookup: per open conflict, the most-relevant
    affinity not in ``attempted_affinities`` (BINARY tried/untried). It ignores trial RESULT KIND,
    scope and success-elsewhere - so the real DESi analysis must beat IT, not just frequency, to earn
    its keep (e.g. a move tried with only TECHNICAL failures should stay open, which this discards)."""
    out: list[str] = []
    for c in snapshot.conflicts:
        for aff, _ in _relevant_affinities(c.kind):
            if aff not in c.attempted_affinities:
                out.append(aff)
                break
    return out
