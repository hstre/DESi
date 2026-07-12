# Externe Validierung von R1 (v2) — Präregistrierung des Protokolls

*Status: **nur Protokoll**, keine Datensammlung, keine Regeländerung. Dieses Dokument wird **vor** jeder
Datenbeschaffung festgeschrieben. Ziel ist zu prüfen, ob die auf synthetischen Sätzen belegte kontrollierte
Härtung von R1 (v2) auf **realen wissenschaftlichen Dokumenten** trägt — und insbesondere, ob eine
**lexikalische Satzregel** überhaupt ausreicht oder ob echte **dokumentweite** epistemische Prüfung nötig ist.*

## 0. Was hier NICHT passiert

- Keine weiteren synthetischen Varianten, kein Regel-Tuning, keine Anpassung an den Testkorpus.
- **v2 ist strikt eingefroren** (`redteam/hard2/rules.py::detect_significance_not_importance_v2`, Logik seit
  Commit `1d6f05c`). Der Testkorpus wird v2 **nie** verändern; wird v2 je überarbeitet, geschieht das auf
  einem *separaten* Entwicklungssatz und wird erneut blind getestet.
- Kein Modell-Training, keine LLM-Beteiligung an der Regelentscheidung (R1 ist deterministisch).

## 1. Fragestellung & Hypothesen

**Objekt unter Test:** die gefrorene deterministische Regel R1 v2 (Signifikanz-als-Bedeutung-Detektor).

- **H1 (Satz-Ebene):** Auf realen, im Kontext gelesenen Aussagen erreicht v2 eine mit dem synthetischen
  Blind-Test vergleichbare **Precision** (dort 1.0), bei ausgewiesenem Recall.
- **H2 (Dokument-Ebene, der eigentliche Test):** v2s Precision **fällt**, wenn die relevante Effektgröße
  **nicht im selben Satz** steht, sondern im Nachbarsatz, in einer Tabelle oder nur über ein
  Konfidenzintervall — weil eine Satzregel diesen Kontext nicht sieht. Die Größe dieses Abfalls quantifiziert
  den Unterschied **lexikalische Satzregel vs. dokumentweite epistemische Prüfung**.

H2 ist der Kern: Bestätigung von H2 wäre ein ehrliches *Negativ*-Ergebnis für die reine Satzregel und die
konkrete Motivation für einen dokumentweiten Prüfschritt.

## 2. Konstrukt-Definition (vorab festgelegte Annotations-Guidelines)

**Positiver Fall (significance-as-importance):** eine Aussage behauptet praktische/klinische **Bedeutung
oder Größe** einer Wirkung und stützt diese **allein auf statistische Signifikanz** (p-Wert / „signifikant" /
„statistisch reliabel"), **ohne** dass an *irgendeiner* zugänglichen Stelle eine Effektgröße die Aussage
angemessen skaliert.

**Negativer Fall (clean):** einer von
- *effect_size_present*: eine Effektgröße skaliert die Aussage korrekt (egal wo im Dokument, s. §4);
- *no_significance*: Größen-/Bedeutungsaussage ohne Signifikanz-Bezug;
- *no_magnitude*: Signifikanz/p neutral berichtet, **keine** Größen-/Bedeutungsbehauptung;
- *null_result*: explizit nicht signifikant.

**Grenzfall (boundary, explizit als eigene Klasse annotiert):** u. a. Signifikanz + Effektgröße nur als
Konfidenzintervall (ohne Punktschätzer-Einordnung); Effektgröße nur in Tabelle/Abbildung; „klinisch
bedeutsam" ohne benannte Schwelle; hedged („könnte", „deutet an"); Effektgröße im Nachbarsatz mit
gegenläufiger Wertung.

Die vollständigen Guidelines (mit ≥3 Beispielen je Klasse, Entscheidungsbaum, Tie-Break-Regeln) werden **vor**
Annotationsbeginn eingefroren und versioniert.

## 3. Annotationseinheit & Dokumentkontext

- **Primäreinheit:** eine **Claim-Instanz** = ein Satz (ggf. Teilsatz), der eine Größen-/Bedeutungsaussage
  trägt, **zusammen mit seinem Kontextfenster**: mindestens der umgebende Absatz, der Abschnittstyp
  (Results/Discussion/Abstract) sowie **alle im Satz referenzierten Tabellen/Abbildungen**.
- **Isolierte Kunstsätze sind ausgeschlossen** — annotiert und getestet wird im Dokumentkontext.
- Annotatoren markieren zuerst Kandidatensätze (Screening), dann Klasse + Effektgrößen-Verortung (§4).

## 4. Effektgrößen-Verortung — die entscheidende Stratifizierungsvariable

Für **jede** Claim-Instanz wird festgehalten, **wo** die relevante Effektgröße (falls vorhanden) steht:

| Locus | Bedeutung | Für eine Satzregel sichtbar? |
|---|---|---|
| `same_sentence` | Effektgröße im selben Satz | ja |
| `adjacent_sentence` | im Nachbarsatz / selben Absatz | nein |
| `table_or_figure` | nur in Tabelle/Abbildung | nein |
| `ci_only` | nur über ein Konfidenzintervall ableitbar | nein (Punktgröße nicht explizit) |
| `absent` | nirgends berichtet | — (echte Konflation) |

Dies erlaubt die **getrennte** Auswertung: v2 kann eine Aussage nur dann korrekt als *clean* erkennen, wenn
die Effektgröße `same_sentence` steht. Die Klassen `adjacent_sentence`/`table_or_figure`/`ci_only` sind der
Prüfstein für H2 — hier erzeugt eine reine Satzregel **erwartbar False Positives**, obwohl das Dokument
sauber ist. `absent` ist die echte Konflation (wo v2 korrekt feuern soll).

## 5. Annotatoren, Blindung, Übereinstimmung

- **≥ 2 unabhängige Annotatoren**, fachlich geeignet (Statistik/Methodik-Hintergrund), **ohne** Kenntnis von
  v2s Regel-Interna oder Vokabular (verhindert Konstrukt-Leckage).
- Annotatoren sehen **nicht** die Regel-Outputs (Gold wird unabhängig vom Detektor erstellt).
- **Reliabilität:** Cohen's κ (2 Annotatoren, kategoriale Klasse **und** binär SIG/clean) bzw. Krippendorff's
  α (≥ 3 Annotatoren oder fehlende Werte). Separat berichtet für (a) die SIG/clean-Entscheidung und (b) die
  Effektgrößen-Verortung. **Akzeptanzschwelle vorab:** κ/α ≥ 0.6 für Aufnahme; darunter werden Guidelines
  (nicht die Regel) überarbeitet und **komplett neu** annotiert.
- **Disagreement-Auflösung:** unabhängige Doppelannotation → Adjudikation durch eine dritte Person; die
  Roh-Labels beider Annotatoren bleiben erhalten (für α und Fehleranalyse).

## 6. Anwendung der gefrorenen v2-Regel

- v2 wird **satzweise** auf denselben Claim-Instanzen angewandt, die annotiert wurden (identische
  Segmentierung, festgelegte Sentence-Splitting-Bibliothek + Version, vorab fixiert).
- **Ein Treffer** = v2 markiert die Claim-Instanz als significance-not-importance.
- Keine Regel-Parameter werden am Korpus justiert. Der Sentence-Splitter und etwaige Vorverarbeitung werden
  **vor** dem Lauf eingefroren und dokumentiert.

## 7. Metriken (getrennt berichtet)

Auf Claim-Ebene, gegen **zwei** Gold-Referenzen:

- **Gold-Satz** (nur der Satz, isoliert betrachtet) — misst, was die Satzregel *sehen kann*.
- **Gold-Dokument** (Effektgröße überall im Kontext berücksichtigt, §4) — misst echte epistemische Korrektheit.

Für **jede** Referenz getrennt: **Precision, Recall, F1** und **Abdeckung** (Coverage = Anteil der
Claim-Instanzen, auf die v2 feuert; zusätzlich Anteil der Dokumente mit ≥ 1 Flag). Zusätzlich verpflichtend:

- **Stratifiziert nach Effektgrößen-Locus** (§4): Precision je Locus. Erwartung H2: hoch bei `same_sentence`,
  niedrig bei `adjacent_sentence`/`table_or_figure`/`ci_only`.
- **Die Precision-Differenz (Gold-Satz − Gold-Dokument)** ist die primäre Kennzahl für „Satzregel vs.
  dokumentweite Prüfung".
- Konfidenzintervalle (Bootstrap) für alle Punktschätzer; N und Klassenverteilung offengelegt.

## 8. Analyseplan

- **Primär:** Precision/Recall/F1/Coverage gegen Gold-Dokument, plus die Precision-Differenz zu Gold-Satz.
- **Sekundär:** dieselben Größen je Effektgrößen-Locus; Fehleranalyse (welche realen Formulierungen v2 verpasst
  → Recall-Lücken; welche kontextuell gerechtfertigten Aussagen v2 fälschlich flaggt → Precision-Lücken).
- **Vorab definierte Deutung:** hält Precision gegen **Gold-Dokument** ≥ ~0.8 über alle Loci, ist die
  Satzregel auch dokumentweit brauchbar. Fällt sie nur bei den nicht-`same_sentence`-Loci deutlich ab, ist
  **H2 bestätigt** → die Satzregel ist lexikalisch begrenzt, ein dokumentweiter Effektgrößen-Resolver (kein
  Regel-Tuning) wäre der nächste Baustein.

## 9. Grenzen, die vorab benannt werden

- Reale Annotation ist teurer und seltener als synthetische; N wird kleiner sein → breitere CIs. N-Ziel und
  Power werden vor Sammlung festgelegt.
- Domänenabhängigkeit (Medizin vs. Psychologie vs. Ökonomie) kann Precision/Recall verschieben → Domäne als
  Kovariate erfassen.
- v2 ist englisch-lexikalisch; nicht-englische Dokumente sind out of scope dieser Runde.

---

## 10. Zusammenfassung — benötigte Dokumentformate & Annotationseinheiten

**Dokumentformate (Anforderung, noch keine Quelle gewählt):**
- **Maschinenlesbarer Volltext mit strukturell zugänglichen Tabellen** — bevorzugt **JATS-XML oder
  strukturiertes HTML** (nicht nur PDF), damit Absatz-/Satzgrenzen sauber und **Tabelleninhalte parsebar**
  sind (Effektgrößen stehen oft nur in Tabellen — für `table_or_figure` unverzichtbar).
- Mindestumfang je Dokument: **Abstract + Results + Discussion**, inklusive der **referenzierten Tabellen/
  Abbildungs-Captions** und, wo möglich, numerischer Tabellenzellen.
- Lizenz, die Speicherung + Annotation erlaubt (z. B. Open-Access-Volltext).
- Erhaltene Metadaten: Abschnittstyp, Absatz-IDs, Satz-IDs, Tabellen-/Abbildungs-Referenzen.

**Annotationseinheiten:**
1. **Claim-Instanz** (Primär): Kandidatensatz + Kontextfenster (Absatz + Abschnittstyp + referenzierte
   Tabellen/Abbildungen).
2. **Klassenlabel** je Claim: {SIG-positiv, clean-*Subtyp*, boundary-*Subtyp*}.
3. **Effektgrößen-Locus** je Claim: {same_sentence, adjacent_sentence, table_or_figure, ci_only, absent}.
4. **Dokument-Metadaten:** Domäne, Abschnitt, Quelle/ID, Lizenz.

**Offen — Entscheidung gemeinsam (Quelle & Beschaffung):** konkrete Korpus-Quelle (z. B. ein Open-Access-
Volltext-Repositorium mit JATS-XML), Stichprobenrahmen (Domänen, Zeitraum, Positiv-Anreicherung ohne
Precision-Verzerrung), N-Ziel/Power, Rekrutierung der ≥ 2 Annotatoren. Diese Punkte werden **nach** Freigabe
dieses Protokolls entschieden — hier bewusst nicht vorweggenommen.
