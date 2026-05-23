"""Aufgabe 6 — taxonomy generation from discovered clusters.

Each cluster gets a *generated* name derived from its
centroid features. The names are intentionally generic so
no v4 class identifier is reused.

Naming rule (closed cascade, evaluated top-down):

* If centroid[``expected_ambiguous``] > 0.5 and
  (audit_supported or audit_rejected) > 0.5:
  ``MT_AMBIGUITY_DECISIVENESS``
* If centroid[``modal_in_concl``] > 0.5 and
  centroid[``modal_in_any_premise``] <= 0.2:
  ``MT_MODAL_ASYMMETRY``
* If centroid[``negation_in_concl``] > 0.5 and
  centroid[``negation_in_any_premise``] <= 0.2:
  ``MT_NEGATION_ASYMMETRY``
* If centroid[``overlap_premises_count``] >= 1.5 and
  centroid[``overlap_total_tokens``] >= 2.5:
  ``MT_OVERLAP_LOOP``
* If centroid[``universal_in_concl``] > 0.5:
  ``MT_UNIVERSAL_LEAP``
* If centroid[``concl_novel_token_ratio``] >= 0.7:
  ``MT_NOVEL_ENTITY``
* If centroid[``audit_supported``] > 0.5 and
  centroid[``expected_invalid``] > 0.5:
  ``MT_AUDIT_OVER_SUPPORT``
* If centroid[``audit_rejected``] > 0.5 and
  centroid[``expected_valid``] > 0.5:
  ``MT_AUDIT_OVER_BLOCK``
* Otherwise:
  ``MT_OTHER``

The rule cascade is strict: each cluster receives exactly
one closed name. The closed-class enumeration is
``TaxonomyClass``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .cluster_discovery import Cluster
from .feature_extraction import FEATURE_NAMES


class TaxonomyClass(str, Enum):
    """Closed v5.0 taxonomy. *Newly named*: no value
    matches any v4 closed-class identifier."""

    MT_MODAL_ASYMMETRY        = "MT_MODAL_ASYMMETRY"
    MT_OVERLAP_LOOP           = "MT_OVERLAP_LOOP"
    MT_NEGATION_ASYMMETRY     = "MT_NEGATION_ASYMMETRY"
    MT_UNIVERSAL_LEAP         = "MT_UNIVERSAL_LEAP"
    MT_NOVEL_ENTITY           = "MT_NOVEL_ENTITY"
    MT_AUDIT_OVER_SUPPORT     = "MT_AUDIT_OVER_SUPPORT"
    MT_AUDIT_OVER_BLOCK       = "MT_AUDIT_OVER_BLOCK"
    MT_AMBIGUITY_DECISIVENESS = "MT_AMBIGUITY_DECISIVENESS"
    MT_OTHER                  = "MT_OTHER"


_FEAT = {n: i for i, n in enumerate(FEATURE_NAMES)}


def _name_for(centroid: tuple[float, ...]) -> str:
    """Closed cascade. Ambiguity-decisiveness is checked
    first because it gates on ``expected_ambiguous`` — a
    label-restricted signal that does not collide with the
    surface-token rules below. Surface-token rules then run
    most-specific-first; audit-state combinations serve as
    fallback for failures that lack a strong surface
    signature."""

    def f(name: str) -> float:
        return centroid[_FEAT[name]]

    # 1) Ambiguity-decisiveness: chain was AMBIGUOUS but
    #    DESi committed to a verdict. Gated on the
    #    AMBIGUOUS ground-truth bit so it does not fire on
    #    VALID/INVALID samples.
    if (
        f("expected_ambiguous") > 0.5
        and (
            f("audit_supported") > 0.5
            or f("audit_rejected") > 0.5
        )
    ):
        return TaxonomyClass.MT_AMBIGUITY_DECISIVENESS.value
    # 2) Modal asymmetry (strong lexical signal).
    if (
        f("modal_in_concl") > 0.5
        and f("modal_in_any_premise") <= 0.2
    ):
        return TaxonomyClass.MT_MODAL_ASYMMETRY.value
    # 3) Negation asymmetry.
    if (
        f("negation_in_concl") > 0.5
        and f("negation_in_any_premise") <= 0.2
    ):
        return TaxonomyClass.MT_NEGATION_ASYMMETRY.value
    # 4) Overlap loop (cycle-disguise shape). Checked
    #    before universal-leap because the cycle pattern can
    #    accidentally pick up "every" tokens from the
    #    repeated conclusion phrasing.
    if (
        f("overlap_premises_count") >= 1.5
        and f("overlap_total_tokens") >= 2.5
    ):
        return TaxonomyClass.MT_OVERLAP_LOOP.value
    # 5) Universal leap.
    if f("universal_in_concl") > 0.5:
        return TaxonomyClass.MT_UNIVERSAL_LEAP.value
    # 6) Novel-entity (high conclusion-novelty relative to
    #    premises).
    if f("concl_novel_token_ratio") >= 0.7:
        return TaxonomyClass.MT_NOVEL_ENTITY.value
    # 7) Audit said SUPPORT on an INVALID chain.
    if (
        f("audit_supported") > 0.5
        and f("expected_invalid") > 0.5
    ):
        return TaxonomyClass.MT_AUDIT_OVER_SUPPORT.value
    # 8) Audit said REJECT on a VALID chain.
    if (
        f("audit_rejected") > 0.5
        and f("expected_valid") > 0.5
    ):
        return TaxonomyClass.MT_AUDIT_OVER_BLOCK.value
    return TaxonomyClass.MT_OTHER.value


@dataclass(frozen=True)
class TaxonomyEntry:
    """One row of the v5.0 closed taxonomy. The
    ``taxonomy_name`` is one of the closed
    ``TaxonomyClass`` values. ``size`` is the count of
    failure samples assigned to this name; ``member_ids``
    enumerates them."""

    taxonomy_name: str
    size: int
    member_ids: tuple[str, ...]
    representative_centroid: tuple[float, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "taxonomy_name": self.taxonomy_name,
            "size": self.size,
            "member_ids": list(self.member_ids),
            "representative_centroid":
                list(self.representative_centroid),
        }


def classify_sample_features(
    feats: tuple[float, ...],
) -> str:
    """Public-named helper for per-sample classification.
    Same closed cascade as ``_name_for`` but applied to a
    single sample's feature vector."""
    return _name_for(feats)


def assign_names(
    clusters: tuple[Cluster, ...],
    sample_features: dict[str, tuple[float, ...]] | None = None,
) -> tuple[TaxonomyEntry, ...]:
    """Build the v5.0 taxonomy by classifying each member
    sample individually and grouping by closed name.
    Falls back to centroid-based naming when per-sample
    features are not supplied."""
    by_name: dict[str, list[tuple[str, tuple[float, ...]]]] = {}
    for c in clusters:
        for member_id in c.member_ids:
            if (
                sample_features is not None
                and member_id in sample_features
            ):
                feats = sample_features[member_id]
            else:
                feats = c.centroid
            name = _name_for(feats)
            by_name.setdefault(name, []).append(
                (member_id, feats),
            )
    out: list[TaxonomyEntry] = []
    for name in sorted(by_name):
        members = by_name[name]
        # representative centroid = mean over members
        n = len(members)
        if n == 0:
            continue
        sums = [0.0] * len(FEATURE_NAMES)
        for _, f in members:
            for i, v in enumerate(f):
                sums[i] += v
        rep = tuple(s / n for s in sums)
        out.append(TaxonomyEntry(
            taxonomy_name=name,
            size=n,
            member_ids=tuple(m for m, _ in members),
            representative_centroid=rep,
        ))
    # Sort by size descending then by name.
    out.sort(key=lambda e: (-e.size, e.taxonomy_name))
    return tuple(out)


__all__ = [
    "TaxonomyClass", "TaxonomyEntry", "assign_names",
    "classify_sample_features",
]
