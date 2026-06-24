"""Post-answer verifier — deterministic, rule-based checks on a generated answer against the report.

This is the measurable counterpart to the pre-decision heuristics: it runs AFTER the model answers
and is the gate that can keep a bad answer from PROPOSING a persistent-state update. The checks mirror
the ablation's degeneration metrics (invalid-claim reuse, conflict closure without evidence,
unsupported status upgrade, stale-confident answer, coherence-without-continuity) but are
re-implemented here so the router stays independent of the benchmark code.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from desi_router.governance.report import DesiReport

_STOP = frozenset((
    "the a an of to in on and or is are was were be been being that this these those it its as at by "
    "for with from has have had do does did but if then than so such into out up down over under "
    "about their they them we you i which who not no only any all per also more most some can").split())
_REUSE_JAC = 0.5
_TOUCH_JAC = 0.25
_CERTAINTY = re.compile(
    r"\b(confirmed|established|definitely|certainly|resolved|settled|proven|is the|are the|"
    r"clearly|undoubtedly|the answer is|we know)\b", re.I)
_EVIDENCE_CUE = re.compile(
    r"\b(evidence|because|since|measured|shows|data|benchmark|test|per|according to|open|"
    r"unresolved|conflict|trade-?off|vs\.?|versus)\b", re.I)
# A unit that overlaps an invalidated claim but *rejects* it is not reuse — it is the model correctly
# refusing the bad claim. Without this guard the token-overlap check is negation-blind and misreads an
# explicit rejection ("... has been superseded, do not use it") as reuse. Found empirically in the
# Phase-3 live run, where the guarded preprompt makes the model name-and-reject the bad claim.
_REJECT_CUE = re.compile(
    r"\b(not|never|no longer|superseded|invalidated|deprecated|outdated|do not|don'?t|should not|"
    r"shouldn'?t|instead|rather than|avoid|reject(?:ed)?|obsolete|wrong|incorrect)\b", re.I)


def _toks(s: str) -> set:
    return {t for t in re.findall(r"[a-z0-9][a-z0-9\-]+", (s or "").lower())
            if t not in _STOP and len(t) > 2}


def _jac(a: set, b: set) -> float:
    return (len(a & b) / len(a | b)) if (a | b) else 0.0


def _units(text: str) -> list[str]:
    out = []
    for line in (text or "").splitlines():
        line = re.sub(r"^\s*([\*\-•]\s+|\d+[.)]\s+)", "", line).strip()
        for s in re.split(r"(?<=[.!?])\s+", line):
            if len(s.strip()) > 8:
                out.append(s.strip())
    return out


@dataclass
class VerifierResult:
    ok: bool = True
    failed_checks: tuple[str, ...] = ()
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


# checks that are SAFETY-CRITICAL (a failure blocks a persistent-state-update proposal)
_CRITICAL = ("invalid_claim_reuse", "conflict_closure_without_evidence", "unsupported_status_upgrade",
             "stale_confident_answer")


def verify_answer(answer_text: str, report: DesiReport) -> VerifierResult:
    units = _units(answer_text)
    utoks = [_toks(u) for u in units]
    low = (answer_text or "").lower()
    details: dict = {}

    invalid_bodies = list(report.invalidated_claim_texts) + list(report.superseded_claim_texts)
    reused = []
    for b in invalid_bodies:
        bt = _toks(b)
        # reuse only if SOME overlapping unit asserts it — a unit that rejects/negates it does not count
        if any(_jac(bt, ut) >= _REUSE_JAC and not _REJECT_CUE.search(u)
               for u, ut in zip(units, utoks, strict=False)):
            reused.append(b)
    details["invalid_claim_reuse"] = reused

    closed = []
    for ctext in report.open_conflict_texts:
        ct = _toks(ctext)
        matched = [u for u, ut in zip(units, utoks, strict=False) if _jac(ct, ut) >= _TOUCH_JAC]
        if matched and not any(_EVIDENCE_CUE.search(u) for u in matched):
            closed.append(ctext)                       # conflict addressed but no open/evidence cue
    details["conflict_closure_without_evidence"] = closed

    # unsupported status upgrade: certainty markers asserted over invalidated/superseded/conflict topics
    risky_topics = invalid_bodies + list(report.open_conflict_texts)
    upgraded = [t for t in risky_topics
                if any(_CERTAINTY.search(u) and _jac(_toks(t), ut) >= _TOUCH_JAC
                       for u, ut in zip(units, utoks, strict=False))]
    details["unsupported_status_upgrade"] = upgraded

    # stale confident: confident answer while state was missing or superseded
    confident = bool(_CERTAINTY.search(low))
    stale = confident and (not report.has_usable_state or bool(report.superseded_claim_ids))
    details["stale_confident_answer"] = stale

    # coherence without continuity: many fluent units but little overlap with the selected state
    coh = False
    if report.selected_claim_texts and len(units) >= 4:
        sel = [_toks(t) for t in report.selected_claim_texts]
        hit = sum(1 for ut in utoks if max((_jac(st, ut) for st in sel), default=0.0) >= _TOUCH_JAC)
        coh = (hit / len(units)) < 0.25
    details["coherence_without_continuity"] = coh

    failed = []
    if reused:
        failed.append("invalid_claim_reuse")
    if closed:
        failed.append("conflict_closure_without_evidence")
    if upgraded:
        failed.append("unsupported_status_upgrade")
    if stale:
        failed.append("stale_confident_answer")
    if coh:
        failed.append("coherence_without_continuity")
    ok = not any(c in failed for c in _CRITICAL)        # non-critical (coherence) warns, doesn't block
    return VerifierResult(ok=ok, failed_checks=tuple(failed), details=details)
