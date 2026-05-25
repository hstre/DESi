#!/usr/bin/env python3
"""Entity / subject normalisation + light coreference (P7 prototype).

Goal: let semantically-equal subjects match (Lincoln ↔ Abraham Lincoln, USA ↔
United States, NYC ↔ New York City, "it" → the local subject) so conflicts that
P6 missed (string-exact only) can be found.

This is deliberately small and **heuristic** — NOT real NER, NOT an ontology, NOT
global coreference. Aggressive merging is dangerous (homonyms: Paris/France vs
Paris/Texas), so `entities_match` reports HOW it matched (`exact` /
`normalized` / `alias`) and the caller flags non-exact matches as
`entity_merge_uncertainty`.
"""
from __future__ import annotations

import re

_ARTICLES = {"the", "a", "an"}
_PRONOUNS = {"he", "she", "it", "they", "him", "her", "them", "this", "that",
             "these", "those"}
# Abbreviation -> canonical full form (both map to the full form).
_ABBREV = {
    "usa": "united states", "u s a": "united states", "us": "united states",
    "u s": "united states", "uk": "united kingdom", "u k": "united kingdom",
    "uae": "united arab emirates", "nyc": "new york city",
    "uno": "united nations", "un": "united nations", "eu": "european union",
}
# Last-token aliasing is unsafe for these (place/org common nouns).
_BLOCK_LAST = {"city", "state", "states", "country", "county", "kingdom",
               "republic", "union", "nations", "university", "company",
               "corporation", "group", "team", "river", "mountain", "island",
               "sea", "ocean", "empire", "tower"}
_GIVEN_INITIAL = re.compile(r"^[a-z]$")


def _basic(text: object) -> str:
    s = "".join(c if c.isalnum() or c.isspace() else " " for c in str(text).lower())
    toks = [t for t in s.split() if t not in _ARTICLES]
    return " ".join(toks)


def _singular(token: str) -> str:
    if len(token) <= 3 or token.endswith("ss") or token.endswith("us"):
        return token
    if token.endswith("ies"):
        return token[:-3] + "y"
    if token.endswith("es") and len(token) > 4:
        return token[:-2]
    if token.endswith("s"):
        return token[:-1]
    return token


def normalize_unit(text: object) -> str:
    s = _basic(text)
    s = re.sub(r"\bdegrees?\b", "", s)
    s = re.sub(r"\bcelsius\b", "c", s)
    s = re.sub(r"\bpercent\b", "pct", s)
    return " ".join(s.split())


def full_norm(text: object) -> str:
    """basic + abbreviation expansion + light singularisation."""
    s = _basic(text)
    if s in _ABBREV:
        s = _ABBREV[s]
    else:
        s = " ".join(_ABBREV.get(t, t) for t in s.split())
    s = " ".join(_singular(t) for t in s.split())
    return s


def canonical_aliases(text: object) -> set[str]:
    """Set of canonical forms for an entity: the full norm + (cautiously) a
    surname alias for person-like proper names."""
    raw = str(text)
    forms = {full_norm(raw)}
    toks_raw = raw.split()
    norm_toks = full_norm(raw).split()
    # surname heuristic: 2-3 capitalised tokens, last token not a place/org word
    cap = [t for t in toks_raw if t[:1].isupper()]
    if 2 <= len(toks_raw) <= 3 and len(cap) >= 2 and norm_toks:
        last = norm_toks[-1]
        if last not in _BLOCK_LAST and len(last) >= 4 and not _GIVEN_INITIAL.match(last):
            forms.add(last)
    return {f for f in forms if f}


def entities_match(a: object, b: object) -> tuple[bool, str]:
    """Return (match, how) with how in exact|normalized|alias|none."""
    ba, bb = _basic(a), _basic(b)
    if ba and ba == bb:
        return True, "exact"
    fa, fb = full_norm(a), full_norm(b)
    if fa and fa == fb:
        return True, "normalized"
    aa, ab = canonical_aliases(a), canonical_aliases(b)
    if aa & ab:
        return True, "alias"
    return False, "none"


def is_pronoun(subject: object) -> bool:
    return _basic(subject) in _PRONOUNS


def resolve_pronoun(subject: object, antecedent: object | None) -> str:
    """Resolve a pronoun subject to a local antecedent (caller-provided)."""
    if antecedent and is_pronoun(subject):
        return str(antecedent)
    return str(subject)


__all__ = ["canonical_aliases", "entities_match", "full_norm", "is_pronoun",
           "normalize_unit", "resolve_pronoun"]


if __name__ == "__main__":
    tests = [("Lincoln", "Abraham Lincoln"), ("USA", "United States"),
             ("NYC", "New York City"), ("the patient", "patient"),
             ("Kansas City", "New York City"), ("Paris", "Paris"),
             ("John F. Kennedy", "Kennedy"), ("cats", "cat")]
    for a, b in tests:
        print(f"{a!r} vs {b!r} -> {entities_match(a, b)}")
