"""v22.2 - Scientific Rendering Layer report.

Pflichtmetriken (directive § v22.2):

* scientific_style_integrity
* claim_conservatism
* uncertainty_visibility
* sandbox_honesty
* replay_stability

Killerfrage: "Kann DESi paperaehnliche Kommunikation
erzeugen ohne in AGI-Hype zu kippen?"

DESi assembles a short, sober, scoped paper-like document
from the v19-v21 results. No forbidden term, no hype, claims
scoped to the synthetic sandbox.
"""
from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass

from desi.scientific_rendering import forbidden_hits

from .abstract import abstract_is_conservative
from .limitations import (
    hedge_count, sandbox_honesty, uncertainty_visibility,
)
from .structure import (
    SECTION_ORDER, all_sections_present, full_document,
)
from .style_governance import (
    claim_conservatism, hype_free, scientific_style_integrity,
)

VERDICT_RENDERED = "PAPER_RENDERED"
VERDICT_HYPED = "RENDERING_HYPED"
VERDICT_HALT = "REPLAY_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_RENDERED, VERDICT_HYPED, VERDICT_HALT,
)

_STYLE_FLOOR = 0.90
_CONSERVATISM_FLOOR = 0.90
_UNCERTAINTY_FLOOR = 0.90


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def document_forbidden_hits() -> tuple[str, ...]:
    return forbidden_hits(full_document())


def document_signature() -> str:
    return hashlib.sha256(
        full_document().encode("utf-8"),
    ).hexdigest()


def _metric_tuple() -> tuple[object, ...]:
    return (
        scientific_style_integrity(), claim_conservatism(),
        uncertainty_visibility(), document_signature(),
    )


def _replay_stability() -> float:
    return 1.0 if _metric_tuple() == _metric_tuple() else 0.0


def _recommendation(
    *, replay: float, style: float, cons: float, unc: float,
    forbidden_clean: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        not forbidden_clean
        or style < _STYLE_FLOOR
        or cons < _CONSERVATISM_FLOOR
        or unc < _UNCERTAINTY_FLOOR
    ):
        return VERDICT_HYPED
    return VERDICT_RENDERED


@dataclass(frozen=True)
class V222Report:
    section_count: int
    scientific_style_integrity: float
    claim_conservatism: float
    uncertainty_visibility: float
    sandbox_honesty: bool
    abstract_is_conservative: bool
    hype_free: bool
    all_sections_present: bool
    document_forbidden_hits: tuple[str, ...]
    hedge_count: int
    document_signature: str
    replay_stability: float
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "section_count": self.section_count,
            "scientific_style_integrity":
                self.scientific_style_integrity,
            "claim_conservatism": self.claim_conservatism,
            "uncertainty_visibility": self.uncertainty_visibility,
            "sandbox_honesty": self.sandbox_honesty,
            "abstract_is_conservative":
                self.abstract_is_conservative,
            "hype_free": self.hype_free,
            "all_sections_present": self.all_sections_present,
            "document_forbidden_hits":
                list(self.document_forbidden_hits),
            "hedge_count": self.hedge_count,
            "document_signature": self.document_signature,
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


def build_report() -> V222Report:
    style = scientific_style_integrity()
    cons = claim_conservatism()
    unc = uncertainty_visibility()
    sh = sandbox_honesty()
    hits = document_forbidden_hits()
    clean = not hits
    replay = _replay_stability()
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, style=style, cons=cons, unc=unc,
        forbidden_clean=clean,
    )
    rationale = (
        f"INFO: sections {list(SECTION_ORDER)}",
        "INFO: DESi assembles a short, sober, sandbox-scoped "
        "document; no forbidden term, no hype, no unscoped "
        "universal claim",
        f"{'PASS' if clean else 'FAIL'}: document_forbidden_"
        f"hits {list(hits)} (must be empty)",
        f"{'PASS' if style >= 0.90 else 'FAIL'}: "
        f"scientific_style_integrity {style} >= 0.90",
        f"{'PASS' if cons >= 0.90 else 'FAIL'}: "
        f"claim_conservatism {cons} >= 0.90",
        f"{'PASS' if unc >= 0.90 else 'FAIL'}: "
        f"uncertainty_visibility {unc} >= 0.90 "
        f"(hedges {hedge_count()})",
        f"{'PASS' if sh else 'FAIL'}: sandbox_honesty {sh}; "
        f"abstract_is_conservative {abstract_is_conservative()}",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (doc_signature "
        f"{document_signature()[:12]})",
    )
    return V222Report(
        section_count=len(SECTION_ORDER),
        scientific_style_integrity=style,
        claim_conservatism=cons,
        uncertainty_visibility=unc,
        sandbox_honesty=sh,
        abstract_is_conservative=abstract_is_conservative(),
        hype_free=hype_free(),
        all_sections_present=all_sections_present(),
        document_forbidden_hits=hits,
        hedge_count=hedge_count(),
        document_signature=document_signature(),
        replay_stability=replay,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_rendering_artifact() -> dict[str, object]:
    from .structure import sections
    return {
        "schema_version": "v22_2_scientific_rendering_layer",
        "disclaimer": (
            "DESi assembles a short, sober, sandbox-scoped "
            "paper-like document from the v19-v21 results. It "
            "contains no forbidden term, no hype, and no "
            "unscoped universal claim; every claim is scoped to "
            "the synthetic sandbox. DESi makes no global "
            "intelligence claim and claims no truth authority. "
            "Replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "section_order": list(SECTION_ORDER),
        "sections": sections(),
        "scientific_style_integrity":
            scientific_style_integrity(),
        "claim_conservatism": claim_conservatism(),
        "uncertainty_visibility": uncertainty_visibility(),
        "sandbox_honesty": sandbox_honesty(),
        "abstract_is_conservative": abstract_is_conservative(),
        "hype_free": hype_free(),
        "all_sections_present": all_sections_present(),
        "document_forbidden_hits":
            list(document_forbidden_hits()),
        "hedge_count": hedge_count(),
        "document_signature": document_signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_HYPED",
    "VERDICT_RENDERED",
    "V222Report",
    "build_rendering_artifact",
    "build_report",
    "document_forbidden_hits",
    "document_signature",
]
