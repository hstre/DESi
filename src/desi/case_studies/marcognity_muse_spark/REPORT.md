# Fallstudie: Die „epistemische Validierung" eines Muse-Spark-1.1-Textes durch MarCognity-AI

**Gegenstand.** Der Hugging-Face-Forumsbeitrag *„Epistemic Stress Test — Muse Spark 1.1
validated by MarCognity-AI"* (User `elly99`, 2026-07-10; Zenodo-DOI 10.5281/zenodo.20509721)
behauptet, ein von Muse Spark 1.1 erzeugter rechtsphilosophischer Text sei mit MarCognity-AI
epistemisch validiert worden. Primärquelle ist die im Forumstitel benannte Repository-Datei
`epistemic_stress_test/Epistemic Integrity Stress Test Muse Spark 1.1` in
`github.com/elly99-AI/MarCognity-AI` (im Folgenden **muse:Zeile**), ergänzt um die referenzierten
Implementierungsdateien (**code:…**).

**Leitfrage** — nicht *„ist der Text gut oder schlecht?"*, sondern: *welche überprüfbaren
Behauptungen enthält das Material, welche davon sind durch geeignete, nachvollziehbare Evidenz
gedeckt — und ist die behauptete Validierung selbst methodisch belastbar?*

**Reproduktion.** Alle maschinellen Artefakte dieser Fallstudie werden erzeugt von:

```bash
python -m desi.case_studies.marcognity_muse_spark
```

Das ist offline und deterministisch (kein LLM-Aufruf; regelbasiert über eine eingefrorene
Materialfixierung). Es schreibt `claims.jsonl`, `evidence.jsonl`, `contradictions.md`,
`comparison.md`, `summary.json`. Optional hängt `--ledger <pfad>` einen hash-verketteten
Audit-Eintrag über das Layer-9-Ledger (`desi_router.ledger`) an.

---

## 1. Zusammenfassung des Originalversuchs

Der Beitrag beschreibt sechs Teile (muse): (1) Zweck — die „fracture" zwischen sprachlicher
Kohärenz und epistemischer Fundierung sichtbar machen und ein „residuales Unsicherheitsregime
(Epistemic Boundary)" identifizieren; (2) den verwendeten Prompt; (3) den generierten Text (eine
rechtsphilosophische Abhandlung über *Rechtssicherheit* und *Wirksamkeit*) samt (3.1)
Validierungsbericht des *Skeptical Agent*; (4) Methode; (5) Ergebnisse; (6) Diskussion;
(7) Schluss.

Der **Validierungsbericht** (muse:L170-198) prüft fünf sehr allgemeine Aussagen und stempelt jede
mit `STATUS: VERIFIED`, jeweils „supported by … the PubMed document". Unmittelbar darunter steht
(muse:L201-202): **„VERIFIED BIBLIOGRAPHIC REFERENCES — No citations found or verifiable in the
text."** Der **Schluss** (muse:L235-237) deutet den Domänenfehler des Validators (Rechtsphilosophie
gegen PubMed) zur Bestätigung um: der Test habe „die Epistemic Boundary sogar im Validator selbst"
offengelegt und „empirically demonstrates", dass das residuale Regime „an intrinsic characteristic
of the autoregressive architecture" sei.

---

## 2. Rekonstruktion der Methode (aus dem Code, nicht aus dem Marketing)

Der *Skeptical Agent* ist **ein einziger LLM-Aufruf**: `res = llm.invoke(prompt.strip())`
(code:skeptical_agent L62). Der metakognitive Ablauf (code:agent_metacognition L29-68) ist:
generieren → **Kohärenz** selbst bewerten und bei Score < 0.7 „verbessern" (L33-43) →
`skeptical_agent(question, response_text, context_docs)` (L48) → `verify_citations(response_text)`
(L51) → beide Ausgaben **ohne Abgleich** aneinanderhängen (L55-66). Der Evaluator-Prompt nennt sich
„an independent LLM" (code:evaluator_prompt L24), erhält aber ausdrücklich „the reference documents
used for generation" (L26-28) — also **denselben Retrieval-Kontext, der schon die Generierung
speiste**. Die Zitationsprüfung (code:extract_citations) ist ein Regex über DOI/PMID/arXiv/
`Autor, X. (Jahr)`; sie ist vom Skeptical Agent **entkoppelt**. Kein Schritt routet Claims nach
Wissensdomäne; es gibt **kein Source-Gating**.

Wichtig für Fairness: MarCognitys **eigenes** README ist vorsichtiger als der Forumsschluss. Es
räumt ein (doc:readme L133): „the evaluator may share epistemic biases with the evaluated system",
nennt sich „not intended for production" und „does not claim to solve hallucinations". Auch das
`Epistemic Boundary.md` ist als *deskriptive Hypothese* gehedged (doc:epistemic_boundary L119-122:
„latent construct, not directly observable … causal mechanisms not identified … further controlled
experimental validation is required"). **Die Überdehnung liegt im Forumsschluss, nicht in der
zurückhaltenderen Repository-Formulierung.**

---

## 3. DESi-Analyse

Die Fallstudie zerlegt das Material in **23 atomare Claims** (`claims.jsonl`), jeder mit exaktem
Anker (doc:Zeile + Wortlaut), Claim-Typ, Domäne, erforderlicher Evidenzart, Urteil, Begründung und
Unsicherheit. Jeder Claim hat einen `evidence.jsonl`-Eintrag mit der **tatsächlich verfügbaren**
Quelle, Provenienzart (primär / sekundär / nur-semantisch / keine) und konkreter Passage —
letztere leer, wo keine genannt wurde. Das Leere *ist* der Befund, es wird protokolliert, nicht
kaschiert.

### 3.1 Wichtigste Claims (Auszug; vollständig in `claims.jsonl`)

| ID | Typ | Urteil | Kern |
|---|---|---|---|
| MET-01 | methodisch | **contradicted** | „keine epistemischen Instruktionen" — vom eigenen Prompt widerlegt |
| MET-02 | methodisch | **contradicted** | „unabhängige externe Validierung" — ein LLM-Call über den Generierungskontext |
| MET-03 | methodisch | unverifiable | „vollständig reproduzierbar" — keine Modellversion/Seed/Parameter |
| VAL-01 | über Validator | **source_domain_mismatch** | fünf Rechts-Claims „VERIFIED" durch „das PubMed-Dokument" |
| VAL-02 | über Validator | **citation_mismatch** | „keine Zitate gefunden" — obwohl 8 Referenzen im Text stehen |
| VAL-03 | über Validator | supported | Validator nutzte domänenfremde DB (Selbstbeobachtung korrekt) |
| EB-02 | über Boundary | **unsupported** | n=1 „empirically demonstrates … intrinsic" — Überdehnung |
| HEUR-01/02/03 | heuristisches Modell | **heuristic_proposal** | die Formeln C, E, E=f(C,K,L) — Eigenkonstruktionen |
| QUOTE-01/02 | Direktzitat | unverifiable | Kelsen-/Bobbio-Zitate ohne belegte Fundstelle |
| ATTR-01/02 | Autorenzuschreibung | unverifiable | Guastini/Bobbio, Kelsen/Di Lucia — ohne Passage |
| NORM-01 | normativ | **normative_claim** | „mature legal science ought…" — nicht wahrheitsfähig |

Die **Formeln für Rechtssicherheit und Wirksamkeit** werden — wie gefordert — *nicht* als wahr
oder falsch klassifiziert, sondern als **heuristische Eigenkonstruktionen** markiert; der Text
selbst nennt sie „in a heuristic way" (muse:L88). Keine wissenschaftliche Herleitung, keine
empirische Kalibrierung liegt vor.

### 3.2 Wichtigste Widersprüche (`contradictions.md`)

Drei strukturelle Widersprüche werden von DESis **eigenem** Detektor
`desi.self_audit.contradictions.find_contradictions` gefunden (nicht von Prosa behauptet):

- **C1 — Prompt ↔ Methode.** Die Methode (muse:L206) behauptet, das Modell habe „No epistemic
  instructions (requests for verification, sources, stages, etc.)" erhalten. Der abgedruckte Prompt
  verlangt aber ≥5 wissenschaftliche Quellen mit Direktzitaten (muse:L56-58), eine
  Zitationskonsistenzprüfung (muse:L64), Datenbanksuchen (muse:L24-27) und **sechs benannte Phasen**
  (muse:L29-47). Der Versuch widerspricht seinem eigenen Aufbau.
- **C2 — „alle VERIFIED" ↔ „keine Zitate".** Derselbe Bericht stempelt fünf Claims `VERIFIED` und
  schließt mit „No citations found or verifiable" — obwohl der Text acht wohlgeformte Referenzen
  trägt (muse:L154-161). Ursache: zwei Subsysteme, ohne Abgleich konkateniert
  (code:agent_metacognition L48-66).
- **C3 — „unabhängig" ↔ ein LLM-Call.** „Independent external validator" (muse:L208) gegen
  `llm.invoke` über den Generierungskontext (code:skeptical_agent L62, code:evaluator_prompt L24-28).

---

## 4. Quellen- und Provenienzprobleme

Von 23 Claims haben **nur 4** eine domänenzulässige, nicht-nur-semantische Evidenz — und das sind
ausschließlich die **Meta-Aussagen über den Versuch selbst** (der Prompt, die Implementierung).
Für praktisch jeden *inhaltlichen* Claim gilt: keine konkrete Quelle, keine Passage, kein Titel.

Der Kernfehler ist **fehlendes Source-Gating**: eine rechtsphilosophische Aussage
(Kelsen/Hart/Bobbio) wird gegen „das PubMed-Dokument" — eine biomedizinische Datenbank — „verifiziert"
(muse:L174-198). Ein *Treffer* in einer Datenbank ist keine Evidenz, solange keine konkrete Quelle
und keine konkrete Passage benannt sind. DESis `source_domain_gate` macht das explizit: PubMed ist
für `legal_philosophy` schlicht nicht zulässig → `SOURCE_DOMAIN_MISMATCH`, kein „VERIFIED".

Ehrliche Gegenprobe: Die **eigene Bibliografie** des Muse-Textes (muse:L154-161) besteht überwiegend
aus realen, bekannten Werken (Kelsen 1960, Hart 1961, Bobbio 1993, Fuller 1969, Luhmann, Guastini
1986, Tamanaha 2001, Kaplow 1992). **Muse hat die Zitate also nicht primär erfunden** — das Versagen
liegt in der *Validierungsschicht*, nicht vorrangig in der Generierung. (Diese Fallstudie hat die
einzelnen Referenzen *nicht* eigenständig gegen die Primärquellen geprüft; sie routet und markiert,
sie adjudiziert die Rechtsphilosophie nicht.)

---

## 5. Bewertung der MarCognity-Validierung (der Bericht als eigenes Prüfobjekt)

- **Warum nur wenige, sehr allgemeine Claims?** Der Bericht prüft fünf breite Definitions-/
  Relationsaussagen und lässt **13 inhaltliche Claims** aus (`summary.json` → `omission`) — darunter
  *jedes* Direktzitat und *jede* Autorenzuschreibung, also gerade die **belegbedürftigsten** Typen.
- **Warum juristische Aussagen per PubMed?** Weil es kein Domain-Gating gibt: der Skeptical Agent
  bekommt, was das Retrieval geliefert hat, und nennt es „the PubMed document".
- **Warum keine Titel/Passagen?** Weil `skeptical_agent` nur gegen Abstract-Text prüft und nie eine
  Fundstelle extrahiert; „the PubMed document" bleibt titel- und passagenlos.
- **Wie „alle bestätigt" *und* „keine verifizierbaren Referenzen"?** Weil zwei entkoppelte
  Subsysteme (Claim-Check vs. Regex-Zitationscheck) unversöhnt nebeneinanderstehen (C2).
- **Extern und unabhängig?** Nein im relevanten Sinn: gleicher Retrieval-Kontext wie die Generierung
  (C3); das README gibt die geteilte Verzerrung selbst zu (doc:readme L133).
- **Mehr als ein weiterer LLM-Aufruf mit Quellkontext?** Der Code zeigt: nein.
- **Fehler durch semantische Ähnlichkeit ohne Provenienzprüfung?** Genau die: topische
  String-Nähe eines biomedizinischen Abstracts wird als Bestätigung eines Rechts-Claims gewertet.

---

## 6. Das Selbstabdichtungsproblem (`contradictions.md` → Selbstabdichtung)

Der Schluss liest **jeden** Ausgang als Bestätigung: arbeitet der Validator „richtig", ist die
Verifizierbarkeitslücke sichtbar gemacht (das erklärte Ziel); arbeitet er „falsch", zeigt sich die
Boundary „even within the validator itself" (muse:L237). Wenn Erfolg **und** Versagen bestätigen und
**kein** Ausgang als widerlegend benannt ist, ist die Hypothese *as run* **unfalsifizierbar**.

- **Stützen würde:** Validator markiert Unverifizierbares → Lücke sichtbar. / Validator scheitert →
  Boundary im Validator.
- **Schwächen würde:** ein vorregistrierter Lauf, in dem der Validator mit *domänenkorrekten* Quellen
  Claims mit zitierten Passagen bestätigt — **nicht bereitgestellt**.
- **Widerlegen würde:** eine Kontrolle, in der die Residualfehler unter sauberem Source-Gating +
  Provenienz *verschwinden* (die Fehler wären dann ein Pipeline-Defekt, keine „intrinsische
  Architektur"-Eigenschaft) — **nicht bereitgestellt**.
- **Falsifikationsbedingungen im Originalversuch angegeben?** **Nein.**

Das ist zugleich der Hebel der ehrlichen Lesart: EB-02 („empirically demonstrates … intrinsic")
überdehnt sogar MarCognitys **eigenes** Boundary-Dokument, das kontrollierte Validierung erst noch
verlangt (doc:epistemic_boundary L119-122).

---

## 7. Vergleich MarCognity vs. DESi

Vollständige Tabelle: `comparison.md` (auto-generiert). In einem Satz je Achse:

| Dimension | MarCognity | DESi |
|---|---|---|
| Claim-Abdeckung | 5 allgemeine Claims | 23 typisierte, inkl. Zitate/Attributionen |
| Quellenpassung | keine (PubMed ↔ Recht) | `source_domain_gate` → Mismatch statt „VERIFIED" |
| Konkrete Provenienz | „das PubMed-Dokument" | exakter Anker (doc:Zeile) oder `provenance=none` |
| Widerspruchserkennung | übersieht C1, erzeugt C2 | C1/C2/C3 via `find_contradictions` |
| Interpretationen/Heuristiken | binär VERIFIED/FAILURE | `heuristic_proposal`/`interpretation`/`normative_claim` |
| Unsicherheit | globaler Fließtext | pro Claim `verdict`+`uncertainty`+`evidence_strength` |
| Falsifizierbarkeit | keine Bedingung | benennt support/weaken/refute + fehlende Falsifier |
| Auditierbarkeit | konkatenierter Freitext | jsonl je Zeile + optional hash-verketteter Ledger |
| Evaluator-Selbstprüfung | keine; Fehler = Bestätigung | Report ist selbst Prüfobjekt (VAL-01..03) |

---

## 8. Methodische Grenzen von DESi (kein Werbetext)

- DESi **verhindert Fehler nicht**. Die Claim-Extraktion und Typisierung dieser Fallstudie ist von
  einem Menschen/Modell kuratiert und kann selbst falsch typisieren oder Claims übersehen; die
  Fixierung ist ein *closed dataset*, nicht ein automatischer Extraktor über den Rohtext.
- DESi **adjudiziert die Rechtsphilosophie hier nicht**. Viele inhaltliche Claims enden bewusst auf
  `unverifiable_from_available_evidence` — das ist ehrlich, aber es ist *kein* positives Sachurteil.
  Wer die Attributionen prüfen will, muss die Primärquellen ziehen; das leistet diese Fallstudie
  nicht.
- Das `source_domain_gate` und die Selbstabdichtungs-Analyse sind **kleine, allgemeine Erweiterungen**
  (DESi hat keinen Wissensdomänen-Router, nur Task-Routing); ihre Domänen-Zuordnung ist eine Setzung
  und könnte in Grenzfällen streiten.
- Auch DESi nutzt für *Sprache* ein LLM. Der Vorteil liegt nicht in Unfehlbarkeit, sondern in der
  **Lokalisierbarkeit**: an welcher Stelle der Verarbeitungskette ein Fehler, eine Auslassung oder ein
  unzulässiger Schluss entstanden ist.

---

## 9. Abschließendes Urteil

Der entscheidende Demonstrationsfall ist **nicht**, dass Muse Spark Fehler macht. Er ist:

> Die behauptete Validierung **bestätigt allgemeine juristische Aussagen mit ungeeigneten bzw. nicht
> transparent ausgewiesenen Quellen** (PubMed für Rechtsphilosophie, ohne Titel/Passage), **übersieht
> einen direkten Widerspruch im Versuchsaufbau** (Prompt verlangt genau die Quellen/Stufen, die die
> Methode für abwesend erklärt) und **deutet anschließend das eigene Versagen als Bestätigung der
> Theorie** (Selbstabdichtung, ohne Falsifikationsbedingung).

MarCognity erzeugt **überwiegend ein Urteil über einen Gesamttext**; DESi erzeugt eine **überprüfbare
Struktur** aus Claims, Evidenzen, Widersprüchen, Auslassungen und Unsicherheiten — und macht damit die
*Stelle* sichtbar, an der die Validierung kippt. Fair bleibt festzuhalten: MarCognitys eigenes README
und Boundary-Dokument sind vorsichtiger formuliert als der Forumsschluss; die belastbarste Kritik
richtet sich gegen die **Überdehnung im Schluss** (EB-02) und den **Pipeline-Defekt** (fehlendes
Source-Gating, entkoppelte Subsysteme), nicht gegen die bloße Existenz eines „residualen Regimes" als
gehedgter Hypothese.

---

### Artefakte in diesem Verzeichnis
- `REPORT.md` — dieser Bericht (handgeschrieben).
- `claims.jsonl` — 23 atomare, je Zeile auditierbare Claims *(generiert)*.
- `evidence.jsonl` — Evidenz-Mapping mit Provenienz und Passagen *(generiert)*.
- `contradictions.md` — die drei strukturellen Widersprüche + Selbstabdichtung *(generiert)*.
- `comparison.md` — Vergleichstabelle MarCognity ↔ DESi *(generiert)*.
- `summary.json` — maschinenlesbare Kennzahlen *(generiert)*.
- `marcognity_muse_spark_findings_en.pdf` / `…_de.pdf` — Befunde mit Daten als PDF
  (Charts + Tabellen), englisch und deutsch; regenerierbar via
  `python scripts/reproduce_marcognity_pdf.py` (benötigt `reportlab`).
- `source_material.py` — verbatim gesicherte, zeilenadressierte Materialanker (Aufgabe 1).
- `claims.py` / `analysis.py` / `report.py` / `__main__.py` — Fixierung, Engine, Writer, Reproduktion.
