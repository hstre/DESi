"""Artifact writers — claims.jsonl, evidence.jsonl, contradictions.md, comparison.md.

Deterministic: given the closed fixture, the bytes are stable (no timestamps or
hostnames in the committed artifacts). The narrative ``REPORT.md`` is hand-authored
and committed alongside; it references what this module regenerates.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import analysis, claims as C


def write_claims_jsonl(path: Path) -> int:
    lines = [json.dumps(c.to_dict(), ensure_ascii=False, sort_keys=True) for c in C.CLAIMS]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def write_evidence_jsonl(path: Path) -> int:
    lines = [json.dumps(e.to_dict(), ensure_ascii=False, sort_keys=True) for e in C.EVIDENCE]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def summary() -> dict:
    return {
        "run_id": analysis.RUN_ID,
        "claims_total": len(C.CLAIMS),
        "verdict_distribution": analysis.verdict_distribution(),
        "evidence_strength_distribution": analysis.evidence_strength_distribution(),
        "structural_contradictions": [nc.cid for nc in analysis.detect_contradictions()],
        "graph": analysis.graph_summary(),
        "source_gate_admissible": sum(1 for g in analysis.source_gate_findings() if g.admissible),
        "source_gate_total": len(analysis.source_gate_findings()),
        "omission": analysis.omission_analysis(),
        "self_sealing": analysis.self_sealing_analysis().to_dict(),
    }


def write_summary_json(path: Path) -> None:
    path.write_text(json.dumps(summary(), ensure_ascii=False, indent=2, sort_keys=True)
                    + "\n", encoding="utf-8")


def render_contradictions_md() -> str:
    cons = analysis.detect_contradictions()
    ss = analysis.self_sealing_analysis()
    out: list[str] = []
    out.append("# Strukturelle Konflikte — MarCognity / Muse Spark 1.1\n")
    out.append("*Auto-generiert von `python -m desi.case_studies.marcognity_muse_spark`. "
               "DESis Detektor `desi.self_audit.contradictions.find_contradictions` findet "
               "diese als Schlüssel/Wert-Inkonsistenzen — nicht von Prosa behauptet. "
               "Nicht jeder ist ein logischer Widerspruch: die Spalte „Art“ hält die "
               "unterschiedliche Stärke fest (Widerspruch / Pipeline-Inkonsistenz / "
               "unbelegte Unabhängigkeit).*\n")
    for nc in cons:
        con = nc.contradiction
        out.append(f"## {nc.cid} — {nc.title}\n")
        out.append(f"- **Art:** {nc.kind}")
        out.append(f"- **Scope (Detektor):** `{con.scope}`")
        out.append(f"- **Konfligierende Werte:** {', '.join(repr(v) for v in con.values)}")
        out.append(f"- **Claim-IDs (Detektor):** {', '.join(con.claim_ids)}")
        out.append(f"\n{nc.explanation}\n")
    out.append("## Selbstabdichtung (Aufgabe 7)\n")
    out.append(f"**Self-sealing:** {ss.is_self_sealing} — {ss.reason}\n")
    out.append("**Was würde die Hypothese stützen?**")
    for x in ss.would_support:
        out.append(f"- {x}")
    out.append("\n**Was würde sie schwächen?**")
    for x in ss.would_weaken:
        out.append(f"- {x}")
    out.append("\n**Was würde sie widerlegen?**")
    for x in ss.would_refute:
        out.append(f"- {x}")
    out.append(f"\n**Falsifikationsbedingungen im Originalversuch angegeben?** "
               f"{'ja' if ss.falsifiers_stated_in_experiment else 'nein'}.\n")
    return "\n".join(out)


# The comparison dimensions (Aufgabe 8), each: (dimension, MarCognity, DESi).
_COMPARISON_ROWS: tuple[tuple[str, str, str], ...] = (
    ("Claim-Abdeckung",
     "5 sehr allgemeine Definitions-Claims geprüft; Zitate, Attributionen, "
     "Formeln, empirische & normative Aussagen ausgelassen.",
     "23 kuratierte, typisierte Claims (inkl. zuvor übersehener Claim-Klassen) — "
     "eine kuratierte Auswahl, KEINE gemessene Vollständigkeit des Muse-Textes."),
    ("Quellenpassung (Source-Gating)",
     "Keine. Rechtsphilosophie gegen 'das PubMed-Dokument' geprüft "
     "(code: kein Domain-Gate).",
     "`source_domain_gate`: biomedizinische Quelle ist für Rechtsphilosophie "
     "nicht zulässig → SOURCE_DOMAIN_MISMATCH, nicht 'VERIFIED'."),
    ("Konkrete Provenienz",
     "'das PubMed-Dokument' — kein Titel, keine Passage.",
     "Jede Bewertung zeigt exakten Anker (doc:Zeile + Wortlaut); fehlt eine "
     "Passage, wird `provenance_kind=none` protokolliert, nicht kaschiert."),
    ("Widerspruchserkennung",
     "Übersieht den Prompt/Methode-Widerspruch; produziert selbst den "
     "'alle VERIFIED' ↔ 'keine Zitate' Widerspruch.",
     "3 strukturelle Widersprüche über `find_contradictions` (C1 Prompt↔Methode, "
     "C2 verifiziert↔keine Zitate, C3 'unabhängig'↔ein LLM-Call)."),
    ("Umgang mit Interpretationen/Heuristiken",
     "Binär VERIFIED/EPISTEMIC FAILURE; Formeln würden fälschlich "
     "verifizierbar/scheitern.",
     "Eigene Verdikte `heuristic_proposal`, `interpretation`, `normative_claim`: "
     "die Formeln sind heuristische Eigenkonstruktionen, weder wahr noch falsch."),
    ("Unsicherheitsdarstellung",
     "Autoritativer VERIFIED-Stempel; Unsicherheit nur global im Fließtext.",
     "Pro Claim `verdict` + `uncertainty` + `evidence_strength`; "
     "`unverifiable_from_available_evidence` ist ein erstklassiges Urteil."),
    ("Falsifizierbarkeit",
     "Keine Falsifikationsbedingung; Erfolg UND Versagen bestätigen die Theorie.",
     "`self_sealing_analysis` benennt would_support/weaken/refute und stellt "
     "fest, dass keine Falsifikationsbedingung angegeben ist."),
    ("Auditierbarkeit",
     "Ein konkatenierter Freitext-Report; zwei Subsysteme ohne Abgleich.",
     "claims.jsonl + evidence.jsonl (je Zeile auditierbar) + optionaler "
     "hash-verketteter Layer-9-Ledger (`desi_router.ledger`)."),
    ("Evaluator-Selbstprüfung",
     "Der Skeptical Agent prüft den Text, aber nicht sich selbst; sein "
     "Domainfehler wird als Theoriebestätigung umgedeutet.",
     "Der MarCognity-Report ist hier selbst Prüfobjekt (VAL-01..03); DESis "
     "eigene Grenzen werden im Report offen benannt."),
)


def render_comparison_md() -> str:
    out: list[str] = []
    out.append("# Vergleich — MarCognity-Validierung vs. DESi-Analyse\n")
    out.append("*Auto-generiert. Kein Werbetext: DESi verhindert Fehler nicht, es macht "
               "die Stelle sichtbar, an der ein Fehler, eine Auslassung oder ein "
               "unzulässiger Schluss entsteht.*\n")
    out.append("| Dimension | MarCognity (Skeptical Agent) | DESi |")
    out.append("|---|---|---|")
    for dim, marc, desi in _COMPARISON_ROWS:
        out.append(f"| **{dim}** | {marc} | {desi} |")
    out.append("")
    return "\n".join(out)


def write_all(out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    n_claims = write_claims_jsonl(out_dir / "claims.jsonl")
    n_ev = write_evidence_jsonl(out_dir / "evidence.jsonl")
    (out_dir / "contradictions.md").write_text(render_contradictions_md(), encoding="utf-8")
    (out_dir / "comparison.md").write_text(render_comparison_md(), encoding="utf-8")
    write_summary_json(out_dir / "summary.json")
    return {"claims": n_claims, "evidence": n_ev, "out_dir": str(out_dir)}


__all__ = [
    "write_claims_jsonl", "write_evidence_jsonl", "summary", "write_summary_json",
    "render_contradictions_md", "render_comparison_md", "write_all",
]
