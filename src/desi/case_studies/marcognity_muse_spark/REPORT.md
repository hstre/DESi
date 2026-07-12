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

**Wichtige Einschränkung:** Diese 23 Claims sind eine **kuratierte Auswahl**, die bewusst zuvor
übersehene Claim-Klassen (Direktzitate, Autorenzuschreibungen, Heuristiken, normative Aussagen)
aufnimmt — **keine gemessene vollständige Claim-Abdeckung** des Muse-Textes. Die Fixierung ist ein
*closed dataset*, kein automatischer Extraktor über den Rohtext; eine vollständige, gemessene
Abdeckung wäre ein eigener, hier nicht erhobener Schritt.

### 3.1 Wichtigste Claims (Auszug; vollständig in `claims.jsonl`)

| ID | Typ | Urteil | Kern |
|---|---|---|---|
| MET-01 | methodisch | **contradicted** | „keine epistemischen Instruktionen" — vom eigenen Prompt widerlegt |
| MET-02 | methodisch | **partially_supported** | „extern“ trifft zu; „independent“ ist auf keiner Achse dokumentiert — methodische Fehlklassifikation |
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

### 3.2 Strukturelle Konflikte (`contradictions.md`)

Drei strukturelle Konflikte werden von DESis **eigenem** Detektor
`desi.self_audit.contradictions.find_contradictions` als Schlüssel/Wert-Inkonsistenzen gefunden
(nicht von Prosa behauptet). **Nicht jeder ist ein logischer Widerspruch** — die Art wird bewusst
unterschieden:

- **C1 — Widerspruch (logisch): Prompt ↔ Methode.** Die Methode (muse:L206) behauptet, das Modell
  habe „No epistemic instructions (requests for verification, sources, stages, etc.)“ erhalten. Der
  abgedruckte Prompt verlangt aber ≥5 wissenschaftliche Quellen mit Direktzitaten (muse:L56-58), eine
  Zitationskonsistenzprüfung (muse:L64), Datenbanksuchen (muse:L24-27) und **sechs benannte Phasen**
  (muse:L29-47). Ein echter Widerspruch: beide Aussagen können nicht zugleich wahr sein.
- **C2 — Pipeline-Inkonsistenz: VERIFIED ohne zitierbare Evidenz.** „VERIFIED“ und „No citations
  found“ können theoretisch beide zutreffen — es ist *kein* strikter logischer Widerspruch. Das
  eigentliche Problem: der Skeptical Agent behauptet Quellenunterstützung, **nennt aber keine Quelle
  und keine Passage** (nur „das PubMed-Dokument“); der Citation Checker erkennt zugleich keine
  überprüfbaren Referenzen (obwohl der Text acht trägt, muse:L154-161); beide Resultate werden **ohne
  Konsistenzprüfung** zusammengefügt (code:agent_metacognition L48-66).
- **C3 — Unbelegte Unabhängigkeit: „Independent external validation“ ↔ keine dokumentierte
  Unabhängigkeit.** Dass der Validator technisch nur ein `llm.invoke` ist (code:skeptical_agent L62),
  widerlegt Unabhängigkeit *nicht per se* — ein externer LLM-Aufruf könnte formal unabhängig sein.
  Der Konflikt ist enger: „independent external validation“ (muse:L208) wird behauptet, ohne dass auf
  **irgendeiner Achse** — organisatorisch, modellseitig oder evidenzseitig — Unabhängigkeit
  dokumentiert wäre; der Validator hängt vollständig an den Generierungsdokumenten
  (code:evaluator_prompt L24-28), ist nicht adversarial abgesichert und nicht reproduzierbar
  spezifiziert. Behauptet, nicht etabliert — eine methodische Fehlklassifikation.

---

## 4. Quellen- und Provenienzprobleme

Von 23 Claims haben **nur 4** eine domänenzulässige, nicht-nur-semantische Evidenz — und das sind
ausschließlich die **Meta-Aussagen über den Versuch selbst** (der Prompt, die Implementierung).
Für praktisch jeden *inhaltlichen* Claim gilt: keine konkrete Quelle, keine Passage, kein Titel.

> **Rahmung (Audit R4):** „4/23 zulässig" und „18/23 ohne Passage" beschreiben die **bereitgestellte
> Evidenz über die 23 kuratierten Claims** — *nicht* eine gemessene Fundierung des Muse-Textes. Ein
> Teil des „keine Passage" reflektiert, dass DESi selbst keine Primärquellen zieht (es adjudiziert
> die Rechtsphilosophie nicht). Die Zahlen sind also eine Eigenschaft des Versuchs-Materials, keine
> Fundierungsmessung.

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

**Fairness zuerst (Audit R5):** MarCognitys Ansatz hat echte methodische Stärken, die zuerst zu
benennen sind — Claim-Zerlegung statt Gesamttext-Urteil, Multi-Source-Retrieval (arXiv/PubMed/
OpenAlex/Zenodo) und ein expliziter skeptischer Prüf-Pass, der Pro-Claim-Unterstützung verlangt. Das
eigene README ist zudem vorsichtiger als der Forumsbeitrag (es räumt geteilte Verzerrung ein,
doc:readme L133). Der Fehler liegt in **Gating und Provenienz**, nicht in der Idee — und die
Überdehnung im **Forumsschluss**, nicht im Code. Genau deshalb ist die folgende Kritik präzise auf
die Verarbeitungsschicht gerichtet, nicht auf das Vorhaben als Ganzes.

- **Warum nur wenige, sehr allgemeine Claims?** Der Bericht prüft fünf breite Definitions-/
  Relationsaussagen und lässt **13 inhaltliche Claims** aus (`summary.json` → `omission`) — darunter
  *jedes* Direktzitat und *jede* Autorenzuschreibung, also gerade die **belegbedürftigsten** Typen.
- **Warum juristische Aussagen per PubMed?** Weil es kein Domain-Gating gibt: der Skeptical Agent
  bekommt, was das Retrieval geliefert hat, und nennt es „the PubMed document".
- **Warum keine Titel/Passagen?** Weil `skeptical_agent` nur gegen Abstract-Text prüft und nie eine
  Fundstelle extrahiert; „the PubMed document" bleibt titel- und passagenlos.
- **Wie „alle bestätigt“ *und* „keine verifizierbaren Referenzen“?** Beides kann formal zugleich
  gelten — die Pipeline-Inkonsistenz (C2) ist, dass zwei entkoppelte Subsysteme (Claim-Check vs.
  Regex-Zitationscheck) unversöhnt nebeneinanderstehen und der Claim-Check Unterstützung *ohne
  genannte Quelle/Passage* behauptet.
- **Extern und unabhängig?** „Extern“ ja (separater Aufruf, hier anderes Modell); „unabhängig“ ist
  auf keiner Achse dokumentiert (C3) — der Validator hängt an den Generierungsdokumenten, ist nicht
  adversarial und nicht reproduzierbar spezifiziert; das README gibt die geteilte Verzerrung selbst
  zu (doc:readme L133). Ein einzelner LLM-Aufruf *widerlegt* Unabhängigkeit nicht, *etabliert* sie
  aber auch nicht.
- **Mehr als ein weiterer LLM-Aufruf mit Quellkontext?** Der Code zeigt: methodisch nicht — ein
  nicht-adversarialer, unspezifizierter Aufruf, vollständig abhängig von den bereitgestellten Dokumenten.
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
| Claim-Abdeckung | 5 allgemeine Claims | 23 kuratierte, typisierte Claims (inkl. übersehener Klassen); keine gemessene Vollständigkeit |
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
  Fixierung ist ein *closed dataset*, nicht ein automatischer Extraktor über den Rohtext. Die 23
  Claims sind ausdrücklich eine **kuratierte Auswahl, keine gemessene vollständige Claim-Abdeckung**
  des Muse-Textes — „23“ ist daher keine Vollständigkeitsaussage.
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
- `doktores/` — **regelgeleiteter Doktores-Self-Audit dieser Fallstudie** (vier quell-verankerte
  Prüfer greifen die DESi-Analyse an; deterministisch, offline). **Einordnung:** logisch und
  provenance-basiert adversarial, aber *nicht* organisatorisch/modellseitig unabhängig — ein
  sauberer Gegencheck, **keine unabhängige Replikation** (DESi prüft DESi). Ergebnis: die meisten
  Befunde hielten stand, einige wurden eingeschränkt, C2/C3 als Nicht-Widersprüche bestätigt, Attest
  *passed_with_qualifications* (kein Gütesiegel). Reproduktion:
  `python -m desi.case_studies.marcognity_muse_spark.doktores`.
  Enthält `AUDIT_REPORT.md`, `ATTESTATION.md`, `claim_reviews.jsonl`, `contradiction_reviews.jsonl`,
  `methodology_review.md`, `fairness_review.md`, `dissent.md`, `REVISION_LOG.md`, `audit_summary.json`.
  Die Revisionen R1/R2/R4/R5 oben stammen aus diesem Audit (siehe `doktores/REVISION_LOG.md`).
- `redteam/` — **Harness (kein Ergebnis) für „Background-Reviewer"** (motiviert durch Claude
  Science's „a background reviewer flags incorrect citations, untraceable numbers …"). Prüft
  mehrdimensional, ob ein Reviewer die fünf epistemischen Failure-Modes fängt (untraceable_citation,
  source_domain_mismatch, self_sealing, overclaim, heuristic_not_empirical) — **ohne** über
  Clean-Controls hinweg über-zu-flaggen: Metriken sind Catch, **False Positives**, Control-Pass,
  **Stabilität** (über Wiederholungen) und **Cost**. DESi-Referenz 5/5 Catch, 0 FP *per
  Konstruktion*; naiver Whole-Text-Reviewer 0/5 — beides **kein Befund**. Der Befund entsteht erst,
  wenn ein echter Reviewer (Claude Science / Frontier-LLM) durch den External-Slot (JSON, inkl.
  `runs` für Varianz) läuft; die tragfähige These wäre dann Architektur-Effizienz („vergleichbare
  Kontrolle, deutlich weniger/deterministischerer Compute"), nicht „A schlägt B". Reproduktion:
  `python -m desi.case_studies.marcognity_muse_spark.redteam [--external out.json]`.
  **Echter cross-vendor Lauf** (`redteam/REDTEAM_RESULT.md`): drei blinde Frontier-Modelle
  (gpt-5.1, gemini-2.5-pro, grok-4.5; je 5 Läufe; NICHT Claude Science) erreichen **alle 5/5 Catch,
  0 FP, Controls sauber, Stabilität 1.0** — genau wie DESi. Lesart: **Parität bei Catch/Präzision** —
  und genau das ist der Punkt von „LLM für Sprache, Regeln für Logik": wo DESis Regeln greifen, matcht
  DESi Frontier-Modelle bei **~10⁵–10⁶× weniger Energie/Review** (~1,6 mJ CPU vs. ~10²–10⁴ J LLM;
  reproduzierbar via `scripts/redteam_energy_estimate.py`) und garantiertem Determinismus.
  **Noch nicht veröffentlichbar**: die Parität ist nur auf vor-destillierten Auszügen gezeigt; der
  Energie-Vorsprung trägt erst, wenn die Parität auch auf **rohen Volltexten** hält (ungetestet).
  Rohantworten verbatim in `redteam/external_runs/`.
- `redteam/hard/` — **HARTER Benchmark** (rohe, eingebettete Fehler, Near-Miss-Paare, Multi-Flag,
  adversariale Controls; Multi-Label-P/R/F1; `redteam/hard/REDTEAM_HARD_RESULT.md`). Diskriminiert
  jetzt: gpt-5.1 F1 **0.989**, grok-4.5 0.926, gemini-2.5-pro 0.901 (drei Fehlerprofile);
  Diskriminator sind **verschränkte Multi-Flag-Items** (Modelle unter-berichten den zweiten Fehler).
  **Kernbefund zur Energie-These:** DESis eigene Sprachschicht — ein *kleines* Modell —, konkret
  getestet: **granite-4.1-8b F1 0.892 (~90 % von gpt-5.1) bei ~100× niedrigerem Preis**, aber
  **granite-4.0-h-micro (3B) kollabiert (F1 0.538)**. Also Größen-Schwelle ~8B, kein „small model can't".
  Reproduktion: `python scripts/run_hard_benchmark.py` (`OPENROUTER_API_KEY` aus env).
