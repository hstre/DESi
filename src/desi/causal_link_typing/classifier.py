"""Aufgaben 2 — closed-priority link-type classifier.

Each link is inspected for lexical features in a fixed
priority order. The first matching feature wins; the fallback
is ``LinkType.UNKNOWN``. Read-only — no LLM, no LogicalAuditor.
"""
from __future__ import annotations

from .enums import LinkType
from .extractor import Link


# Authority verbs (v1.8 lemma library + v3.16 extensions).
_AUTHORITY_VERBS: tuple[str, ...] = (
    " says ", " said ", " states ", " stated ",
    " claims ", " claimed ", " declares ", " declared ",
    " concludes ", " concluded ", " announces ", " announced ",
    " publishes ", " published ", " proves ", " proved ",
    " reports ", " reported ",
    # v3.16 extensions for adversarial cases that bypass v1.8.
    " wrote ", " writes ", " argued ", " argues ",
    " noted ", " notes ",
    # Note: "observed/observes" intentionally *omitted* — they
    # appear naturally in non-authority sentences like "every
    # observed swan is white" and would shadow LOGICAL.
    " thought ", " thinks ", " felt ", " feels ",
    " suggested ", " suggests ", " believed ", " believes ",
    " according to ",
)


# Metaphorical markers — "X is a Y", "X is an Y", "like a/as if".
_METAPHOR_MARKERS: tuple[str, ...] = (
    " is a ", " is an ", " are a ", " are an ",
    " like a ", " as if ", " as a ",
    " metaphorically ", " figuratively ",
    " loosely speaking ",
)


# Logical-implication markers — quantifiers, syllogism vocab,
# explicit modus ponens, axioms, theorems, lemmas.
_LOGICAL_MARKERS: tuple[str, ...] = (
    " all ", " every ", " each ", " any ", " some ",
    " modus ponens ", " syllogism ", " axiom ", " axioms ",
    " theorem ", " theorems ", " lemma ", " lemmas ",
    " universal instantiation ", " therefore ",
    " consistently ", " universally ", " invariably ",
    " always ", " globally ", " everywhere ",
)


# Physical-causal vocabulary — natural processes and physical
# state verbs/nouns.
_PHYSICAL_VERBS: tuple[str, ...] = (
    " flowed ", " flows ", " flow ",
    " rose ", " rises ", " rising ",
    " fell ", " falls ", " falling ",
    " expanded ", " expands ", " contract ", " contracted ",
    " boiled ", " boils ", " boiling ", " whistled ", " whistles ",
    " froze ", " freezes ", " freezing ", " melted ", " melts ",
    " burned ", " burns ", " ignited ", " ignites ",
    " evaporated ", " vaporised ", " condensed ", " crystallised ",
    " vibrated ", " vibrates ", " resonated ", " resonates ",
    " collided ", " collides ", " radiated ", " radiates ",
    " absorbed ", " absorbs ", " reflected ", " reflects ",
    " heated ", " heats ", " cooled ", " cools ",
    " orbited ", " orbits ", " transit ", " transits ",
    " drifted ", " drifts ", " erupted ", " erupts ",
    " germinated ", " germinates ", " sprouted ", " sprouts ",
    " bloomed ", " blooms ", " ripened ", " ripens ",
    " swelled ", " swells ", " hardened ", " hardens ",
    " filled ", " fills ", " spread ", " spreads ",
    " poured ", " pours ", " soaked ", " soaks ",
    " evaporates ", " condenses ", " freezes ", " thaws ",
    " thawed ",
)

_PHYSICAL_NOUNS: tuple[str, ...] = (
    " heat ", " temperature ", " pressure ", " flame ",
    " steam ", " water ", " ice ", " air ", " wind ",
    " current ", " radiation ", " atom ", " atoms ",
    " molecule ", " particle ", " photon ", " electron ",
    " gravity ", " mass ", " density ", " volume ",
    " velocity ", " force ", " momentum ", " energy ",
    " kettle ", " kiln ", " oven ", " hive ", " comb ",
    " pollen ", " stigma ", " ovary ", " tulip ",
    " seedling ", " sprout ", " seed ", " bud ", " bloom ",
    " curd ", " curds ", " whey ", " dough ", " loaf ", " yeast ",
    " bread ",
)


# Institutional/agency vocabulary — organisations, policies,
# roles. Detects causal claims about social/institutional events.
_INSTITUTIONAL_MARKERS: tuple[str, ...] = (
    " policy ", " ministry ", " minister ", " ministers ",
    " parliament ", " congress ", " government ", " cabinet ",
    " court ", " judge ", " judges ", " judiciary ",
    " company ", " corporation ", " firm ", " bank ",
    " market ", " markets ", " economy ", " inflation ",
    " tariff ", " tariffs ", " election ", " elections ",
    " trial ", " trials ", " regulation ", " regulator ",
    " auditor ", " accountant ", " books ", " ledger ",
    " trade ", " trade war ", " import ", " imports ",
    " export ", " exports ", " bill ", " act ",
    " law ", " laws ", " statute ", " statutes ",
    " convention ", " treaty ", " merger ",
    " licence ", " license ", " licensing ",
    " budget ", " plan ", " planning ", " contract ", " contracts ",
)


# Temporal markers — pure ordering with no causal vocab.
_TEMPORAL_MARKERS: tuple[str, ...] = (
    " morning ", " noon ", " afternoon ", " evening ",
    " midnight ", " dawn ", " dusk ", " twilight ",
    " then ", " next ", " after ", " before ", " later ",
    " yesterday ", " today ", " tomorrow ", " overnight ",
    " at five ", " at six ", " at seven ",
)


# Numeric / tool vocabulary.
_NUMBER_WORDS: frozenset[str] = frozenset({
    "one", "two", "three", "four", "five", "six", "seven",
    "eight", "nine", "ten", "eleven", "twelve", "thirteen",
    "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
    "nineteen", "twenty", "thirty", "forty", "fifty", "sixty",
    "seventy", "eighty", "ninety", "hundred", "thousand",
})


def _has_number(text: str) -> bool:
    padded = " " + text.lower() + " "
    for ch in ",.:;!?'\"-":
        padded = padded.replace(ch, " ")
    for tok in padded.split():
        if tok in _NUMBER_WORDS:
            return True
        if any(c.isdigit() for c in tok):
            return True
    return False


def _matches(text: str, markers: tuple[str, ...]) -> bool:
    padded = " " + text.lower() + " "
    # Normalise punctuation so markers like " loosely speaking "
    # match against texts ending the marker in a comma or period.
    for ch in ",.:;!?'\"":
        padded = padded.replace(ch, " ")
    return any(m in padded for m in markers)


def classify_link(link: Link) -> LinkType:
    """Return exactly one ``LinkType`` for the link.

    Priority order (first match wins):
      1. AUTHORITY_ASSERTION
      2. METAPHORICAL_ASSOCIATION
      3. TOOL_DEPENDENCY  (numbers on both ends)
      4. LOGICAL_IMPLICATION
      5. PHYSICAL_CAUSAL
      6. INSTITUTIONAL_CAUSAL
      7. TEMPORAL_SEQUENCE
      8. UNKNOWN (fallback)
    """
    src = link.source_text
    tgt = link.target_text

    # 1 — authority assertion in either end.
    if _matches(src, _AUTHORITY_VERBS) or _matches(tgt, _AUTHORITY_VERBS):
        return LinkType.AUTHORITY_ASSERTION

    # 2 — metaphor markers in either end.
    if _matches(src, _METAPHOR_MARKERS) or _matches(tgt, _METAPHOR_MARKERS):
        return LinkType.METAPHORICAL_ASSOCIATION

    # 3 — numbers in both ends → arithmetic / tool dependency.
    if _has_number(src) and _has_number(tgt):
        return LinkType.TOOL_DEPENDENCY

    # 4 — logical implication via quantifier / proof vocabulary.
    if _matches(src, _LOGICAL_MARKERS) or _matches(tgt, _LOGICAL_MARKERS):
        return LinkType.LOGICAL_IMPLICATION

    # 5 — institutional / agency vocabulary on either side. We
    # check institutional *before* physical because phrases like
    # "Parliament passed a bill. Tax rates rose." carry physical
    # verbs ("rose") in their natural-causal effect sentence; the
    # link itself is institutional and the priority should reflect
    # that.
    if (_matches(src, _INSTITUTIONAL_MARKERS)
            or _matches(tgt, _INSTITUTIONAL_MARKERS)):
        return LinkType.INSTITUTIONAL_CAUSAL

    # 6 — physical-causal verbs or nouns on either side.
    if (_matches(src, _PHYSICAL_VERBS) or _matches(tgt, _PHYSICAL_VERBS)
            or _matches(src, _PHYSICAL_NOUNS)
            or _matches(tgt, _PHYSICAL_NOUNS)):
        return LinkType.PHYSICAL_CAUSAL

    # 7 — purely temporal markers, no causal verbs.
    if (_matches(src, _TEMPORAL_MARKERS)
            or _matches(tgt, _TEMPORAL_MARKERS)):
        return LinkType.TEMPORAL_SEQUENCE

    # 8 — fallback.
    return LinkType.UNKNOWN


def classify_all(
    links: tuple[Link, ...],
) -> tuple[tuple[Link, LinkType], ...]:
    return tuple((l, classify_link(l)) for l in links)


__all__ = ["classify_all", "classify_link"]
