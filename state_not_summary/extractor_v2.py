"""State extractor v2 — emits structured epistemic entries, never prose.

This is intentionally narrow: it scans the chat for *explicit structural markers* of state
(decisions, constraints, discarded paths, claims, conflicts, questions, evidence labels) and
emits IDs + short canonical bodies. Anything that does NOT match a structural pattern is
ignored. The brief allows this — the extractor must NOT summarize the chat.

If the chat lacks structural markers, the extractor returns a near-empty state. That is
the honest outcome, not a bug: an unstructured chat has little epistemic state to extract.
"""
from __future__ import annotations

import re

from state_v2 import (CLAIM_STATUS, Claim, Conflict, Constraint, DOMAINS, DesiStateV2,
                      Decision, DiscardedPath, EVIDENCE, MAX_BODY_WORDS, OpenQuestion)

# Structural patterns: '[CLAIM C1 evidence=likely] body…', '[DECISION D2 since=t3 replaces=D1] body',
# '[CONSTRAINT R1 scope=core] body', '[DISCARD X1 reason=…] body', '[CONFLICT K1 claims=C1,C2 status=open]',
# '[QUESTION Q1 blocking] body', '[EVIDENCE domain=tokenization status=likely]'.
# These are explicit markers an author uses while writing — the extractor never invents them.

_PAT_CLAIM = re.compile(r"\[CLAIM\s+(?P<id>[A-Z0-9_-]+)(?:\s+status=(?P<status>[a-z]+))?"
                        r"(?:\s+evidence=(?P<evidence>[a-z]+))?\]\s*(?P<body>[^\[\n]*)")
_PAT_DECISION = re.compile(r"\[DECISION\s+(?P<id>[A-Z0-9_-]+)(?:\s+since=(?P<since>[^\s\]]+))?"
                           r"(?:\s+replaces=(?P<replaces>[A-Z0-9_-]+))?\]\s*(?P<body>[^\[\n]*)")
_PAT_CONSTRAINT = re.compile(r"\[CONSTRAINT\s+(?P<id>[A-Z0-9_-]+)(?:\s+scope=(?P<scope>[a-z_]+))?\]"
                             r"\s*(?P<body>[^\[\n]*)")
_PAT_DISCARD = re.compile(r"\[DISCARD\s+(?P<id>[A-Z0-9_-]+)\]\s*(?P<body>[^\|\[\n]*?)"
                          r"(?:\s*\|\s*reason:\s*(?P<reason>[^\[\n]*))?")
_PAT_CONFLICT = re.compile(r"\[CONFLICT\s+(?P<id>[A-Z0-9_-]+)\s+claims=(?P<claims>[A-Z0-9,_-]+)"
                           r"(?:\s+status=(?P<status>[a-z]+))?\]")
_PAT_QUESTION = re.compile(r"\[QUESTION\s+(?P<id>[A-Z0-9_-]+)(?P<block>\s+blocking)?\]\s*(?P<body>[^\[\n]*)")
_PAT_EVIDENCE = re.compile(r"\[EVIDENCE\s+domain=(?P<domain>[a-z_]+)\s+status=(?P<status>[a-z]+)\]")


def _canon(body: str) -> str:
    """Strip the body to a short canonical form (NOT a summary — just whitespace + word cap)."""
    body = re.sub(r"\s+", " ", body or "").strip().rstrip(".,;:")
    words = body.split()
    if len(words) > MAX_BODY_WORDS:
        body = " ".join(words[:MAX_BODY_WORDS])
    return body


def _short_reason(reason: str) -> str:
    """Single short sentence; trim hard if author wrote more."""
    reason = re.sub(r"\s+", " ", reason or "").strip().rstrip(".")
    # take only up to the first sentence terminator
    cut = re.split(r"[.!?]\s", reason, maxsplit=1)[0]
    words = cut.split()
    if len(words) > 14:
        cut = " ".join(words[:14])
    return cut


def extract_state(chat_history) -> DesiStateV2:
    if not isinstance(chat_history, list):
        raise TypeError("chat_history must be a list of {'role','content'} dicts")
    text = "\n".join((m.get("content") or "") for m in chat_history if isinstance(m, dict))

    claims_by_id: dict = {}
    decisions_by_id: dict = {}
    constraints_by_id: dict = {}
    discards_by_id: dict = {}
    conflicts_by_id: dict = {}
    questions_by_id: dict = {}
    evidence_by_domain: dict = {}

    for m in _PAT_CLAIM.finditer(text):
        cid = m.group("id")
        status = m.group("status") or "active"
        evidence = m.group("evidence") or "untested"
        if status not in CLAIM_STATUS:
            status = "active"
        if evidence not in EVIDENCE:
            evidence = "untested"
        claims_by_id[cid] = Claim(id=cid, body=_canon(m.group("body")),
                                  status=status, evidence=evidence)

    for m in _PAT_DECISION.finditer(text):
        did = m.group("id")
        decisions_by_id[did] = Decision(id=did, body=_canon(m.group("body")),
                                        active_since=m.group("since") or "",
                                        replaces=m.group("replaces") or "")

    for m in _PAT_CONSTRAINT.finditer(text):
        rid = m.group("id")
        constraints_by_id[rid] = Constraint(id=rid, body=_canon(m.group("body")),
                                            scope=m.group("scope") or "global")

    for m in _PAT_DISCARD.finditer(text):
        did = m.group("id")
        discards_by_id[did] = DiscardedPath(id=did, body=_canon(m.group("body")),
                                            reason=_short_reason(m.group("reason") or ""))

    for m in _PAT_CONFLICT.finditer(text):
        kid = m.group("id")
        claim_ids = tuple(x for x in m.group("claims").split(",") if x)
        status = m.group("status") or "open"
        conflicts_by_id[kid] = Conflict(id=kid, claim_ids=claim_ids, status=status)

    for m in _PAT_QUESTION.finditer(text):
        qid = m.group("id")
        questions_by_id[qid] = OpenQuestion(id=qid, body=_canon(m.group("body")),
                                            blocking=bool(m.group("block")))

    for m in _PAT_EVIDENCE.finditer(text):
        dom, status = m.group("domain"), m.group("status")
        if dom in DOMAINS and status in EVIDENCE:
            evidence_by_domain[dom] = status

    # Remove decisions that are explicitly REPLACED by later decisions in the same chat.
    replaced = {d.replaces for d in decisions_by_id.values() if d.replaces}
    decisions = [d for did, d in decisions_by_id.items() if did not in replaced]

    # Remove conflicts whose status is resolved.
    open_conflicts = [k for k in conflicts_by_id.values() if k.status != "resolved"]

    state = DesiStateV2(
        active_claims=sorted(claims_by_id.values(), key=lambda c: c.id),
        active_constraints=sorted(constraints_by_id.values(), key=lambda r: r.id),
        open_conflicts=sorted(open_conflicts, key=lambda k: k.id),
        decisions=sorted(decisions, key=lambda d: d.id),
        discarded_paths=sorted(discards_by_id.values(), key=lambda p: p.id),
        open_questions=sorted(questions_by_id.values(), key=lambda q: q.id),
        evidence_status=dict(sorted(evidence_by_domain.items())),
    )
    return state
