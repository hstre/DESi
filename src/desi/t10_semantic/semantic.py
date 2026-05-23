"""v3.111 — closed set of text-derived semantic
candidate dimensions.

Each function takes a trajectory text and returns
one float. The candidates are deliberately
structural / lexical, NOT id-derived. If any of
them recovers the v3.105 entanglements without
metadata, T10's expansion vocabulary has a
genuine semantic alternative; if none do, the
metadata candidates are confirmed as proxies.

Closed taxonomy:

* ``MEAN_WORD_LENGTH``     - average length of
  alphabetic tokens.
* ``UNIQUE_TOKEN_COUNT``   - number of distinct
  tokens >= 3 chars.
* ``CONSONANT_VOWEL_RATIO`` - ratio of
  consonants to vowels in the text.
* ``BIGRAM_DIVERSITY``     - distinct bigrams /
  total bigrams.
* ``FIRST_NOUN_HASH``      - 4-bit sha256 of the
  first lower-cased token of length >= 4 (a
  rough noun-proxy).
* ``CAPITAL_RATIO``        - fraction of
  characters that are upper-case (writing
  style).
"""
from __future__ import annotations

import re
from enum import Enum
from hashlib import sha256


_TOKEN_RE = re.compile(r"[a-zA-Z]+")
_VOWELS = set("aeiouAEIOU")


class SemanticCandidate(str, Enum):
    MEAN_WORD_LENGTH       = "mean_word_length"
    UNIQUE_TOKEN_COUNT     = "unique_token_count"
    CONSONANT_VOWEL_RATIO  = (
        "consonant_vowel_ratio"
    )
    BIGRAM_DIVERSITY       = "bigram_diversity"
    FIRST_NOUN_HASH        = "first_noun_hash"
    CAPITAL_RATIO          = "capital_ratio"


SEMANTIC_CANDIDATES: tuple[str, ...] = tuple(
    c.value for c in SemanticCandidate
)


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _mean_word_length(text: str) -> float:
    toks = _tokens(text)
    if not toks:
        return 0.0
    return _round(sum(len(t) for t in toks) / len(toks))


def _unique_token_count(text: str) -> float:
    return float(
        len({t for t in _tokens(text) if len(t) >= 3}),
    )


def _consonant_vowel_ratio(text: str) -> float:
    letters = [
        c for c in text if c.isalpha()
    ]
    if not letters:
        return 0.0
    vowels = sum(1 for c in letters if c in _VOWELS)
    cons = len(letters) - vowels
    if vowels == 0:
        return float(cons)
    return _round(cons / vowels)


def _bigram_diversity(text: str) -> float:
    toks = _tokens(text)
    if len(toks) < 2:
        return 0.0
    bigrams = [
        (toks[i], toks[i + 1])
        for i in range(len(toks) - 1)
    ]
    return _round(
        len(set(bigrams)) / len(bigrams),
    )


def _first_noun_hash(text: str) -> float:
    for t in _tokens(text):
        if len(t) >= 4:
            digest = sha256(
                t.encode("utf-8"),
            ).digest()
            return float(digest[0] & 0x0F)
    return 0.0


def _capital_ratio(text: str) -> float:
    letters = [
        c for c in text if c.isalpha()
    ]
    if not letters:
        return 0.0
    upper = sum(1 for c in letters if c.isupper())
    return _round(upper / len(letters))


_FNS: dict[str, "callable"] = {
    SemanticCandidate.MEAN_WORD_LENGTH.value:
        _mean_word_length,
    SemanticCandidate.UNIQUE_TOKEN_COUNT.value:
        _unique_token_count,
    SemanticCandidate.CONSONANT_VOWEL_RATIO.value:
        _consonant_vowel_ratio,
    SemanticCandidate.BIGRAM_DIVERSITY.value:
        _bigram_diversity,
    SemanticCandidate.FIRST_NOUN_HASH.value:
        _first_noun_hash,
    SemanticCandidate.CAPITAL_RATIO.value:
        _capital_ratio,
}


def semantic_value(
    candidate: str, text: str,
) -> float:
    return _FNS[candidate](text)


__all__ = [
    "SEMANTIC_CANDIDATES",
    "SemanticCandidate",
    "semantic_value",
]
