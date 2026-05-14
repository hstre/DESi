"""Premise extraction — first stage of the v1.2 logical audit.

The extractor consumes free-form text and emits a structured
:class:`Propositions` record: a tuple of typed :class:`Premise`
objects plus an optional :class:`ConclusionProposition`. Every
premise carries its own deterministic id so the proof chain can
later reference it by hash.

Authority-independence is *enforced here*: source / author / title
are never inputs to the extractor. The only signal is the text of
the proposition itself. Five premise kinds are recognised:

* ``UNIVERSAL``    — "All X are Y"
* ``PARTICULAR``   — "S is Y" / "S is a Y"
* ``CONDITIONAL``  — "If P then Q"
* ``IMPLICATION``  — "P → Q"
* ``AUTHORITY``    — "X says Y"   (recognised so it can be
                    *rejected* — never accepted as evidence)
* ``ATOMIC``       — anything else (an unstructured proposition)

Synonym normalisation is intentionally narrow (a small inflection
table) so that "men" and "man" canonicalise to the same atom in a
syllogism.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum


class PremiseKind(str, Enum):
    UNIVERSAL = "universal"
    PARTICULAR = "particular"
    CONDITIONAL = "conditional"
    IMPLICATION = "implication"
    AUTHORITY = "authority"
    ATOMIC = "atomic"


# v1.2 directive: a tiny, well-known inflection map. We intentionally
# do not call out to a stemmer / NLP library — every transformation
# the extractor performs must be inspectable here.
_INFLECTIONS: dict[str, str] = {
    "men": "man",
    "women": "woman",
    "people": "person",
    "children": "child",
    "mice": "mouse",
    "feet": "foot",
}


def _normalise_word(word: str) -> str:
    w = word.strip().lower()
    if w in _INFLECTIONS:
        return _INFLECTIONS[w]
    return w


def _normalise_phrase(phrase: str) -> str:
    return " ".join(_normalise_word(w) for w in phrase.split())


def _premise_id(text: str, kind: PremiseKind) -> str:
    h = hashlib.sha256()
    h.update(kind.value.encode("utf-8"))
    h.update(b"\x00")
    h.update(_normalise_phrase(text).encode("utf-8"))
    return "pr_" + h.hexdigest()[:12]


@dataclass(frozen=True)
class Premise:
    """One typed proposition extracted from the input text.

    Identity rule: same ``kind`` + same canonicalised text →
    identical ``premise_id``. Two textual variants that mean the
    same thing collide deterministically, so the proof chain stays
    stable across reformulations.
    """

    premise_id: str
    text: str
    kind: PremiseKind
    subject: str = ""
    predicate: str = ""
    antecedent: str = ""
    consequent: str = ""
    speaker: str = ""

    def to_dict(self) -> dict:
        return {
            "premise_id": self.premise_id,
            "text": self.text,
            "kind": self.kind.value,
            "subject": self.subject,
            "predicate": self.predicate,
            "antecedent": self.antecedent,
            "consequent": self.consequent,
            "speaker": self.speaker,
        }


@dataclass(frozen=True)
class ConclusionProposition:
    """The proposition the input asserts as conclusion."""

    text: str
    kind: PremiseKind
    subject: str = ""
    predicate: str = ""
    antecedent: str = ""
    consequent: str = ""
    speaker: str = ""

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "kind": self.kind.value,
            "subject": self.subject,
            "predicate": self.predicate,
            "antecedent": self.antecedent,
            "consequent": self.consequent,
            "speaker": self.speaker,
        }


@dataclass(frozen=True)
class Propositions:
    """Structured output of :meth:`PremiseExtractor.extract`."""

    premises: tuple[Premise, ...] = field(default_factory=tuple)
    conclusion: ConclusionProposition | None = None
    has_explicit_chain: bool = False

    @property
    def premise_ids(self) -> tuple[str, ...]:
        return tuple(p.premise_id for p in self.premises)


# ---------------------------------------------------------------------------
# Sentence patterns
# ---------------------------------------------------------------------------


_RE_UNIVERSAL = re.compile(
    r"^all\s+(?P<subj>[\w\s]+?)\s+are\s+(?P<pred>[\w\s]+?)\.?$",
    re.IGNORECASE,
)
_RE_PARTICULAR_A = re.compile(
    r"^(?P<subj>[\w][\w\s]*?)\s+is\s+a\s+(?P<pred>[\w][\w\s]*?)\.?$",
    re.IGNORECASE,
)
_RE_PARTICULAR = re.compile(
    r"^(?P<subj>[\w][\w\s]*?)\s+is\s+(?P<pred>[\w][\w\s]*?)\.?$",
    re.IGNORECASE,
)
_RE_CONDITIONAL = re.compile(
    r"^if\s+(?P<ant>.+?)\s+then\s+(?P<con>.+?)\.?$",
    re.IGNORECASE,
)
_RE_IMPLICATION = re.compile(
    r"^(?P<ant>[\w][\w\s]*?)\s*(?:->|→)\s*(?P<con>[\w][\w\s]*?)\.?$",
)
_RE_AUTHORITY = re.compile(
    r"^(?P<speaker>[\w][\w\s]*?)\s+says\s+(?P<claim>.+?)\.?$",
    re.IGNORECASE,
)
_RE_THEREFORE = re.compile(r"\bTherefore\b", re.IGNORECASE)


def _classify(text: str) -> tuple[PremiseKind, dict[str, str]]:
    text = text.strip().rstrip(".").strip()
    if not text:
        return PremiseKind.ATOMIC, {}
    m = _RE_UNIVERSAL.match(text)
    if m:
        return PremiseKind.UNIVERSAL, {
            "subject": _normalise_phrase(m.group("subj")),
            "predicate": _normalise_phrase(m.group("pred")),
        }
    m = _RE_CONDITIONAL.match(text)
    if m:
        return PremiseKind.CONDITIONAL, {
            "antecedent": _normalise_phrase(m.group("ant")),
            "consequent": _normalise_phrase(m.group("con")),
        }
    m = _RE_IMPLICATION.match(text)
    if m:
        return PremiseKind.IMPLICATION, {
            "antecedent": _normalise_phrase(m.group("ant")),
            "consequent": _normalise_phrase(m.group("con")),
        }
    m = _RE_AUTHORITY.match(text)
    if m:
        return PremiseKind.AUTHORITY, {
            "speaker": _normalise_phrase(m.group("speaker")),
            "predicate": _normalise_phrase(m.group("claim")),
        }
    m = _RE_PARTICULAR_A.match(text)
    if m:
        return PremiseKind.PARTICULAR, {
            "subject": _normalise_phrase(m.group("subj")),
            "predicate": _normalise_phrase(m.group("pred")),
        }
    m = _RE_PARTICULAR.match(text)
    if m:
        return PremiseKind.PARTICULAR, {
            "subject": _normalise_phrase(m.group("subj")),
            "predicate": _normalise_phrase(m.group("pred")),
        }
    return PremiseKind.ATOMIC, {}


def _build_premise(text: str) -> Premise:
    kind, fields = _classify(text)
    return Premise(
        premise_id=_premise_id(text, kind),
        text=text.strip(),
        kind=kind,
        subject=fields.get("subject", ""),
        predicate=fields.get("predicate", ""),
        antecedent=fields.get("antecedent", ""),
        consequent=fields.get("consequent", ""),
        speaker=fields.get("speaker", ""),
    )


def _build_conclusion(text: str) -> ConclusionProposition:
    kind, fields = _classify(text)
    return ConclusionProposition(
        text=text.strip(),
        kind=kind,
        subject=fields.get("subject", ""),
        predicate=fields.get("predicate", ""),
        antecedent=fields.get("antecedent", ""),
        consequent=fields.get("consequent", ""),
        speaker=fields.get("speaker", ""),
    )


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?]\s+", text)
            if s.strip()]


class PremiseExtractor:
    """Extract typed premises + an optional conclusion from text.

    The extractor is stateless and deterministic. The same input
    bytes always produce identical :class:`Propositions`.
    """

    def extract(self, text: str) -> Propositions:
        if not isinstance(text, str):
            raise TypeError("extract() requires a str input")
        text = text.strip()
        if not text:
            return Propositions()

        # Split on the literal word "Therefore" — explicit chain signal.
        if _RE_THEREFORE.search(text):
            parts = _RE_THEREFORE.split(text, maxsplit=1)
            premise_block = parts[0].strip().rstrip(".")
            conclusion_block = parts[1].strip().rstrip(".")
            premise_sentences = _split_sentences(premise_block + ".")
            premises = tuple(
                _build_premise(s) for s in premise_sentences if s
            )
            conclusion = (
                _build_conclusion(conclusion_block) if conclusion_block
                else None
            )
            return Propositions(
                premises=premises,
                conclusion=conclusion,
                has_explicit_chain=conclusion is not None,
            )

        # No explicit "Therefore". Treat every sentence as a premise.
        sentences = _split_sentences(text)
        premises = tuple(_build_premise(s) for s in sentences)
        return Propositions(
            premises=premises,
            conclusion=None,
            has_explicit_chain=False,
        )


__all__ = [
    "ConclusionProposition",
    "Premise",
    "PremiseExtractor",
    "PremiseKind",
    "Propositions",
]
