"""DESi dissent governance gate (PERIPHERAL).

Architectural invariant:

    DISSENT_IS_NEVER_AUTHORITY = True

The wild-brother / dissent layer (challenger, auditor) produces UNTRUSTED raw
dissent signals. They must pass through this DESi governance filter before any
solver or recheck may see them. The filter:

  * checks claim-relevance, evidence-basis, concreteness,
  * prunes pure generic skepticism,
  * NEVER converts dissent into a verdict and NEVER forces NOT_ENOUGH_INFO,
  * strips any verdict the dissent tries to assert (authority-takeover attempt),
  * assigns the dissent WEIGHT itself (DESi-assigned, not the wild brother's
    self-claimed strength).

Only a ``GovernedDissent`` produced here may enter a recheck, and the solver
boundary refuses any dissent payload that is not stamped by this gate (see
``require_governed`` / ``GOVERNED_SENTINEL``). The wild brother stays an
epistemic disruptor; DESi stays governance. This is periphery: it touches no
DESi-core structure and invents no ontology.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

DISSENT_IS_NEVER_AUTHORITY = True
GOVERNED_SENTINEL = "[DESI-GOVERNED]"           # stamp only this gate may apply
WEIGHTS = ("NONE", "WEAK", "MEDIUM", "STRONG")

# generic, content-free skepticism (pruned -- not admissible dissent on its own)
_GENERIC = (
    "might be wrong", "could be wrong", "not sure", "hard to say", "uncertain",
    "who knows", "in general", "generally skeptical", "cannot be certain",
    "can't be certain", "more research", "needs more study", "it depends",
)
# concrete evidence-gap markers (admissible only with claim relevance)
_CONCRETE = (
    "does not state", "does not say", "no evidence that", "missing", "not mentioned",
    "not specified", "no information about", "fails to", "absent", "upper bound",
    "lower bound", "only states", "only says", "does not establish", "not given",
)
# verdict directives a dissent must NOT assert (authority-takeover attempt)
_VERDICT = ("final:", "final verdict", "the verdict is", "i conclude", "answer:",
            "the answer is", "verdict:", "label:")
_VERDICT_LABELS = ("supports", "refutes", "not_enough_info", "not enough info")
_STOP = {"the", "a", "an", "of", "to", "in", "on", "is", "are", "and", "or", "that",
         "this", "it", "for", "with", "as", "be", "not", "no", "does", "do", "than",
         "which", "but", "by", "from", "we", "you", "they", "there"}


@dataclass(frozen=True)
class GovernedDissent:
    """Output of the DESi gate. Carries a DESi-ASSIGNED weight and a verdict-free
    audit signal. Never a decision. Only this gate constructs it with
    ``governed=True``; the solver boundary requires that stamp."""
    admitted: bool
    weight: str                 # DESi-assigned (NONE..STRONG); never a verdict
    reasons: tuple = ()
    pruned_reason: str | None = None
    authority_violation: bool = False
    audit_signal: str = ""      # verdict-free dissent text (empty if not admitted)
    governed: bool = True

    def recheck_payload(self) -> str:
        """The ONLY string allowed into a recheck. Stamped + verdict-free."""
        body = self.audit_signal if self.admitted else "no admissible evidence gap"
        return f"{GOVERNED_SENTINEL} weight={self.weight}; {body}"


def _content_tokens(text: str) -> set:
    toks = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {t for t in toks if t not in _STOP and len(t) >= 3}


def _strip_verdict(text: str) -> str:
    """Remove any verdict directive / label the dissent asserts (authority strip)."""
    out = text
    low = out.lower()
    for marker in _VERDICT:
        i = low.find(marker)
        if i != -1:
            out = out[:i]            # drop everything from the verdict directive on
            low = out.lower()
    # also blank standalone verdict labels
    for lab in _VERDICT_LABELS:
        out = re.sub(lab, "[redacted-verdict]", out, flags=re.IGNORECASE)
    return out.strip()


def filter_dissent(raw_text: str, *, claim: str, evidence: str) -> GovernedDissent:
    """The DESi governance gate. Takes the wild brother's UNTRUSTED raw dissent
    text (its self-claimed strength/flag is deliberately ignored) and returns a
    GovernedDissent. Never forces NEI; never propagates a verdict."""
    raw = raw_text or ""
    low = raw.lower()
    authority = any(m in low for m in _VERDICT) or any(l in low for l in _VERDICT_LABELS)
    clean = _strip_verdict(raw)
    low_clean = clean.lower()

    claim_ev = _content_tokens(claim) | _content_tokens(evidence)
    d_toks = _content_tokens(clean)
    overlap = len(d_toks & claim_ev)
    claim_relevant = overlap >= 2
    concrete = any(m in low_clean for m in _CONCRETE) or bool(re.search(r"\d", clean))
    generic_only = (any(g in low_clean for g in _GENERIC) and not concrete) or (overlap < 2 and not concrete)

    admitted = claim_relevant and concrete and not generic_only and len(clean.split()) >= 4
    reasons: list[str] = []
    pruned = None
    if not admitted:
        if not claim_relevant:
            pruned = "not claim-relevant"
        elif not concrete:
            pruned = "not concrete / generic skepticism"
        elif generic_only:
            pruned = "generic skepticism only"
        else:
            pruned = "insufficient dissent content"
    else:
        if concrete:
            reasons.append("names a concrete evidence gap")
        if claim_relevant:
            reasons.append(f"claim-relevant (overlap={overlap})")

    # DESi-assigned weight from the FILTERED signal (NOT the wild brother's claim)
    weight = "NONE"
    if admitted:
        names_missing = any(m in low_clean for m in _CONCRETE)
        if names_missing and overlap >= 4:
            weight = "STRONG"
        elif names_missing or overlap >= 3:
            weight = "MEDIUM"
        else:
            weight = "WEAK"

    return GovernedDissent(
        admitted=admitted, weight=weight, reasons=tuple(reasons),
        pruned_reason=pruned, authority_violation=authority,
        audit_signal=(clean[:600] if admitted else ""), governed=True,
    )


class DissentAuthorityViolation(RuntimeError):
    """Raised when raw / ungoverned dissent reaches a solver boundary.
    DISSENT_IS_NEVER_AUTHORITY."""


def require_governed(payload: str) -> str:
    """Solver-boundary guard. A recheck/dissent payload MUST be stamped by the
    DESi gate. Raw or unfiltered dissent raises -- enforcing the invariant.
    Returns the verdict-free body (sentinel stripped) for prompt building."""
    if not isinstance(payload, str) or not payload.startswith(GOVERNED_SENTINEL):
        raise DissentAuthorityViolation(
            "ungoverned dissent reached the solver: DISSENT_IS_NEVER_AUTHORITY "
            "(route wild-brother output through dissent_governance.filter_dissent)."
        )
    return payload[len(GOVERNED_SENTINEL):].strip()


def governance_log(items, audit_info, parsed, *, nei="NOT_ENOUGH_INFO"):
    """DESi protocol over a governed audit run. items carry {id, gold};
    audit_info[id] carries {first, final, governed: GovernedDissent}."""
    accepted = rejected = pruned_generic = authority_attempts = 0
    uncertainty_preserved = uncertainty_over_amplified = 0
    for it in items:
        info = audit_info.get(it["id"])
        if not info:
            continue
        gd = info.get("governed")
        first, final = info.get("first"), info.get("final")
        if gd is not None:
            if gd.authority_violation:
                authority_attempts += 1
            if not gd.admitted:
                pruned_generic += 1
            elif final == nei and first != nei:
                accepted += 1
            elif gd.admitted and final == first:
                rejected += 1
            # uncertainty bookkeeping (admitted dissent only)
            if gd.admitted and final == nei:
                if it["gold"] == nei:
                    uncertainty_preserved += 1
                else:
                    uncertainty_over_amplified += 1
    return {
        "accepted_dissent": accepted,
        "rejected_dissent": rejected,
        "pruned_generic_dissent": pruned_generic,
        "uncertainty_preserved": uncertainty_preserved,
        "uncertainty_over_amplified": uncertainty_over_amplified,
        "authority_violation_attempts": authority_attempts,
        "DISSENT_IS_NEVER_AUTHORITY": DISSENT_IS_NEVER_AUTHORITY,
    }


__all__ = [
    "DISSENT_IS_NEVER_AUTHORITY", "DissentAuthorityViolation", "GOVERNED_SENTINEL",
    "GovernedDissent", "WEIGHTS", "filter_dissent", "governance_log",
    "require_governed",
]
