"""A fail-open WordNet adapter — the reference offline ontology channel.

WordNet is chosen as the FIRST real adapter (over OpenCyc) because it is small, offline, and clean
for sense/hypernym typing — no network, no multi-GB OWL load. OpenCyc 2012 is an archival upper
ontology with near-zero coverage of technical/research vocabulary; it belongs as a later optional
channel, measured before adoption, not as the default.

This adapter is FAIL-OPEN by contract: it tries ``nltk.corpus.wordnet`` then the ``wn`` package; if
neither corpus is installed it raises ``OntologyUnavailable`` from :meth:`senses`, which the probe
catches and turns into an ``unavailable`` hint. So importing this module never requires the corpus,
and a deployment without WordNet simply gets a silent (no-op) channel — never an error in the gate.

Type derivation: a WordNet synset's *lexicographer file* (e.g. ``noun.person`` / ``noun.artifact`` /
``noun.cognition``) is a good coarse 'kind'. We use that category as the top type, so
``operator`` -> {``person``, ``cognition``, …} comes out as an ambiguous-across-kinds term — exactly
the disambiguation signal the probe consumes. Deterministic given a fixed corpus version.
"""
from __future__ import annotations

from desi_router.ontology_probe.base import WEAK, Sense


class OntologyUnavailable(RuntimeError):
    """Raised when no WordNet corpus is importable. The probe catches this and degrades, fail-open."""


def _load_wordnet():
    """Return a callable ``synsets(term) -> list[synset-like]`` or raise OntologyUnavailable.

    Tries NLTK first (most common), then the ``wn`` package. Both are optional and offline; neither is
    a hard dependency of desi_router."""
    try:
        from nltk.corpus import wordnet as _wn  # type: ignore

        _wn.all_synsets  # touch the lazy corpus loader so a missing data file fails HERE, not later
        return lambda term: _wn.synsets(term), "wordnet_nltk"
    except Exception:  # noqa: BLE001 — fall through to the next backend
        pass
    try:
        import wn as _wnpkg  # type: ignore

        return lambda term: _wnpkg.synsets(term), "wordnet_wn"
    except Exception as exc:  # noqa: BLE001
        raise OntologyUnavailable("no WordNet corpus (nltk or wn) available") from exc


def _category(synset) -> str:
    """Coarse 'kind' for a synset: the lexicographer-file category (``noun.person`` -> ``person``).
    Falls back to the part of speech, then empty."""
    for getter in ("lexname", "pos"):
        fn = getattr(synset, getter, None)
        if callable(fn):
            try:
                val = fn()
            except Exception:  # noqa: BLE001
                continue
            if val:
                return str(val).split(".")[-1]
    return ""


def _name(synset) -> str:
    fn = getattr(synset, "name", None)
    try:
        return str(fn() if callable(fn) else (fn or ""))
    except Exception:  # noqa: BLE001
        return ""


class WordNetAdapter:
    source = "wordnet"

    def __init__(self) -> None:
        # resolve the backend lazily and cache it; stays uninitialised until first probe.
        self._synsets = None
        self._loaded = False

    def _ensure(self):
        if not self._loaded:
            self._synsets, self.source = _load_wordnet()
            self._loaded = True
        return self._synsets

    def senses(self, term: str) -> tuple[Sense, ...]:
        synsets_of = self._ensure()
        out: list[Sense] = []
        for ss in synsets_of((term or "").strip()) or ():
            cat = _category(ss)
            name = _name(ss)
            type_path = tuple(t for t in (cat, name) if t)
            out.append(Sense(sense=name or cat or (term or ""), type_path=type_path,
                             confidence=WEAK))
        return tuple(out)
