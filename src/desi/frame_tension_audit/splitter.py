"""Aufgaben 2 + 4 — split TENSION targets into TRUE / FALSE / AMBIGUOUS.

Deterministic, content-based classifier. Each TENSION case is
inspected for three families of evidence:

* **hard inner markers** — unambiguous frame-specific vocabulary
  (e.g. "isolated system" is hard-thermodynamic, "Shannon entropy"
  is hard-information-theoretic). When present, the inner verdict
  is grounded in the text itself and the outer marker is in fact
  contradictory — TRUE_TENSION.
* **metaphor subjects** — poet / lover / smile / market / justice /
  hope. These indicate the sentence is using frame-borrowed
  vocabulary metaphorically, so a TENSION verdict against an
  outer information- or thermo-frame is too strict — AMBIGUOUS.
* **no clear evidence either way** — FALSE_TENSION; the inner
  verdict came from a single weak token and the outer pair is
  conflict-capable but the case itself is benign.

Each FALSE / AMBIGUOUS case is also tagged with exactly one
``TensionFailureCause`` (Aufgabe 4). TRUE cases carry ``None``.
"""
from __future__ import annotations

from dataclasses import dataclass

from .enums import TensionAuditClass, TensionFailureCause
from .extractor import TensionTarget


# Hard, frame-specific markers per inner frame. If a sentence
# contains one of these, the inner verdict is grounded — any
# TENSION against another outer is a real signal.
_HARD_INNER: dict[str, tuple[str, ...]] = {
    "thermodynamic": (
        "isolated system", "closed physical system", "joules per second",
        "kelvin", "hot to cold", "second law", "heat flow",
    ),
    "information_theoretic": (
        "shannon entropy", "fair coin", "fair die", "channel capacity",
        "mutual information", "one bit", "in bits", "in nats",
        "message distribution", "biased coin", "loaded coin",
        "bounds compression",
    ),
    "formal_logic": (
        "modus ponens", "axiom", "lemma", "theorem",
        "universal instantiation", "therefore the next",
    ),
    "authority_speech": (
        "minister stated", "according to the report",
        "report states", "the minister stated", "according to,",
    ),
    "empirical_causal": (
        "drought resulted", "crop failure", "experiment shows",
        "observed cause", "cause-effect chain",
    ),
    "tool_computable": (
        "calculate the area", "compute the shannon",
        "please compute",
    ),
    "ontological_distinguishability": (
        "morning star", "evening star", "hesperus", "phosphorus",
        "identity statement",
    ),
    "metaphorical": (
        "poet's smile", "delicate flame", "feathers", "small flame",
        "small bird",
    ),
}


# Subjects that license metaphorical borrowing of another frame's
# vocabulary. When any of these appears, an outer/inner mismatch
# is more likely AMBIGUOUS than TRUE.
_METAPHOR_SUBJECTS: tuple[str, ...] = (
    "poet", "lover", "smile", "delicate", "feathers",
    "the market", "justice", "hope", "the brain",
)


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    low = text.lower()
    return any(n in low for n in needles)


def _has_hard_inner(text: str, inner: str | None) -> bool:
    if inner is None:
        return False
    markers = _HARD_INNER.get(inner, ())
    return _has_any(text, markers)


def _has_metaphor_subject(text: str) -> bool:
    return _has_any(text, _METAPHOR_SUBJECTS)


_POLYSEMY_FRAME_PAIRS: frozenset[frozenset[str]] = frozenset({
    frozenset({"thermodynamic", "information_theoretic"}),
    frozenset({"metaphorical", "information_theoretic"}),
    frozenset({"metaphorical", "thermodynamic"}),
})


_BRIDGE_FRAME_PAIRS: frozenset[frozenset[str]] = frozenset({
    frozenset({"information_theoretic", "tool_computable"}),
    frozenset({"authority_speech", "empirical_causal"}),
})


def _pair(a: str | None, b: str | None) -> frozenset[str] | None:
    if a is None or b is None:
        return None
    return frozenset({a, b})


def _classify(
    target: TensionTarget,
) -> tuple[TensionAuditClass, TensionFailureCause | None]:
    inner = target.inner_frame
    outer = target.outer_frame
    pair = _pair(inner, outer)

    if inner is None or outer is None:
        # Should not normally happen in a TENSION case — both sides
        # must be present for score=0.5 — but guard anyway.
        return (
            TensionAuditClass.AMBIGUOUS_TENSION,
            TensionFailureCause.INNER_UNDERDETECTION,
        )

    has_hard = _has_hard_inner(target.text, inner)
    has_metaphor = _has_metaphor_subject(target.text)

    # Hard inner marker present → the inner verdict is grounded;
    # the outer/inner conflict is a real signal.
    if has_hard and not has_metaphor:
        return (TensionAuditClass.TRUE_TENSION, None)

    # Metaphor subject + polysemy pair → semantic borrowing is
    # plausible; the TENSION is over-strict.
    if has_metaphor and pair in _POLYSEMY_FRAME_PAIRS:
        return (
            TensionAuditClass.AMBIGUOUS_TENSION,
            TensionFailureCause.POLYSEMY_COLLISION,
        )

    # Bridge-frame pair (e.g. info ↔ tool, authority ↔ causal)
    # without a hard inner marker → the system lacks an explicit
    # composite frame.
    if pair in _BRIDGE_FRAME_PAIRS and not has_hard:
        return (
            TensionAuditClass.AMBIGUOUS_TENSION,
            TensionFailureCause.MISSING_BRIDGE_FRAME,
        )

    # Hard marker present but a metaphor subject also showed up
    # (e.g. "the poet's Shannon entropy") → real polysemy ambiguity.
    if has_hard and has_metaphor:
        return (
            TensionAuditClass.AMBIGUOUS_TENSION,
            TensionFailureCause.POLYSEMY_COLLISION,
        )

    # No hard inner marker, no metaphor cue → the inner verdict is
    # likely an over-eager domain-token detection; the pair is
    # treated as conflict-capable but the actual sentence is
    # benign.
    return (
        TensionAuditClass.FALSE_TENSION,
        TensionFailureCause.OUTER_OVERDETECTION,
    )


@dataclass(frozen=True)
class TensionAuditOutcome:
    target: TensionTarget
    audit_class: TensionAuditClass
    failure_cause: TensionFailureCause | None

    def to_dict(self) -> dict[str, object]:
        return {
            "target": self.target.to_dict(),
            "audit_class": self.audit_class.value,
            "failure_cause": (
                self.failure_cause.value if self.failure_cause else None
            ),
        }


def split_tension_targets(
    targets: tuple[TensionTarget, ...],
) -> tuple[TensionAuditOutcome, ...]:
    out: list[TensionAuditOutcome] = []
    for t in targets:
        cls, cause = _classify(t)
        out.append(TensionAuditOutcome(
            target=t, audit_class=cls, failure_cause=cause,
        ))
    return tuple(out)


__all__ = ["TensionAuditOutcome", "split_tension_targets"]
