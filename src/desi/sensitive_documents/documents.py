"""v17.0 - synthetic document corpus for the
sensitive-document integrity sandbox.

CRITICAL SAFETY / ETHICS NOTES
==============================
1. EVERYTHING here is SYNTHETIC and ANONYMISED.
   Entities are abstract placeholders (ENTITY_A,
   ENTITY_B, ...) with NO real-world identity.
   Documents carry only STRUCTURAL METADATA
   (class, provenance grade, source id, a synthetic
   content fingerprint) - NEVER any real content,
   names, victim data, minors' data, intimate
   detail, or sensitive material of any kind.

2. The closed claim vocabulary has NO "involved",
   "guilty", "perpetrator", or "participant" value.
   The strongest claim is VERIFIED_DOCUMENT_PRESENCE
   - that a document verifiably exists. MENTION,
   REFERENCE, and CONTEXTUAL_ASSOCIATION are NOT
   involvement. The governing rule is:

       Erwaehnung != Beteiligung
       (mention != involvement)

3. Every entity stays EPISTEMICALLY NEUTRAL. DESi
   never derives guilt, never builds a suspect
   list, never escalates association into
   participation, never identifies anyone, and
   never claims journalistic, moral, or legal
   authority. It structures provenance and claims
   and keeps uncertainty visible - nothing more.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DocumentClass(str, Enum):
    """Closed set of document classes."""
    COURT_DOCUMENTS = "court_documents"
    FLIGHT_LOGS = "flight_logs"
    WITNESS_STATEMENTS = "witness_statements"
    MEDIA_REPORTS = "media_reports"
    LEAKED_MATERIAL = "leaked_material"
    SECONDARY_COMMENTARY = "secondary_commentary"
    DUPLICATED_DOCUMENTS = "duplicated_documents"
    UNKNOWN_PROVENANCE = "unknown_provenance"


DOCUMENT_CLASSES: tuple[str, ...] = tuple(
    d.value for d in DocumentClass
)


class ProvenanceGrade(str, Enum):
    """Closed provenance-quality ladder."""
    CHAIN_OF_CUSTODY = "chain_of_custody"
    ATTRIBUTED = "attributed"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


PROVENANCE_GRADES: tuple[str, ...] = tuple(
    p.value for p in ProvenanceGrade
)

_GRADE_VALUE: dict[str, float] = {
    ProvenanceGrade.CHAIN_OF_CUSTODY.value: 1.0,
    ProvenanceGrade.ATTRIBUTED.value: 0.66,
    ProvenanceGrade.PARTIAL.value: 0.33,
    ProvenanceGrade.UNKNOWN.value: 0.0,
}


def grade_value(grade: str) -> float:
    return _GRADE_VALUE[grade]


# Abstract, synthetic entity placeholders. They do
# NOT correspond to any real person. They exist only
# to demonstrate that mention/association never
# escalates to involvement.
ENTITIES: tuple[str, ...] = (
    "ENTITY_A", "ENTITY_B", "ENTITY_C",
    "ENTITY_D", "ENTITY_E", "ENTITY_F",
)


@dataclass(frozen=True)
class Document:
    doc_id: str
    doc_class: str
    provenance_grade: str
    # which source line produced it (for independence)
    source_id: str
    # synthetic fingerprint for duplicate detection
    content_fingerprint: str
    # abstract entity placeholders the document
    # MENTIONS (mention != involvement)
    entities_referenced: tuple[str, ...]
    is_synthetic_placeholder: bool = True

    def provenance_value(self) -> float:
        return grade_value(self.provenance_grade)

    def to_dict(self) -> dict[str, object]:
        return {
            "doc_id": self.doc_id,
            "doc_class": self.doc_class,
            "provenance_grade": self.provenance_grade,
            "source_id": self.source_id,
            "content_fingerprint":
                self.content_fingerprint,
            "entities_referenced":
                list(self.entities_referenced),
            "provenance_value":
                round(self.provenance_value(), 4),
            "is_synthetic_placeholder":
                self.is_synthetic_placeholder,
        }


def _D(
    doc_id: str, dc: DocumentClass,
    pg: ProvenanceGrade, source_id: str,
    fp: str, *entities: str,
) -> Document:
    return Document(
        doc_id=doc_id, doc_class=dc.value,
        provenance_grade=pg.value, source_id=source_id,
        content_fingerprint=fp,
        entities_referenced=tuple(entities),
    )


# Synthetic corpus: a contaminated mix of strong-
# provenance court/witness records and weak-
# provenance leaked/secondary/unknown material, with
# planted duplicates. No real content.
_DOCUMENTS: tuple[Document, ...] = (
    _D("D01", DocumentClass.COURT_DOCUMENTS,
       ProvenanceGrade.CHAIN_OF_CUSTODY, "court",
       "FP100", "ENTITY_A", "ENTITY_B"),
    _D("D02", DocumentClass.COURT_DOCUMENTS,
       ProvenanceGrade.CHAIN_OF_CUSTODY, "court",
       "FP101", "ENTITY_A"),
    _D("D03", DocumentClass.WITNESS_STATEMENTS,
       ProvenanceGrade.ATTRIBUTED, "witness_1",
       "FP102", "ENTITY_B", "ENTITY_C"),
    _D("D04", DocumentClass.FLIGHT_LOGS,
       ProvenanceGrade.ATTRIBUTED, "registry",
       "FP103", "ENTITY_C", "ENTITY_D", "ENTITY_E"),
    _D("D05", DocumentClass.FLIGHT_LOGS,
       ProvenanceGrade.PARTIAL, "registry",
       "FP104", "ENTITY_E"),
    _D("D06", DocumentClass.MEDIA_REPORTS,
       ProvenanceGrade.PARTIAL, "media_outlet_1",
       "FP105", "ENTITY_A", "ENTITY_F"),
    _D("D07", DocumentClass.MEDIA_REPORTS,
       ProvenanceGrade.PARTIAL, "media_outlet_2",
       "FP106", "ENTITY_F"),
    _D("D08", DocumentClass.SECONDARY_COMMENTARY,
       ProvenanceGrade.UNKNOWN, "blog_aggregator",
       "FP107", "ENTITY_A", "ENTITY_C", "ENTITY_F"),
    _D("D09", DocumentClass.LEAKED_MATERIAL,
       ProvenanceGrade.UNKNOWN, "anon_leak",
       "FP108", "ENTITY_D"),
    _D("D10", DocumentClass.UNKNOWN_PROVENANCE,
       ProvenanceGrade.UNKNOWN, "unknown",
       "FP109", "ENTITY_F"),
    # planted duplicates (same fingerprint as an
    # earlier document) - re-circulated material.
    _D("D11", DocumentClass.DUPLICATED_DOCUMENTS,
       ProvenanceGrade.UNKNOWN, "repost_1",
       "FP105", "ENTITY_A", "ENTITY_F"),
    _D("D12", DocumentClass.DUPLICATED_DOCUMENTS,
       ProvenanceGrade.UNKNOWN, "repost_2",
       "FP107", "ENTITY_A", "ENTITY_C", "ENTITY_F"),
    _D("D13", DocumentClass.WITNESS_STATEMENTS,
       ProvenanceGrade.ATTRIBUTED, "witness_2",
       "FP110", "ENTITY_B"),
    _D("D14", DocumentClass.COURT_DOCUMENTS,
       ProvenanceGrade.CHAIN_OF_CUSTODY, "court",
       "FP111", "ENTITY_D"),
)


def documents() -> tuple[Document, ...]:
    return _DOCUMENTS


def by_id(doc_id: str) -> Document:
    for d in _DOCUMENTS:
        if d.doc_id == doc_id:
            return d
    raise KeyError(doc_id)


def doc_ids() -> tuple[str, ...]:
    return tuple(d.doc_id for d in _DOCUMENTS)


def sources() -> tuple[str, ...]:
    seen: list[str] = []
    for d in _DOCUMENTS:
        if d.source_id not in seen:
            seen.append(d.source_id)
    return tuple(seen)


__all__ = [
    "DOCUMENT_CLASSES",
    "ENTITIES",
    "PROVENANCE_GRADES",
    "Document",
    "DocumentClass",
    "ProvenanceGrade",
    "by_id",
    "doc_ids",
    "documents",
    "grade_value",
    "sources",
]
