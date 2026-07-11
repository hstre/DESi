"""Render the MarCognity / Muse Spark 1.1 case-study findings (with data) to a PDF.

Reads the committed artifacts (summary.json, claims.jsonl, evidence.jsonl) produced
by ``python -m desi.case_studies.marcognity_muse_spark`` so the PDF reflects exactly
the generated data. Writes ``marcognity_muse_spark_findings.pdf`` next to them.

Kept in ``scripts/`` (not inside the importable ``desi`` package) on purpose:
``reportlab`` is not a DESi dependency, and nothing in the package or the test
suite should import it. Run explicitly:

    python scripts/reproduce_marcognity_pdf.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

CS = (Path(__file__).resolve().parents[1]
      / "src/desi/case_studies/marcognity_muse_spark")
OUT = CS / "marcognity_muse_spark_findings.pdf"


def main() -> int:
    try:
        from reportlab.graphics.charts.barcharts import HorizontalBarChart
        from reportlab.graphics.shapes import Drawing, String
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            HRFlowable,
            KeepTogether,
            PageBreak,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError:
        print("reportlab is required: pip install reportlab", file=sys.stderr)
        return 2

    summary = json.loads((CS / "summary.json").read_text())
    claims = [json.loads(x) for x in (CS / "claims.jsonl").read_text().splitlines() if x]
    evidence = {json.loads(x)["claim_id"]: json.loads(x)
                for x in (CS / "evidence.jsonl").read_text().splitlines() if x}

    INK = colors.HexColor("#1a1a1a")
    MUTE = colors.HexColor("#5b6570")
    RULE = colors.HexColor("#d5dae0")
    BG_TILE = colors.HexColor("#f2f5f8")
    RED = colors.HexColor("#c0392b")
    AMBER = colors.HexColor("#d98a00")
    BLUE = colors.HexColor("#2c6fbb")
    GREEN = colors.HexColor("#2e8b57")
    SLATE = colors.HexColor("#5a6b82")
    TEAL = colors.HexColor("#1c8a8a")

    VERDICT_COLOR = {
        "contradicted": RED, "citation_mismatch": RED, "source_domain_mismatch": RED,
        "unsupported": RED, "unverifiable_from_available_evidence": AMBER,
        "interpretation": BLUE, "heuristic_proposal": SLATE, "normative_claim": SLATE,
        "partially_supported": TEAL, "supported": GREEN,
    }
    VERDICT_LABEL = {
        "contradicted": "contradicted", "citation_mismatch": "citation_mismatch",
        "source_domain_mismatch": "source_domain_mismatch", "unsupported": "unsupported",
        "unverifiable_from_available_evidence": "unverifiable",
        "interpretation": "interpretation", "heuristic_proposal": "heuristic_proposal",
        "normative_claim": "normative_claim", "supported": "supported",
    }

    styles = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=styles["Heading1"], textColor=INK, fontSize=17,
                        leading=21, spaceAfter=2, spaceBefore=8)
    H2 = ParagraphStyle("H2", parent=styles["Heading2"], textColor=INK, fontSize=12.5,
                        leading=16, spaceBefore=12, spaceAfter=4)
    BODY = ParagraphStyle("Body", parent=styles["BodyText"], textColor=INK, fontSize=9.3,
                          leading=13.2, alignment=TA_LEFT, spaceAfter=4)
    SMALL = ParagraphStyle("Small", parent=BODY, fontSize=8, leading=10.5, textColor=MUTE)
    TILE_N = ParagraphStyle("TileN", parent=BODY, fontSize=20, leading=22, textColor=INK,
                            alignment=1)
    TILE_L = ParagraphStyle("TileL", parent=BODY, fontSize=7.6, leading=9.5, textColor=MUTE,
                            alignment=1)
    CELL = ParagraphStyle("Cell", parent=BODY, fontSize=8, leading=10)

    def bar_chart(pairs, color_fn, width=170 * mm, row_h=13, title=""):
        data = [v for _, v in pairs]
        labels = [k for k, _ in pairs]
        n = len(pairs)
        h = row_h * n + 26
        d = Drawing(width, h)
        bc = HorizontalBarChart()
        bc.x, bc.y = 116, 8
        bc.height = row_h * n
        bc.width = width - 150
        bc.data = [data]
        bc.strokeColor = None
        bc.bars.strokeColor = None
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = max(data) + (1 if max(data) < 10 else 2)
        bc.valueAxis.valueStep = max(1, (max(data) + 1) // 5)
        bc.valueAxis.labels.fontSize = 7
        bc.valueAxis.labels.fillColor = MUTE
        bc.categoryAxis.labels.boxAnchor = "e"
        bc.categoryAxis.labels.fontSize = 7.6
        bc.categoryAxis.labels.fillColor = INK
        bc.categoryAxis.labels.dx = -3
        bc.categoryAxis.categoryNames = labels
        bc.categoryAxis.strokeColor = RULE
        bc.valueAxis.strokeColor = RULE
        bc.valueAxis.gridStrokeColor = colors.HexColor("#eef1f4")
        bc.valueAxis.visibleGrid = True
        for i in range(n):
            bc.bars[(0, i)].fillColor = color_fn(labels[i])
        bc.barLabels.fontSize = 7.5
        bc.barLabels.fillColor = INK
        bc.barLabelFormat = "%d"
        bc.barLabels.dx = 6
        d.add(bc)
        if title:
            d.add(String(0, h - 8, title, fontSize=8.5, fillColor=MUTE,
                         fontName="Helvetica-Bold"))
        return d

    def tiles(items):
        cells = []
        for big, lab in items:
            inner = Table([[Paragraph(big, TILE_N)], [Paragraph(lab, TILE_L)]],
                          rowHeights=[24, 20])
            inner.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
            cells.append(inner)
        t = Table([cells], colWidths=[42.5 * mm] * len(items))
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BG_TILE),
            ("BOX", (0, 0), (-1, -1), 0.5, RULE),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
        return t

    def data_table(header, rows, col_widths, verdict_col=None):
        head = [Paragraph(f"<b>{hh}</b>", ParagraphStyle("th", parent=CELL, fontSize=8,
                textColor=colors.white)) for hh in header]
        body = [head] + [[Paragraph(str(c), CELL) for c in r] for r in rows]
        t = Table(body, colWidths=col_widths, repeatRows=1)
        st = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#33414f")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fb")]),
        ]
        if verdict_col is not None:
            for i, r in enumerate(rows, start=1):
                v = r[verdict_col]
                key = next((k for k, lab in VERDICT_LABEL.items() if lab == v or k == v), None)
                st.append(("TEXTCOLOR", (verdict_col, i), (verdict_col, i),
                           VERDICT_COLOR.get(key, MUTE)))
                st.append(("FONTNAME", (verdict_col, i), (verdict_col, i), "Helvetica-Bold"))
        t.setStyle(TableStyle(st))
        return t

    story: list = []

    def rule():
        story.append(Spacer(1, 3))
        story.append(HRFlowable(width="100%", thickness=0.6, color=RULE))
        story.append(Spacer(1, 3))

    # Page 1
    story.append(Paragraph("Epistemische Fallstudie — Befunde mit Daten", H1))
    story.append(Paragraph(
        "Die „epistemische Validierung“ eines Muse-Spark-1.1-Textes durch "
        "MarCognity-AI, analysiert mit DESi",
        ParagraphStyle("sub", parent=BODY, fontSize=10.5, textColor=MUTE, spaceAfter=6)))
    story.append(Paragraph(
        "Quelle: Hugging-Face-Beitrag <i>„Epistemic Stress Test — Muse Spark 1.1 "
        "validated by MarCognity-AI“</i> (User elly99, 2026-07-10; Zenodo "
        "10.5281/zenodo.20509721) und github.com/elly99-AI/MarCognity-AI. Regeneriert "
        "offline &amp; deterministisch mit <font face='Courier'>python -m "
        "desi.case_studies.marcognity_muse_spark</font>. Jede Zahl unten stammt aus "
        "<font face='Courier'>summary.json / claims.jsonl / evidence.jsonl</font>.", SMALL))
    rule()
    story.append(tiles([
        (str(summary["claims_total"]), "atomare Claims<br/>typisiert &amp; verankert"),
        (f"{summary['source_gate_admissible']}/{summary['source_gate_total']}",
         "Claims mit domänen-<br/>zulässiger Evidenz"),
        (str(len(summary["structural_contradictions"])),
         "strukturelle Wider-<br/>sprüche (Detektor)"),
        ("ja" if summary["self_sealing"]["is_self_sealing"] else "nein",
         "selbstabdichtender<br/>Schluss; Falsifier: nein"),
    ]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Verteilung der Urteile (23 Claims)", H2))
    story.append(Paragraph(
        "Keine binären VERIFIED/FAILURE-Stempel: Heuristiken, Interpretationen und "
        "normative Aussagen bekommen eigene Kategorien; „unverifiable“ ist ein "
        "erstklassiges Urteil, keine Notlösung.", BODY))
    vdist = sorted(summary["verdict_distribution"].items(), key=lambda kv: (-kv[1], kv[0]))
    story.append(bar_chart(
        [(VERDICT_LABEL.get(k, k), v) for k, v in vdist],
        lambda lab: VERDICT_COLOR.get(
            next((k for k, lb in VERDICT_LABEL.items() if lb == lab), lab), MUTE)))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Evidenzstärke — wo konkrete Belege fehlen", H2))
    esd = summary["evidence_strength_distribution"]
    edist = [("none", esd.get("none", 0)), ("weak", esd.get("weak", 0)),
             ("moderate", esd.get("moderate", 0)), ("strong", esd.get("strong", 0))]
    escol = {"none": RED, "weak": AMBER, "moderate": BLUE, "strong": GREEN}
    story.append(bar_chart(edist, lambda lab: escol.get(lab, MUTE)))
    story.append(Paragraph(
        f"<b>{esd.get('none', 0)} von 23</b> Claims haben gar keine konkrete "
        "Evidenzpassage — der Validator nannte durchweg „das PubMed-Dokument“ "
        "ohne Titel oder Fundstelle.", SMALL))
    story.append(PageBreak())

    # Page 2
    story.append(Paragraph("Die drei strukturellen Widersprüche", H1))
    story.append(Paragraph(
        "Gefunden von DESis eigenem Detektor <font face='Courier'>desi.self_audit."
        "contradictions.find_contradictions</font> — nicht von Prosa behauptet.", SMALL))
    rule()
    contra = [
        ("C1", "Prompt ↔ Methode",
         "Die Methode (muse:L206): „No epistemic instructions (verification, sources, "
         "stages)“. Der abgedruckte Prompt verlangt ≥5 Quellen mit Direktzitaten "
         "(L56–58), eine Zitationskonsistenzprüfung (L64) und sechs benannte Phasen "
         "(L29–47). Der Versuch widerspricht seinem eigenen Aufbau."),
        ("C2", "„alle VERIFIED“ ↔ „keine Zitate“",
         "Derselbe Bericht stempelt fünf Claims VERIFIED (L170–198) und schließt mit "
         "„No citations found or verifiable“ (L201–202) — obwohl der Text "
         "acht Referenzen trägt (L154–161). Zwei entkoppelte Subsysteme, ohne Abgleich "
         "konkateniert (agent_metacognition L48–66)."),
        ("C3", "„unabhängig“ ↔ ein LLM-Call",
         "„Independent external validator“ (L208) gegen die Implementierung: ein "
         "einziges <font face='Courier'>llm.invoke</font> (skeptical_agent L62), das „the "
         "reference documents used for generation“ erhält (evaluator_prompt L24–28)."),
    ]
    for cid, title, txt in contra:
        story.append(KeepTogether([
            Paragraph(f"<b>{cid} — {title}</b>", ParagraphStyle(
                "c", parent=BODY, fontSize=10, textColor=RED, spaceAfter=1)),
            Paragraph(txt, BODY), Spacer(1, 4)]))
    story.append(Paragraph("Selbstabdichtung &amp; Falsifizierbarkeit", H2))
    ss_rows = [
        ["Würde stützen", "Validator markiert Unverifizierbares → Lücke sichtbar; ODER "
         "Validator scheitert → Boundary „im Validator selbst“ (L237). Beide "
         "Ausgänge bestätigen."],
        ["Würde schwächen", "Ein vorregistrierter Lauf, in dem der Validator mit "
         "domänenkorrekten Quellen Claims mit zitierten Passagen bestätigt — nicht "
         "bereitgestellt."],
        ["Würde widerlegen", "Eine Kontrolle, in der die Residualfehler unter sauberem "
         "Source-Gating verschwinden (Pipeline-Defekt statt „intrinsische Architektur“) "
         "— nicht bereitgestellt."],
        ["Falsifikationsbedingung im Versuch?", "<b>Nein.</b> Da Erfolg und Versagen beide "
         "bestätigen und kein Ausgang als widerlegend benannt ist, ist die Hypothese <i>as "
         "run</i> unfalsifizierbar."],
    ]
    t = Table([[Paragraph(f"<b>{a}</b>", CELL), Paragraph(b, CELL)] for a, b in ss_rows],
              colWidths=[45 * mm, 125 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (0, -1), BG_TILE),
        ("BOX", (0, 0), (-1, -1), 0.5, RULE),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, RULE),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6)]))
    story.append(t)
    story.append(PageBreak())

    # Page 3
    story.append(Paragraph("Alle 23 Claims — die Daten", H1))
    story.append(Paragraph(
        "Vollständig und je Zeile auditierbar in <font face='Courier'>claims.jsonl</font> / "
        "<font face='Courier'>evidence.jsonl</font>. Spalte „Evidenz“ = Provenienzart "
        "der tatsächlich verfügbaren Quelle.", SMALL))
    rule()
    prov_short = {"none": "keine", "semantic_similarity_only": "nur semantisch",
                  "primary": "primär", "secondary": "sekundär"}
    rows = []
    for c in claims:
        ev = evidence.get(c["claim_id"], {})
        rows.append([c["claim_id"], c["claim_type"].replace("_", " "),
                     c["domain"].replace("_", " "),
                     VERDICT_LABEL.get(c["verdict"], c["verdict"]),
                     prov_short.get(ev.get("provenance_kind", ""),
                                    ev.get("provenance_kind", ""))])
    story.append(data_table(["ID", "Typ", "Domäne", "Urteil", "Evidenz"], rows,
                            [18 * mm, 34 * mm, 34 * mm, 52 * mm, 32 * mm], verdict_col=3))
    story.append(PageBreak())

    # Page 4
    story.append(Paragraph("MarCognity vs. DESi — was anders ist", H1))
    story.append(Paragraph(
        "Kein Werbetext: DESi verhindert Fehler nicht, es macht die Stelle sichtbar, an der "
        "ein Fehler, eine Auslassung oder ein unzulässiger Schluss entsteht.", SMALL))
    rule()
    comp = [
        ("Claim-Abdeckung", "5 allgemeine Claims", "23 typisierte, inkl. Zitate/Attributionen"),
        ("Quellenpassung", "keine (PubMed ↔ Recht)", "source_domain_gate → Mismatch statt VERIFIED"),
        ("Konkrete Provenienz", "„das PubMed-Dokument“", "exakter Anker (doc:Zeile) oder none"),
        ("Widerspruchserkennung", "übersieht C1, erzeugt C2", "C1/C2/C3 via find_contradictions"),
        ("Interpret./Heuristik", "binär VERIFIED/FAILURE", "heuristic_proposal / interpretation / normative"),
        ("Unsicherheit", "globaler Fließtext", "pro Claim verdict + uncertainty + strength"),
        ("Falsifizierbarkeit", "keine Bedingung", "benennt support/weaken/refute + fehlende Falsifier"),
        ("Auditierbarkeit", "konkatenierter Freitext", "jsonl je Zeile + optional Hash-Ledger"),
        ("Evaluator-Selbstprüfung", "keine; Fehler = Bestätigung", "Report ist selbst Prüfobjekt (VAL-01..03)"),
    ]
    story.append(data_table(["Dimension", "MarCognity (Skeptical Agent)", "DESi"], comp,
                            [40 * mm, 62 * mm, 68 * mm]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Kernbefund", H2))
    story.append(Paragraph(
        "Der Demonstrationsfall ist nicht, dass Muse Spark Fehler macht. Er ist: die "
        "behauptete Validierung <b>bestätigt allgemeine juristische Aussagen mit ungeeigneten, "
        "intransparenten Quellen</b> (PubMed für Rechtsphilosophie, ohne Titel/Passage), "
        "<b>übersieht einen direkten Widerspruch im Versuchsaufbau</b> (C1) und <b>deutet das "
        "eigene Versagen als Bestätigung der Theorie</b> (Selbstabdichtung, ohne "
        "Falsifikationsbedingung).", BODY))
    story.append(Paragraph("Grenzen von DESi (ehrlich)", H2))
    story.append(Paragraph(
        "DESi ist nicht unfehlbar: die Claim-Fixierung ist kuratiert (kein Auto-Extraktor); "
        "die Rechtsphilosophie wird hier <i>nicht</i> inhaltlich adjudiziert (viele Claims enden "
        "bewusst auf „unverifiable“); source_domain_gate und die Selbstabdichtungs-"
        "Analyse sind kleine, allgemeine Erweiterungen. MarCognitys eigenes README/Boundary-"
        "Dokument sind vorsichtiger als der Forumsschluss — die Überdehnung liegt im "
        "Schluss, nicht in der gehedgten Hypothese.", SMALL))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(MUTE)
        canvas.drawString(18 * mm, 10 * mm,
                          "DESi-Fallstudie · marcognity_muse_spark · regeneriert "
                          "offline & deterministisch")
        canvas.drawRightString(192 * mm, 10 * mm, f"Seite {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=15 * mm, bottomMargin=16 * mm,
        title="DESi-Fallstudie MarCognity / Muse Spark 1.1 — Befunde",
        author="DESi case study")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
