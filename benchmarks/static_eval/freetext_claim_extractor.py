#!/usr/bin/env python3
"""Rule-based free-text claim decomposition (P2 prototype).

Turns one free-text answer into several *atomic* sub-claims. This is a
deliberately small, honest, **heuristic** prototype — NOT a semantic parser.
It uses only:

- sentence splitting (on . ! ?),
- clause splitting on a few connectives (and / because / but / while),
- subject propagation (a verb-initial clause inherits the previous subject),
- a year heuristic (``... born in <Place> in <Year>`` -> a separate
  "<subject> birth year = <Year>" claim, with the year removed from the prose).

It will mis-split many real sentences (see the report for failure modes). The
existing ``src/desi/self_audit/extractor.py`` is intentionally closed-kind
(HASH/NUMERIC/COUNT/PHASE) and markdown-specific, so it is **not** reused here;
this prototype is the free-text counterpart.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")
_CONN_SPLIT = re.compile(r"\s+(and|because|but|while)\s+", re.IGNORECASE)
_YEAR = re.compile(r"\b(1[5-9]\d{2}|20\d{2})\b")
_LEADING_SUBJECT = re.compile(
    r"^((?:[A-Z][\w.'\-]*)(?:\s+(?:[A-Z][\w.'\-]*|of|the|de|van|von|der))*)")
_VERB_START = re.compile(
    r"^(was|were|is|are|been|being|became|become|had|has|have|did|does|died|"
    r"wrote|won|lived|worked|founded|created|made|served|ruled|invented|"
    r"discovered|painted|composed|led|joined|married)\b", re.IGNORECASE)
CONNECTIVES = ("and", "because", "but", "while")


@dataclass
class SubClaim:
    text: str
    kind: str          # "clause" | "year"
    subject: str
    connective: str    # "" | "and" | "because" | "but" | "while"


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text.strip()) if s.strip()]


def _split_clauses(sentence: str) -> list[tuple[str, str]]:
    parts = _CONN_SPLIT.split(sentence)
    clauses: list[tuple[str, str]] = [(parts[0].strip(), "")]
    for i in range(1, len(parts), 2):
        conn = parts[i].lower()
        clause = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if clause:
            clauses.append((clause, conn))
    return clauses


def _leading_subject(clause: str) -> str | None:
    m = _LEADING_SUBJECT.match(clause)
    return m.group(1).strip() if m else None


def _with_subject(clause: str, subject: str | None) -> str:
    if subject and _VERB_START.match(clause):
        return f"{subject} {clause}"
    return clause


def _remove_year(clause: str, year: str) -> str:
    out = re.sub(rf"\s*\b(?:in|on|around|by|circa|c\.)\s+{year}\b", "", clause,
                 flags=re.IGNORECASE)
    if out == clause:  # no preposition — strip the bare year
        out = re.sub(rf"\s*\b{year}\b", "", clause)
    return re.sub(r"\s{2,}", " ", out).strip(" ,;")


def extract_subclaims(answer: str) -> list[SubClaim]:
    """Decompose a free-text answer into atomic sub-claims (heuristic)."""
    out: list[SubClaim] = []
    for sentence in _split_sentences(answer):
        subject: str | None = None
        for clause, conn in _split_clauses(sentence):
            subj = _leading_subject(clause)
            if subj:
                subject = subj

            year_claim: SubClaim | None = None
            m = _YEAR.search(clause)
            if m and subject:
                year = m.group(1)
                key = "birth year" if re.search(r"\bborn\b", clause, re.IGNORECASE) else "year"
                year_claim = SubClaim(text=f"{subject} {key} = {year}", kind="year",
                                      subject=subject, connective=conn)
                clause = _remove_year(clause, year)

            prose = _with_subject(clause.strip(), subject).strip(" .,;")
            if len(prose.split()) >= 2:
                out.append(SubClaim(text=prose, kind="clause",
                                    subject=subject or "", connective=conn))
            if year_claim is not None:
                out.append(year_claim)
    return out


__all__ = ["SubClaim", "CONNECTIVES", "extract_subclaims"]


if __name__ == "__main__":
    import json
    demos = [
        "Virginia Woolf was born in London in 1882 and became a famous writer.",
        "The Great Wall is in China but it cannot be seen from space.",
        "Water boils at 100 degrees because of atmospheric pressure.",
        "Sharks are fish while dolphins are mammals.",
    ]
    for d in demos:
        print(d)
        for sc in extract_subclaims(d):
            print(f"   - [{sc.kind}/{sc.connective or '-'}] {sc.text}")
        print()
