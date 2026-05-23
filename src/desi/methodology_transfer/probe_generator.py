"""Aufgabe 7 — candidate-probe generation per taxonomy
class.

For each discovered taxonomy class, generate a closed
probe definition with:

* a *newly named* probe id (no v4 probe name reused),
* a deterministic predicate (text -> bool) derived from
  the same feature schema the clustering used,
* a probe type from a closed list.

The probe predicates here are *candidates only*; v5.0
does not patch the runtime. Contamination is measured by
``contamination.py``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from ..logic.premises import PremiseExtractor
from .feature_extraction import (
    _MODAL_TOKENS, _NEGATION_SURFACE, _UNIVERSAL_SURFACE,
    _all_tokens, _content_tokens, _has_ed_suffix,
)
from .taxonomy import TaxonomyClass


class ProbeType(str, Enum):
    MARKER_LIKE         = "marker_like"
    STRUCTURAL          = "structural"
    GRAMMATICAL         = "grammatical"
    MODALITY            = "modality"
    CONTENT_CONSISTENCY = "content_consistency"
    WARRANT_LIKE        = "warrant_like"


# Generated probe ids — none collide with any v4 probe.
# ``MT-`` prefix differentiates from v4 (``C1``, ``W3``,
# ``S5``, etc.).
_PROBE_IDS: dict[str, str] = {
    TaxonomyClass.MT_MODAL_ASYMMETRY.value:        "MT-P01",
    TaxonomyClass.MT_NEGATION_ASYMMETRY.value:     "MT-P02",
    TaxonomyClass.MT_UNIVERSAL_LEAP.value:         "MT-P03",
    TaxonomyClass.MT_OVERLAP_LOOP.value:           "MT-P04",
    TaxonomyClass.MT_NOVEL_ENTITY.value:           "MT-P05",
    TaxonomyClass.MT_AMBIGUITY_DECISIVENESS.value: "MT-P06",
    TaxonomyClass.MT_AUDIT_OVER_SUPPORT.value:     "MT-P07",
    TaxonomyClass.MT_AUDIT_OVER_BLOCK.value:       "MT-P08",
    TaxonomyClass.MT_OTHER.value:                  "MT-P09",
}


_PROBE_TYPES: dict[str, ProbeType] = {
    TaxonomyClass.MT_MODAL_ASYMMETRY.value:        ProbeType.MODALITY,
    TaxonomyClass.MT_NEGATION_ASYMMETRY.value:     ProbeType.GRAMMATICAL,
    TaxonomyClass.MT_UNIVERSAL_LEAP.value:         ProbeType.MARKER_LIKE,
    TaxonomyClass.MT_OVERLAP_LOOP.value:           ProbeType.STRUCTURAL,
    TaxonomyClass.MT_NOVEL_ENTITY.value:           ProbeType.CONTENT_CONSISTENCY,
    TaxonomyClass.MT_AMBIGUITY_DECISIVENESS.value: ProbeType.WARRANT_LIKE,
    TaxonomyClass.MT_AUDIT_OVER_SUPPORT.value:     ProbeType.WARRANT_LIKE,
    TaxonomyClass.MT_AUDIT_OVER_BLOCK.value:       ProbeType.WARRANT_LIKE,
    TaxonomyClass.MT_OTHER.value:                  ProbeType.MARKER_LIKE,
}


# -- predicate factories ---------------------------------------------


def _has_any(text: str, vocab: frozenset[str]) -> bool:
    return bool(_all_tokens(text) & vocab)


# Tightened modal set — only the strong/categorical modals
# (epistemic hedges and normative auxiliaries excluded
# because protected-pool chains use them as standard
# hedging language).
_STRICT_MODALS: frozenset[str] = frozenset({
    "will", "cannot",
})

_STRICT_NEGATION: frozenset[str] = frozenset({
    "excluded", "denied", "withheld",
})

_STRICT_UNIVERSALS: frozenset[str] = frozenset({
    "every patient", "every cohort", "every market",
    "across every", "for every",
})


def _modality_asymmetry(text: str) -> bool:
    e = PremiseExtractor().extract(text)
    if e.conclusion is None or not e.premises:
        return False
    if not _has_any(e.conclusion.text, _STRICT_MODALS):
        return False
    return not any(
        _has_any(p.text, _STRICT_MODALS) for p in e.premises
    )


def _negation_asymmetry(text: str) -> bool:
    """Tightened: uses the rare-negation set (``excluded``,
    ``denied``, ``withheld``) — broader negation tokens
    like ``no`` / ``not`` / ``never`` appear in many
    protected chains."""
    e = PremiseExtractor().extract(text)
    if e.conclusion is None or not e.premises:
        return False
    if not _has_any(e.conclusion.text, _STRICT_NEGATION):
        return False
    return not any(
        _has_any(p.text, _STRICT_NEGATION)
        for p in e.premises
    )


def _universal_leap(text: str) -> bool:
    """Tightened: multi-word universal phrases only."""
    e = PremiseExtractor().extract(text)
    if e.conclusion is None or not e.premises:
        return False
    low = " " + e.conclusion.text.lower() + " "
    return any(p in low for p in _STRICT_UNIVERSALS)


def _overlap_loop(text: str) -> bool:
    e = PremiseExtractor().extract(text)
    if e.conclusion is None or not e.premises:
        return False
    concl = _content_tokens(e.conclusion.text)
    overlap_premises = 0
    overlap_total = 0
    for p in e.premises:
        shared = concl & _content_tokens(p.text)
        if shared:
            overlap_premises += 1
            overlap_total += len(shared)
    return overlap_premises >= 2 and overlap_total >= 3


def _novel_entity(text: str) -> bool:
    e = PremiseExtractor().extract(text)
    if e.conclusion is None or not e.premises:
        return False
    concl = _content_tokens(e.conclusion.text)
    if not concl:
        return False
    union = set()
    for p in e.premises:
        union |= _content_tokens(p.text)
    novel = concl - union
    return (len(novel) / len(concl)) >= 0.7


def _ambiguity_decisiveness(text: str) -> bool:
    # The v5.0 corpus carries explicit AMBIGUOUS hedge
    # markers in the conclusion. A safe content-level probe
    # that fires on these is impossible without inspecting
    # ground truth, so this probe is intentionally a
    # *meta-probe*: it requires explicit hedge tokens
    # ('may', 'might', 'appears to', 'could') in the
    # conclusion and abstains otherwise.
    _HEDGE = frozenset({
        "may", "might", "could", "appears", "appear",
        "likely", "perhaps", "possibly",
    })
    e = PremiseExtractor().extract(text)
    if e.conclusion is None or not e.premises:
        return False
    return _has_any(e.conclusion.text, _HEDGE)


def _audit_over_support(text: str) -> bool:
    # Placeholder predicate — there is no safe surface
    # signal that distinguishes audit-over-support failures
    # from valid SUPPORTED chains; this probe is generated
    # but is expected to be UNSAFE under the contamination
    # audit.
    return _negation_asymmetry(text) or _overlap_loop(text)


def _audit_over_block(text: str) -> bool:
    # Similar placeholder.
    return False


_PROBE_PREDICATES: dict[
    str, Callable[[str], bool],
] = {
    TaxonomyClass.MT_MODAL_ASYMMETRY.value:        _modality_asymmetry,
    TaxonomyClass.MT_NEGATION_ASYMMETRY.value:     _negation_asymmetry,
    TaxonomyClass.MT_UNIVERSAL_LEAP.value:         _universal_leap,
    TaxonomyClass.MT_OVERLAP_LOOP.value:           _overlap_loop,
    TaxonomyClass.MT_NOVEL_ENTITY.value:           _novel_entity,
    TaxonomyClass.MT_AMBIGUITY_DECISIVENESS.value: _ambiguity_decisiveness,
    TaxonomyClass.MT_AUDIT_OVER_SUPPORT.value:     _audit_over_support,
    TaxonomyClass.MT_AUDIT_OVER_BLOCK.value:       _audit_over_block,
    TaxonomyClass.MT_OTHER.value:                  lambda _t: False,
}


@dataclass(frozen=True)
class ProbeDefinition:
    probe_id: str
    cluster_name: str
    probe_type: str
    description: str

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_id": self.probe_id,
            "cluster_name": self.cluster_name,
            "probe_type": self.probe_type,
            "description": self.description,
        }


def generate_probes_for_taxonomy(
    taxonomy_names: tuple[str, ...],
) -> tuple[ProbeDefinition, ...]:
    out: list[ProbeDefinition] = []
    for name in taxonomy_names:
        out.append(ProbeDefinition(
            probe_id=_PROBE_IDS[name],
            cluster_name=name,
            probe_type=_PROBE_TYPES[name].value,
            description=_describe(name),
        ))
    return tuple(out)


def _describe(name: str) -> str:
    return {
        TaxonomyClass.MT_MODAL_ASYMMETRY.value:
            "suspend when conclusion uses a modal verb absent from every premise",
        TaxonomyClass.MT_NEGATION_ASYMMETRY.value:
            "suspend when conclusion uses negation absent from every premise",
        TaxonomyClass.MT_UNIVERSAL_LEAP.value:
            "suspend when conclusion contains universal quantifier markers",
        TaxonomyClass.MT_OVERLAP_LOOP.value:
            "suspend when conclusion tokens span >=2 premises with >=3 total overlap",
        TaxonomyClass.MT_NOVEL_ENTITY.value:
            "suspend when >=70% of conclusion content tokens are absent from premises",
        TaxonomyClass.MT_AMBIGUITY_DECISIVENESS.value:
            "abstain when conclusion uses hedge tokens (may, might, could)",
        TaxonomyClass.MT_AUDIT_OVER_SUPPORT.value:
            "no safe surface signal; placeholder probe",
        TaxonomyClass.MT_AUDIT_OVER_BLOCK.value:
            "no safe surface signal; placeholder probe",
        TaxonomyClass.MT_OTHER.value:
            "catchall; never fires",
    }[name]


def probe_fires(probe_cluster: str, text: str) -> bool:
    pred = _PROBE_PREDICATES.get(probe_cluster)
    if pred is None:
        return False
    return pred(text)


__all__ = [
    "ProbeDefinition", "ProbeType",
    "generate_probes_for_taxonomy", "probe_fires",
]
