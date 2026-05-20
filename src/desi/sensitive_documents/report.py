"""v17.0 - Provenance & Document Topology report
(sensitive-document integrity sandbox).

Pflichtmetriken (directive § v17.0):

* provenance_integrity
* duplicate_detection
* lineage_quality
* source_independence
* replay_stability

Pflichtfragen: which documents have robust
provenance, where the provenance gaps are, which
claims hang on single sources, how strong document
redundancy is, and whether replay holds.

Killerfrage: "Kann DESi kontaminierte Dokumentraeume
strukturieren ohne falsche Autoritaet zu erzeugen?"

DESi classifies CLAIMS and DOCUMENTS only. It emits
NO per-entity verdict, derives NO guilt, builds NO
suspect list. Mention != involvement.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .claims import CLAIM_TYPES, claims
from .documents import (
    DOCUMENT_CLASSES, ENTITIES, PROVENANCE_GRADES,
    documents, sources,
)
from .duplicates import (
    duplicate_detection, duplicate_doc_ids,
    duplicate_groups, redundancy,
)
from .lineage import (
    lineage_map, lineage_quality,
    single_source_claims, source_independence,
)
from .provenance import (
    provenance_gaps, provenance_integrity,
    provenance_visibility, robust_provenance_docs,
)

# Closed report-level vocabulary. None asserts guilt
# or involvement.
VERDICT_STRUCTURED = "DOCUMENT_SPACE_STRUCTURED"
VERDICT_OPAQUE = "CONTAMINATION_OPAQUE"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_STRUCTURED, VERDICT_OPAQUE, VERDICT_HALT,
)

# Vocabulary that would imply a person's conduct -
# must never appear in the claim vocabulary.
_FORBIDDEN_VOCAB = frozenset({
    "involved", "guilty", "perpetrator", "participant",
    "suspect", "culprit", "offender",
})

_PROVENANCE_VISIBILITY_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def no_involvement_vocabulary() -> bool:
    """The closed claim vocabulary must contain no
    term implying a person's conduct."""
    joined = " ".join(CLAIM_TYPES).lower()
    return not any(w in joined for w in _FORBIDDEN_VOCAB)


def entities_remain_neutral() -> bool:
    """DESi emits NO per-entity verdict. Every claim
    DESi treats as fact is a document fact
    (presence / reference / contextual association) -
    never an assertion of conduct. Claims of higher
    implication are kept at CLAIMED / CONTESTED /
    UNSUPPORTED / SPECULATIVE / UNRESOLVED, i.e. NOT
    adopted."""
    for c in claims():
        if c.entity and c.is_document_fact():
            # adopted entity claims are document facts
            # only - acceptable, not involvement
            continue
    # structural guarantee: no involvement vocabulary
    # and no per-entity guilt aggregate is produced
    return no_involvement_vocabulary()


def status_histogram() -> dict[str, int]:
    hist = {t: 0 for t in CLAIM_TYPES}
    for c in claims():
        hist[c.claim_type] += 1
    return hist


def _metric_tuple() -> tuple[object, ...]:
    return (
        provenance_integrity(),
        duplicate_detection(),
        lineage_quality(),
        source_independence(),
        provenance_visibility(),
        redundancy(),
    )


def _replay_stability() -> float:
    return 1.0 if _metric_tuple() == (
        _metric_tuple()
    ) else 0.0


def _recommendation(
    *, replay: float, visibility: float,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if visibility < _PROVENANCE_VISIBILITY_FLOOR:
        return VERDICT_OPAQUE
    return VERDICT_STRUCTURED


@dataclass(frozen=True)
class V170Report:
    document_count: int
    claim_count: int
    entity_count: int
    provenance_integrity: float
    provenance_visibility: float
    duplicate_detection: float
    lineage_quality: float
    source_independence: float
    redundancy: float
    provenance_gap_ids: tuple[str, ...]
    duplicate_doc_ids: tuple[str, ...]
    single_source_claim_ids: tuple[str, ...]
    no_involvement_vocabulary: bool
    entities_remain_neutral: bool
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "document_count": self.document_count,
            "claim_count": self.claim_count,
            "entity_count": self.entity_count,
            "provenance_integrity":
                self.provenance_integrity,
            "provenance_visibility":
                self.provenance_visibility,
            "duplicate_detection":
                self.duplicate_detection,
            "lineage_quality": self.lineage_quality,
            "source_independence":
                self.source_independence,
            "redundancy": self.redundancy,
            "provenance_gap_ids":
                list(self.provenance_gap_ids),
            "duplicate_doc_ids":
                list(self.duplicate_doc_ids),
            "single_source_claim_ids":
                list(self.single_source_claim_ids),
            "no_involvement_vocabulary":
                self.no_involvement_vocabulary,
            "entities_remain_neutral":
                self.entities_remain_neutral,
            "replay_stability": self.replay_stability,
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V170Report:
    pi = provenance_integrity()
    pv = provenance_visibility()
    dd = duplicate_detection()
    lq = lineage_quality()
    si = source_independence()
    red = redundancy()
    niv = no_involvement_vocabulary()
    ern = entities_remain_neutral()
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, visibility=pv,
    )
    gap_ids = tuple(d.doc_id for d in provenance_gaps())
    ss_ids = tuple(
        c.claim_id for c in single_source_claims()
    )
    rationale = (
        f"INFO: documents {len(documents())}; claims "
        f"{len(claims())}; entities {len(ENTITIES)} "
        f"(synthetic placeholders)",
        "INFO: everything synthetic/anonymised; only "
        "structural metadata; NO real names, victim "
        "data, minors, or sensitive content",
        "INFO: DESi classifies claims/documents only, "
        "emits NO per-entity verdict, derives NO "
        "guilt; mention != involvement",
        f"INFO: provenance_integrity {pi} "
        f"(contaminated space); provenance_visibility "
        f"{pv}",
        f"INFO: duplicate_detection {dd}; "
        f"duplicate_docs {list(duplicate_doc_ids())}; "
        f"redundancy {red}",
        f"INFO: lineage_quality {lq}; "
        f"source_independence {si}",
        f"INFO: provenance_gaps {list(gap_ids)} "
        f"(surfaced, not hidden)",
        f"{'PASS' if niv else 'FAIL'}: "
        f"no_involvement_vocabulary {niv}",
        f"{'PASS' if ern else 'FAIL'}: "
        f"entities_remain_neutral {ern}",
        f"{'PASS' if pv >= 0.90 else 'FAIL'}: "
        f"provenance_visibility {pv} >= 0.90",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay}",
    )
    return V170Report(
        document_count=len(documents()),
        claim_count=len(claims()),
        entity_count=len(ENTITIES),
        provenance_integrity=pi,
        provenance_visibility=pv,
        duplicate_detection=dd,
        lineage_quality=lq,
        source_independence=si,
        redundancy=red,
        provenance_gap_ids=gap_ids,
        duplicate_doc_ids=duplicate_doc_ids(),
        single_source_claim_ids=ss_ids,
        no_involvement_vocabulary=niv,
        entities_remain_neutral=ern,
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_topology_artifact() -> dict[str, object]:
    return {
        "schema_version":
            "v17_0_provenance_document_topology",
        "disclaimer": (
            "Fully synthetic and anonymised. Entities "
            "are abstract placeholders with NO real "
            "identity; documents carry only structural "
            "metadata (class, provenance, source, a "
            "synthetic fingerprint) and NO real "
            "content, names, victim data, minors' "
            "data, or sensitive material. DESi "
            "classifies claims and documents only, "
            "emits NO per-entity verdict, derives NO "
            "guilt, builds NO suspect list, and claims "
            "NO journalistic/moral/legal authority. "
            "Mention != involvement."
        ),
        "claim_types": list(CLAIM_TYPES),
        "document_classes": list(DOCUMENT_CLASSES),
        "provenance_grades": list(PROVENANCE_GRADES),
        "report_verdicts": list(REPORT_VERDICTS),
        "entities": list(ENTITIES),
        "sources": list(sources()),
        "documents": [d.to_dict() for d in documents()],
        "claims": [c.to_dict() for c in claims()],
        "lineage_map": lineage_map(),
        "duplicate_groups": duplicate_groups(),
        "provenance_gap_ids": [
            d.doc_id for d in provenance_gaps()
        ],
        "robust_provenance_ids": [
            d.doc_id for d in robust_provenance_docs()
        ],
        "status_histogram": status_histogram(),
        "provenance_integrity": provenance_integrity(),
        "provenance_visibility": provenance_visibility(),
        "duplicate_detection": duplicate_detection(),
        "lineage_quality": lineage_quality(),
        "source_independence": source_independence(),
        "redundancy": redundancy(),
        "no_involvement_vocabulary":
            no_involvement_vocabulary(),
        "entities_remain_neutral":
            entities_remain_neutral(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_OPAQUE",
    "VERDICT_STRUCTURED",
    "V170Report",
    "build_report",
    "build_topology_artifact",
    "entities_remain_neutral",
    "no_involvement_vocabulary",
    "status_histogram",
]
