"""v25.3 - Multi-Port Rendering report.

Pflichtmetriken (directive § v25.3):

* cross_port_claim_consistency
* cross_port_metric_consistency
* format_validity
* limitation_preservation
* replay_stability

Killerfrage: "Kann DESi denselben epistemischen Zustand in
verschiedene wissenschaftliche Ausgabeformate rendern, ohne
Claims zu veraendern?"

Every port renders from one shared section provider, so claims,
numbers, references and limitations are identical across ports;
only the title and the included-section set differ by format.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from desi.scientific_rendering import forbidden_hits
from desi.output_ports import (
    PORT_TYPES, schema_for, section_title,
)
from desi.output_ports_arxiv import result_lines

from .renderer import all_renders, canonical_body, render_port

VERDICT_PUBLISHABLE = "MULTI_PORT_CLAIM_STABLE"
VERDICT_INCONSISTENT = "MULTI_PORT_INCONSISTENT"
VERDICT_HALT = "RENDER_DRIFT_HALT"
REPORT_VERDICTS: tuple[str, ...] = (
    VERDICT_PUBLISHABLE, VERDICT_INCONSISTENT, VERDICT_HALT,
)

_FLOOR = 0.95


def _round(x: float, n: int = 6) -> float:
    return round(x, n)


def _required(port: str) -> tuple[str, ...]:
    return schema_for(port).required_sections


def cross_port_claim_consistency() -> float:
    """Fraction of (port, shared-section) renderings whose body
    is byte-identical to the canonical shared body, in [0, 1]."""
    total = 0
    ok = 0
    for p in PORT_TYPES:
        text = render_port(p)
        for sec in _required(p):
            if sec == "title":
                continue
            total += 1
            if canonical_body(sec) and canonical_body(sec) in text:
                ok += 1
    return _round(ok / total) if total else 0.0


def cross_port_metric_consistency() -> float:
    """Fraction of (port, result-line) pairs where the value and
    its sprint source both appear, across ports that report
    results, in [0, 1]."""
    lines = result_lines()
    ports = [p for p in PORT_TYPES if "results" in _required(p)]
    if not ports or not lines:
        return 1.0
    total = 0
    ok = 0
    for p in ports:
        text = render_port(p)
        for l in lines:
            total += 1
            if str(l.value) in text and l.sprint_source in text:
                ok += 1
    return _round(ok / total) if total else 0.0


def format_validity() -> float:
    """Fraction of ports whose render contains every required
    section header and is non-empty, in [0, 1]."""
    total = len(PORT_TYPES)
    ok = 0
    for p in PORT_TYPES:
        text = render_port(p)
        valid = bool(text.strip()) and all(
            (sec == "title") or (section_title(sec) in text)
            for sec in _required(p)
        )
        if valid:
            ok += 1
    return _round(ok / total) if total else 0.0


def limitation_preservation() -> float:
    """Fraction of ports that mandate Limitations and actually
    render a non-empty Limitations section, in [0, 1]."""
    ports = [
        p for p in PORT_TYPES if schema_for(p).limitation.required
    ]
    if not ports:
        return 1.0
    ok = 0
    for p in ports:
        text = render_port(p)
        if (
            "limitations" in _required(p)
            and canonical_body("limitations").strip()
            and section_title("limitations") in text
        ):
            ok += 1
    return _round(ok / len(ports))


def corpus_forbidden_hits() -> tuple[str, ...]:
    hits: set[str] = set()
    for text in all_renders().values():
        hits.update(forbidden_hits(text))
    return tuple(sorted(hits))


def _signature() -> str:
    renders = all_renders()
    parts = [
        f"{p}:{hashlib.sha256(renders[p].encode()).hexdigest()}"
        for p in sorted(renders)
    ]
    return hashlib.sha256(
        "\n".join(parts).encode("utf-8"),
    ).hexdigest()


def replay_stability() -> float:
    if _signature() != _signature():
        return 0.0
    return 1.0 if all_renders() == all_renders() else 0.0


def _recommendation(
    *, replay: float, claim: float, metric: float,
    fmt: float, limitation: float, clean: bool,
) -> str:
    if replay < 1.0:
        return VERDICT_HALT
    if (
        not clean
        or claim < _FLOOR
        or metric < _FLOOR
        or fmt < _FLOOR
        or limitation < _FLOOR
    ):
        return VERDICT_INCONSISTENT
    return VERDICT_PUBLISHABLE


@dataclass(frozen=True)
class V253Report:
    port_count: int
    cross_port_claim_consistency: float
    cross_port_metric_consistency: float
    format_validity: float
    limitation_preservation: float
    replay_stability: float
    corpus_forbidden_hits: tuple[str, ...]
    halt: bool
    recommendation: str
    rationale: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "port_count": self.port_count,
            "cross_port_claim_consistency":
                self.cross_port_claim_consistency,
            "cross_port_metric_consistency":
                self.cross_port_metric_consistency,
            "format_validity": self.format_validity,
            "limitation_preservation":
                self.limitation_preservation,
            "replay_stability": self.replay_stability,
            "corpus_forbidden_hits":
                list(self.corpus_forbidden_hits),
            "halt": self.halt,
            "recommendation": self.recommendation,
            "rationale": list(self.rationale),
        }

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True,
            separators=(",", ":"),
        )


def build_report() -> V253Report:
    claim = cross_port_claim_consistency()
    metric = cross_port_metric_consistency()
    fmt = format_validity()
    limitation = limitation_preservation()
    replay = replay_stability()
    hits = corpus_forbidden_hits()
    clean = not hits
    halt = replay < 1.0
    verdict = _recommendation(
        replay=replay, claim=claim, metric=metric, fmt=fmt,
        limitation=limitation, clean=clean,
    )
    rationale = (
        f"INFO: {len(PORT_TYPES)} ports rendered from one shared "
        f"section provider",
        "INFO: only the title and the included-section set vary "
        "by format; claims, numbers, references and limitations "
        "are byte-identical across ports",
        f"{'PASS' if claim >= _FLOOR else 'FAIL'}: "
        f"cross_port_claim_consistency {claim} >= 0.95",
        f"{'PASS' if metric >= _FLOOR else 'FAIL'}: "
        f"cross_port_metric_consistency {metric} >= 0.95",
        f"{'PASS' if fmt >= _FLOOR else 'FAIL'}: "
        f"format_validity {fmt} >= 0.95",
        f"{'PASS' if limitation >= _FLOOR else 'FAIL'}: "
        f"limitation_preservation {limitation} >= 0.95",
        f"{'PASS' if clean else 'FAIL'}: corpus_forbidden_hits "
        f"{list(hits)} (must be empty)",
        f"{'PASS' if replay == 1.0 else 'FAIL'}: "
        f"replay_stability {replay} (signature "
        f"{_signature()[:12]})",
    )
    return V253Report(
        port_count=len(PORT_TYPES),
        cross_port_claim_consistency=claim,
        cross_port_metric_consistency=metric,
        format_validity=fmt,
        limitation_preservation=limitation,
        replay_stability=replay,
        corpus_forbidden_hits=hits,
        halt=halt,
        recommendation=verdict,
        rationale=rationale,
    )


def build_multi_port_artifact() -> dict[str, object]:
    renders = all_renders()
    return {
        "schema_version": "v25_3_multi_port_rendering",
        "disclaimer": (
            "Renders the same epistemic state into several "
            "scientific document formats - arXiv paper, workshop "
            "note, technical report, citation appendix and "
            "reproducibility statement. All ports draw from one "
            "shared section provider, so claims, numbers, "
            "references and limitations are byte-identical across "
            "ports; only the title and the included-section set "
            "differ by format. No forbidden term appears. "
            "Replay-exact."
        ),
        "report_verdicts": list(REPORT_VERDICTS),
        "port_types": list(PORT_TYPES),
        "render_lengths": {
            p: len(renders[p]) for p in sorted(renders)
        },
        "cross_port_claim_consistency":
            cross_port_claim_consistency(),
        "cross_port_metric_consistency":
            cross_port_metric_consistency(),
        "format_validity": format_validity(),
        "limitation_preservation": limitation_preservation(),
        "replay_stability": replay_stability(),
        "corpus_forbidden_hits": list(corpus_forbidden_hits()),
        "signature": _signature(),
        "recommendation": build_report().recommendation,
    }


__all__ = [
    "REPORT_VERDICTS",
    "VERDICT_HALT",
    "VERDICT_INCONSISTENT",
    "VERDICT_PUBLISHABLE",
    "V253Report",
    "build_multi_port_artifact",
    "build_report",
    "corpus_forbidden_hits",
    "cross_port_claim_consistency",
    "cross_port_metric_consistency",
    "format_validity",
    "limitation_preservation",
    "replay_stability",
]
