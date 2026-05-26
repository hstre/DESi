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
# genuine missing-evidence markers (admissible NEI gap)
_MISSING = ("does not state", "does not say", "no evidence that", "not mentioned",
            "not specified", "no information about", "not given", "missing",
            "absent", "does not mention", "not provided", "no data on",
            "says nothing about", "does not establish")
# precision/approximation quibbles -- NOT a missing-evidence gap on their own
_PRECISION = ("approximate", "around", "about ", "roughly", "exact figure",
              "exact number", "not exact", "estimate", "rough", "precise",
              "specific number", "exact count", "approximatel")
# claim comparison cues -> numeric direction
_COMP = {"more than": "gt", "greater than": "gt", "over ": "gt", "exceeds": "gt",
         "at least": "gt", "fewer than": "lt", "less than": "lt", "under ": "lt",
         "at most": "lt", "below ": "lt", "no more than": "lt"}


def _ord(w) -> int:
    w = (w or "NONE").upper()
    return WEIGHTS.index(w) if w in WEIGHTS else 0


def _cap(desi: str, auditor: str) -> str:
    """DESi may DOWNGRADE but never ESCALATE above the auditor's self-claim."""
    return WEIGHTS[min(_ord(desi), _ord(auditor))]


def _numbers(text: str) -> list[int]:
    out = []
    for m in re.findall(r"\d[\d,]*", text or ""):
        try:
            out.append(int(m.replace(",", "")))
        except ValueError:
            pass
    return out


def numeric_contradiction(claim: str, evidence: str) -> bool:
    """True iff the claim asserts a numeric bound that an evidence number of the
    SAME magnitude contradicts (e.g. claim 'more than 79,500' vs evidence 'around
    79,000'). Magnitude-bounded so unrelated numbers (deaths, cases) don't fire."""
    cl = (claim or "").lower()
    ev_nums = _numbers(evidence)
    if not ev_nums:
        return False
    for phrase, op in _COMP.items():
        i = cl.find(phrase)
        if i == -1:
            continue
        m = re.search(r"\d[\d,]*", cl[i + len(phrase):])
        if not m:
            continue
        n = int(m.group(0).replace(",", ""))
        for e in ev_nums:
            if op == "gt" and 0.5 * n <= e < n:      # claim '>n', same-magnitude e below n
                return True
            if op == "lt" and n < e <= 2.0 * n:      # claim '<n', same-magnitude e above n
                return True
    return False


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
    can_defeat_first: bool = False   # may this dissent legitimately overturn the first verdict?
    contradiction_present: bool = False  # evidence already contradicts the claim
    names_missing_evidence: bool = False
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


def filter_dissent(raw_text: str, *, claim: str, evidence: str,
                   auditor_strength: str = "STRONG") -> GovernedDissent:
    """The DESi governance gate. The wild brother's dissent text is UNTRUSTED.
    DESi assigns the weight from the filtered signal but NEVER escalates above the
    auditor's own self-claim (``auditor_strength`` is an upper cap: WEAK stays
    WEAK). A dissent may only DEFEAT the first verdict when it is a concrete,
    claim-relevant, MISSING-evidence gap of weight >= MEDIUM AND the evidence does
    not already contradict the claim. Never forces NEI; never propagates a verdict."""
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

    # missing-evidence vs precision-quibble vs already-contradictory (Rules 2 & 3)
    names_missing = any(m in low_clean for m in _MISSING)
    precision_only = any(p in low_clean for p in _PRECISION) and not names_missing
    contradiction_present = numeric_contradiction(claim, evidence)

    admitted = claim_relevant and concrete and not generic_only and len(clean.split()) >= 4
    reasons: list[str] = []
    pruned = None
    if not admitted:
        pruned = ("not claim-relevant" if not claim_relevant else
                  "generic skepticism only" if generic_only else
                  "not concrete" if not concrete else "insufficient dissent content")
    else:
        if names_missing:
            reasons.append("names a concrete missing-evidence gap")
        if precision_only:
            reasons.append("precision/approximation quibble (not a missing-evidence gap)")
        reasons.append(f"claim-relevant (overlap={overlap})")

    # DESi-assessed weight from the signal, then CAPPED at the auditor self-claim
    # (Rule 1: never auto-escalate WEAK -> MEDIUM).
    desi = "NONE"
    if admitted:
        if names_missing and overlap >= 4:
            desi = "STRONG"
        elif names_missing or overlap >= 3:
            desi = "MEDIUM"
        else:
            desi = "WEAK"
    weight = _cap(desi, auditor_strength) if admitted else "NONE"

    # A dissent may DEFEAT the first verdict only as a real missing-evidence gap,
    # weight >= MEDIUM, and NOT when the evidence already contradicts the claim
    # (missing evidence -> NEI possible; contradictory evidence -> REFUTES stands).
    can_defeat = (admitted and _ord(weight) >= _ord("MEDIUM")
                  and names_missing and not precision_only
                  and not contradiction_present)

    return GovernedDissent(
        admitted=admitted, weight=weight, reasons=tuple(reasons),
        pruned_reason=pruned, authority_violation=authority,
        audit_signal=(clean[:600] if admitted else ""),
        can_defeat_first=can_defeat, contradiction_present=contradiction_present,
        names_missing_evidence=names_missing, governed=True,
    )


def resolve_final(first, recheck_verdict, governed: GovernedDissent):
    """DESi governance over the recheck output: a dissent that may NOT defeat the
    first verdict cannot overturn it. If the recheck flipped a first verdict that
    the (non-defeating) dissent had no authority to defeat, REVERT to the first
    verdict. Wild brother may disturb, not rule. Returns (final, reverted)."""
    if (first is not None and recheck_verdict != first
            and not governed.can_defeat_first):
        return first, True
    return recheck_verdict, False


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
    uncertainty_preserved = uncertainty_over_amplified = overweight_prevented = 0
    for it in items:
        info = audit_info.get(it["id"])
        if not info:
            continue
        gd = info.get("governed")
        first, final = info.get("first"), info.get("final")
        if info.get("reverted_overweight"):
            overweight_prevented += 1   # DESi reverted a non-defeating dissent flip
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
        "dissent_overweight_prevented": overweight_prevented,
        "authority_violation_attempts": authority_attempts,
        "DISSENT_IS_NEVER_AUTHORITY": DISSENT_IS_NEVER_AUTHORITY,
    }


__all__ = [
    "DISSENT_IS_NEVER_AUTHORITY", "DissentAuthorityViolation", "GOVERNED_SENTINEL",
    "GovernedDissent", "WEIGHTS", "filter_dissent", "governance_log",
    "numeric_contradiction", "require_governed", "resolve_final",
]
