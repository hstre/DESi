# Decision Attribution — wer traf welche Entscheidung?

Frage 6. Klassifikation pro größerer Entscheidung: **DESI / CODE AGENT / MENSCH / NICHT
FESTSTELLBAR**. Begründung erforderlich, keine Vermutungen.

| # | Entscheidung | Klassifikation | Begründung (Evidenz) |
| - | --- | --- | --- |
| 1 | Welche Kandidaten/Ideen überhaupt existieren | **CODE AGENT** | `CANDIDATES`/`SCORES` sind hand-codierte Literale in vom Agent geschriebenen `.py`-Dateien. Kein Generator. |
| 2 | Welche Fitness-/Utility-Punkte jeder Kandidat bekommt | **CODE AGENT** | Die Zahlen (`helps_now=2`, …) stehen als Konstanten im Quelltext, vom Agent vergeben; keine Messung. |
| 3 | Wo die BUILD/SPEC/REJECT-Schwellen liegen | **CODE AGENT** | `BUILD_T`, `SPEC_T` sind vom Agent gesetzte Konstanten. |
| 4 | Die Summen-Arithmetik & das Ranking | **DESI (peripher) + CODE AGENT** | Die Summen-/Sortierfunktion ist Code, den der Agent schrieb; `replay_hash` (echte DESi-Core-Funktion) hasht das Ergebnis. Die *Rechnung* ist mechanisch; die *Eingaben* sind Agent-Urteile. |
| 5 | Was als „forbidden direction" hart abgelehnt wird | **CODE AGENT** | Die `core_change`/`paper_metric_only`/`needs_embeddings`-Flags sind im Literal vom Agent gesetzt; die Regel, die sie liest, schrieb der Agent. |
| 6 | Welche Tools tatsächlich gebaut werden | **CODE AGENT** | Die Build-Entscheidung folgt aus (2)+(3), beide Agent. Der Code wurde vom Agent geschrieben (`git author=Claude`). |
| 7 | Die Wild-Brother-Kritiken & -Ideen | **CODE AGENT** | Hand-geschriebene `Critique(...)`/`Idea(...)`-Literale; kein LLM-Aufruf, keine externe Quelle. |
| 8 | Bugfixes (Commits 5658954/c79367b/3f624c2) | **CODE AGENT** | Git-Author=Claude; ausgelöst durch fehlgeschlagene Tests, die der Agent las und manuell korrigierte. |
| 9 | Scope-Erweiterung „alle 4 Richtungen + echte Module" | **MENSCH** | Per `AskUserQuestion` vom Nutzer beantwortet (im Transkript dokumentiert). |
| 10 | Interpretation „2500 Loops" = degeneratives Experiment | **MENSCH** | Nutzer präzisierte: „degeneratives experiment ich will wissen ob desi das kann". |
| 11 | Die Verdikt-Formulierungen in den Reports | **CODE AGENT** | Report-Text vom Agent generiert. |

## Welche Rolle spielte der DESi-CORE konkret?
- **Aufgerufen:** nur `desi.core.replay_kernel.replay_hash` (Hashing) — in 4 Dateien. Das ist eine
  deterministische Hash-Hilfsfunktion, **kein Entscheider**.
- **NICHT aufgerufen:** `desi.gates.concept_gate` (das eigentliche Governance-Gate),
  `LogicalAuditor`, `FrameDetector`, irgendein StateVector-Kernmechanismus. 0 Treffer im
  Evolutions-Pfad.
- Damit hat der DESi-Kern **keine einzige Selektions- oder Mutationsentscheidung getroffen**. Er
  hat Ergebnisse gehasht.

## Zusammenfassung
Der **CODE AGENT** traf die inhaltlichen Entscheidungen (Variation, Punktevergabe, Schwellen,
Selektion, Bau). Der **MENSCH** setzte Scope und Interpretation. **DESI** lieferte eine
Hash-Funktion für Reproduzierbarkeit. Keine größere Entscheidung ist als „DESI" oder „NICHT
FESTSTELLBAR" zu klassifizieren — die Quellenlage ist eindeutig.
